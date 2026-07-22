"""Private-safe Spotify playlist item access diagnostics."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from songtrace.providers.spotify_api_access import request_spotify_client_credentials_access_token
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SPOTIFY_USER_ACCESS_TOKEN_ENV,
    validate_spotify_environment,
)
from songtrace.providers.spotify_playlist_membership import (
    SPOTIFY_PLAYLIST_URL_BASE,
    PlaylistPayloadRequester,
    PlaylistTrackPagesRequester,
    request_spotify_playlist_payload,
    request_spotify_playlist_track_pages,
)

TokenProvider = Callable[[str, str], str]
MinimalTrackItemsRequester = Callable[[str, str], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistItemsDiagnostic:
    """Private-safe result for Spotify playlist item access probes."""

    spotify_playlist_id: str
    access_mode: str
    metadata_readable: bool
    track_pages_readable: bool
    minimal_track_items_readable: bool
    playlist_name: str | None = None
    metadata_failure_reason: str | None = None
    track_pages_failure_reason: str | None = None
    minimal_track_items_failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.spotify_playlist_id.strip():
            msg = "spotify_playlist_id_required"
            raise ValueError(msg)
        if not self.access_mode.strip():
            msg = "spotify_access_mode_required"
            raise ValueError(msg)
        object.__setattr__(self, "spotify_playlist_id", self.spotify_playlist_id.strip())
        object.__setattr__(self, "access_mode", self.access_mode.strip())
        if self.playlist_name is not None:
            normalized_name = self.playlist_name.strip()
            object.__setattr__(self, "playlist_name", normalized_name or None)
        _validate_probe_state(self.metadata_readable, self.metadata_failure_reason)
        _validate_probe_state(self.track_pages_readable, self.track_pages_failure_reason)
        _validate_probe_state(
            self.minimal_track_items_readable,
            self.minimal_track_items_failure_reason,
        )


def diagnose_spotify_playlist_items(
    spotify_playlist_id: str,
    env: Mapping[str, str | None] | None = None,
    token_provider: TokenProvider | None = None,
    playlist_payload_requester: PlaylistPayloadRequester | None = None,
    playlist_track_pages_requester: PlaylistTrackPagesRequester | None = None,
    minimal_track_items_requester: MinimalTrackItemsRequester | None = None,
    access_mode: str = "client_credentials",
) -> SpotifyPlaylistItemsDiagnostic:
    """Diagnose Spotify playlist item access with multiple safe request shapes."""

    normalized_playlist_id = spotify_playlist_id.strip()
    if not normalized_playlist_id:
        msg = "spotify_playlist_id_required"
        raise ValueError(msg)

    values = os.environ if env is None else env
    normalized_access_mode = access_mode.strip()
    access_token = _access_token_for_mode(values, normalized_access_mode, token_provider)

    playlist_name: str | None = None
    metadata_readable = False
    metadata_failure_reason: str | None = None
    metadata_requester = playlist_payload_requester or request_spotify_playlist_payload
    try:
        metadata_payload = metadata_requester(access_token, normalized_playlist_id)
        playlist_name = _optional_string(metadata_payload, "name", "spotify_playlist_invalid_name")
        metadata_readable = True
    except ValueError as error:
        metadata_failure_reason = str(error)

    track_pages_readable = False
    track_pages_failure_reason: str | None = None
    pages_requester = playlist_track_pages_requester or request_spotify_playlist_track_pages
    try:
        pages_requester(access_token, normalized_playlist_id)
        track_pages_readable = True
    except ValueError as error:
        track_pages_failure_reason = str(error)

    minimal_track_items_readable = False
    minimal_track_items_failure_reason: str | None = None
    minimal_requester = (
        minimal_track_items_requester or request_spotify_minimal_playlist_track_items
    )
    try:
        minimal_requester(access_token, normalized_playlist_id)
        minimal_track_items_readable = True
    except ValueError as error:
        minimal_track_items_failure_reason = str(error)

    return SpotifyPlaylistItemsDiagnostic(
        spotify_playlist_id=normalized_playlist_id,
        access_mode=normalized_access_mode,
        playlist_name=playlist_name,
        metadata_readable=metadata_readable,
        metadata_failure_reason=metadata_failure_reason,
        track_pages_readable=track_pages_readable,
        track_pages_failure_reason=track_pages_failure_reason,
        minimal_track_items_readable=minimal_track_items_readable,
        minimal_track_items_failure_reason=minimal_track_items_failure_reason,
    )


def request_spotify_minimal_playlist_track_items(
    access_token: str,
    spotify_playlist_id: str,
) -> Mapping[str, object]:
    """Request a minimal Spotify playlist tracks page without custom field projection."""

    if not access_token.strip():
        msg = "spotify_access_token_required"
        raise ValueError(msg)

    request = Request(
        f"{SPOTIFY_PLAYLIST_URL_BASE}/{quote(spotify_playlist_id, safe='')}/tracks?limit=1",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        msg = f"spotify_playlist_minimal_tracks_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = "spotify_playlist_minimal_tracks_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = "spotify_playlist_minimal_tracks_invalid_json"
        raise ValueError(msg) from error

    if not isinstance(payload, dict):
        msg = "spotify_playlist_minimal_tracks_invalid_payload"
        raise ValueError(msg)
    return cast("Mapping[str, object]", payload)


def _access_token_for_mode(
    values: Mapping[str, str | None],
    access_mode: str,
    token_provider: TokenProvider | None,
) -> str:
    match access_mode:
        case "client_credentials":
            environment = validate_spotify_environment(values)
            if not environment.is_configured:
                msg = "missing_credentials"
                raise ValueError(msg)
            requester = token_provider or request_spotify_client_credentials_access_token
            return requester(
                _required_env_value(values, SPOTIFY_CLIENT_ID_ENV),
                _required_env_value(values, SPOTIFY_CLIENT_SECRET_ENV),
            )
        case "user_token":
            return _required_env_value(values, SPOTIFY_USER_ACCESS_TOKEN_ENV, "missing_user_token")
        case _:
            msg = "spotify_playlist_access_mode_invalid"
            raise ValueError(msg)


def _validate_probe_state(readable: bool, failure_reason: str | None) -> None:
    if readable and failure_reason is not None:
        msg = "spotify_playlist_items_diagnostic_failure_mismatch"
        raise ValueError(msg)
    if not readable and (failure_reason is None or not failure_reason.strip()):
        msg = "spotify_playlist_items_diagnostic_failure_mismatch"
        raise ValueError(msg)


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


def _required_env_value(
    values: Mapping[str, str | None],
    variable_name: str,
    missing_error: str = "missing_credentials",
) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        raise ValueError(missing_error)
    return value.strip()
