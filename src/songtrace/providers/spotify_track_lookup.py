"""Private-safe Spotify track metadata lookup."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from songtrace.providers.spotify_api_access import (
    request_spotify_client_credentials_access_token,
)
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    validate_spotify_environment,
)

SPOTIFY_TRACK_URL_BASE = "https://api.spotify.com/v1/tracks"

TokenProvider = Callable[[str, str], str]
TrackPayloadRequester = Callable[[str, str], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class SpotifyTrackMetadata:
    """Safe Spotify track metadata for identity validation."""

    spotify_track_id: str
    title: str
    artist_names: tuple[str, ...]
    album_name: str | None = None
    isrc: str | None = None

    def __post_init__(self) -> None:
        if not self.spotify_track_id.strip():
            msg = "spotify_track_id_required"
            raise ValueError(msg)
        if not self.title.strip():
            msg = "spotify_track_title_required"
            raise ValueError(msg)
        if not self.artist_names:
            msg = "spotify_track_artist_required"
            raise ValueError(msg)
        if len(set(self.artist_names)) != len(self.artist_names):
            msg = "spotify_track_duplicate_artists"
            raise ValueError(msg)


def lookup_spotify_track_metadata(
    spotify_track_id: str,
    env: Mapping[str, str | None] | None = None,
    token_provider: TokenProvider | None = None,
    track_payload_requester: TrackPayloadRequester | None = None,
) -> SpotifyTrackMetadata:
    """Lookup safe Spotify track metadata without storing credentials or tokens."""

    normalized_track_id = spotify_track_id.strip()
    if not normalized_track_id:
        msg = "spotify_track_id_required"
        raise ValueError(msg)

    values = os.environ if env is None else env
    environment = validate_spotify_environment(values)
    if not environment.is_configured:
        msg = "missing_credentials"
        raise ValueError(msg)

    requester = token_provider or request_spotify_client_credentials_access_token
    access_token = requester(
        _required_env_value(values, SPOTIFY_CLIENT_ID_ENV),
        _required_env_value(values, SPOTIFY_CLIENT_SECRET_ENV),
    )

    payload_requester = track_payload_requester or request_spotify_track_payload
    payload = payload_requester(access_token, normalized_track_id)
    return _metadata_from_payload(payload)


def request_spotify_track_payload(access_token: str, spotify_track_id: str) -> Mapping[str, object]:
    """Request a Spotify track payload using a short-lived access token."""

    if not access_token.strip():
        msg = "spotify_access_token_required"
        raise ValueError(msg)

    request = Request(
        f"{SPOTIFY_TRACK_URL_BASE}/{quote(spotify_track_id, safe='')}",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        msg = f"spotify_track_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = "spotify_track_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = "spotify_track_invalid_json"
        raise ValueError(msg) from error

    if not isinstance(payload, dict):
        msg = "spotify_track_invalid_payload"
        raise ValueError(msg)
    return cast("Mapping[str, object]", payload)


def _metadata_from_payload(payload: Mapping[str, object]) -> SpotifyTrackMetadata:
    spotify_track_id = _required_string(payload, "id", "spotify_track_missing_id")
    title = _required_string(payload, "name", "spotify_track_missing_name")
    artist_names = _artist_names(payload)
    album_name = _optional_album_name(payload)
    isrc = _optional_isrc(payload)

    return SpotifyTrackMetadata(
        spotify_track_id=spotify_track_id,
        title=title,
        artist_names=artist_names,
        album_name=album_name,
        isrc=isrc,
    )


def _artist_names(payload: Mapping[str, object]) -> tuple[str, ...]:
    artists = payload.get("artists")
    if not isinstance(artists, list):
        msg = "spotify_track_missing_artists"
        raise ValueError(msg)

    names: list[str] = []
    for artist_item in cast("list[object]", artists):
        if not isinstance(artist_item, dict):
            msg = "spotify_track_invalid_artist"
            raise ValueError(msg)
        artist = cast("Mapping[str, object]", artist_item)
        name = artist.get("name")
        if not isinstance(name, str) or not name.strip():
            msg = "spotify_track_missing_artist_name"
            raise ValueError(msg)
        names.append(name.strip())

    return tuple(names)


def _optional_album_name(payload: Mapping[str, object]) -> str | None:
    album = payload.get("album")
    if album is None:
        return None
    if not isinstance(album, dict):
        msg = "spotify_track_invalid_album"
        raise ValueError(msg)
    album_data = cast("Mapping[str, object]", album)
    name = album_data.get("name")
    if name is None:
        return None
    if not isinstance(name, str):
        msg = "spotify_track_invalid_album_name"
        raise ValueError(msg)
    normalized = name.strip()
    return normalized or None


def _optional_isrc(payload: Mapping[str, object]) -> str | None:
    external_ids = payload.get("external_ids")
    if external_ids is None:
        return None
    if not isinstance(external_ids, dict):
        msg = "spotify_track_invalid_external_ids"
        raise ValueError(msg)
    external_id_data = cast("Mapping[str, object]", external_ids)
    isrc = external_id_data.get("isrc")
    if isrc is None:
        return None
    if not isinstance(isrc, str):
        msg = "spotify_track_invalid_isrc"
        raise ValueError(msg)
    normalized = isrc.strip()
    return normalized or None


def _required_string(payload: Mapping[str, object], field_name: str, error_code: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error_code)
    return value.strip()


def _required_env_value(values: Mapping[str, str | None], variable_name: str) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        msg = "missing_credentials"
        raise ValueError(msg)
    return value.strip()
