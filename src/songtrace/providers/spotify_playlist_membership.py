"""Private-safe Spotify current playlist membership lookup."""

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

SPOTIFY_PLAYLIST_URL_BASE = "https://api.spotify.com/v1/playlists"

TokenProvider = Callable[[str, str], str]
PlaylistPayloadRequester = Callable[[str, str], Mapping[str, object]]
PlaylistTrackPagesRequester = Callable[[str, str], tuple[Mapping[str, object], ...]]


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistTrackMembership:
    """Safe result for current Spotify playlist track membership."""

    spotify_playlist_id: str
    spotify_track_id: str
    contains_track: bool
    matched_track_ids: tuple[str, ...]
    playlist_name: str | None = None

    def __post_init__(self) -> None:
        if not self.spotify_playlist_id.strip():
            msg = "spotify_playlist_id_required"
            raise ValueError(msg)
        if not self.spotify_track_id.strip():
            msg = "spotify_track_id_required"
            raise ValueError(msg)
        object.__setattr__(self, "matched_track_ids", tuple(self.matched_track_ids))
        if self.contains_track != bool(self.matched_track_ids):
            msg = "spotify_playlist_membership_mismatch"
            raise ValueError(msg)


def lookup_spotify_playlist_track_membership(
    spotify_playlist_id: str,
    spotify_track_id: str,
    env: Mapping[str, str | None] | None = None,
    token_provider: TokenProvider | None = None,
    playlist_payload_requester: PlaylistPayloadRequester | None = None,
    playlist_track_pages_requester: PlaylistTrackPagesRequester | None = None,
) -> SpotifyPlaylistTrackMembership:
    """Lookup whether a Spotify playlist currently contains a Spotify track."""

    normalized_playlist_id = spotify_playlist_id.strip()
    normalized_track_id = spotify_track_id.strip()
    if not normalized_playlist_id:
        msg = "spotify_playlist_id_required"
        raise ValueError(msg)
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

    playlist_requester = playlist_payload_requester or request_spotify_playlist_payload
    playlist_payload = playlist_requester(access_token, normalized_playlist_id)
    playlist_id = _required_string(
        playlist_payload,
        "id",
        "spotify_playlist_missing_id",
    )
    playlist_name = _optional_string(playlist_payload, "name", "spotify_playlist_invalid_name")

    pages_requester = playlist_track_pages_requester or request_spotify_playlist_track_pages
    pages = pages_requester(access_token, normalized_playlist_id)
    matched_track_ids = _matched_track_ids(pages, normalized_track_id)

    return SpotifyPlaylistTrackMembership(
        spotify_playlist_id=playlist_id,
        playlist_name=playlist_name,
        spotify_track_id=normalized_track_id,
        contains_track=bool(matched_track_ids),
        matched_track_ids=matched_track_ids,
    )


def request_spotify_playlist_payload(
    access_token: str, spotify_playlist_id: str
) -> Mapping[str, object]:
    """Request safe Spotify playlist metadata."""

    return _request_spotify_json_object(
        access_token,
        f"{SPOTIFY_PLAYLIST_URL_BASE}/{quote(spotify_playlist_id, safe='')}?fields=id,name",
        "spotify_playlist",
    )


def request_spotify_playlist_track_pages(
    access_token: str,
    spotify_playlist_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Request current Spotify playlist track pages in provider order."""

    url: str | None = (
        f"{SPOTIFY_PLAYLIST_URL_BASE}/{quote(spotify_playlist_id, safe='')}/tracks"
        "?fields=items(track(id)),next&limit=100"
    )
    pages: list[Mapping[str, object]] = []
    while url is not None:
        page = _request_spotify_json_object(access_token, url, "spotify_playlist_tracks")
        pages.append(page)
        next_url = page.get("next")
        if next_url is None:
            url = None
        elif isinstance(next_url, str) and next_url.strip():
            url = next_url
        else:
            msg = "spotify_playlist_tracks_invalid_next"
            raise ValueError(msg)
    return tuple(pages)


def _request_spotify_json_object(
    access_token: str,
    url: str,
    error_prefix: str,
) -> Mapping[str, object]:
    if not access_token.strip():
        msg = "spotify_access_token_required"
        raise ValueError(msg)

    request = Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        msg = f"{error_prefix}_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = f"{error_prefix}_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = f"{error_prefix}_invalid_json"
        raise ValueError(msg) from error

    if not isinstance(payload, dict):
        msg = f"{error_prefix}_invalid_payload"
        raise ValueError(msg)
    return cast("Mapping[str, object]", payload)


def _matched_track_ids(
    pages: tuple[Mapping[str, object], ...],
    spotify_track_id: str,
) -> tuple[str, ...]:
    matches: list[str] = []
    for page in pages:
        items = page.get("items")
        if not isinstance(items, list):
            msg = "spotify_playlist_tracks_missing_items"
            raise ValueError(msg)
        for item_value in cast("list[object]", items):
            if not isinstance(item_value, dict):
                msg = "spotify_playlist_tracks_invalid_item"
                raise ValueError(msg)
            item = cast("Mapping[str, object]", item_value)
            track_value = item.get("track")
            if track_value is None:
                continue
            if not isinstance(track_value, dict):
                msg = "spotify_playlist_tracks_invalid_track"
                raise ValueError(msg)
            track = cast("Mapping[str, object]", track_value)
            current_track_id = _required_string(
                track,
                "id",
                "spotify_playlist_track_missing_id",
            )
            if current_track_id == spotify_track_id:
                matches.append(current_track_id)
    return tuple(matches)


def _required_string(payload: Mapping[str, object], field_name: str, error_code: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error_code)
    return value.strip()


def _optional_string(
    payload: Mapping[str, object],
    field_name: str,
    error_code: str,
) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(error_code)
    normalized = value.strip()
    return normalized or None


def _required_env_value(values: Mapping[str, str | None], variable_name: str) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        msg = "missing_credentials"
        raise ValueError(msg)
    return value.strip()
