"""Private-safe Spotify playlist access diagnostics."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from songtrace.providers.spotify_api_access import request_spotify_client_credentials_access_token
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SPOTIFY_USER_ACCESS_TOKEN_ENV,
    validate_spotify_environment,
)
from songtrace.providers.spotify_playlist_membership import (
    PlaylistPayloadRequester,
    PlaylistTrackPagesRequester,
    request_spotify_playlist_payload,
    request_spotify_playlist_track_pages,
)

TokenProvider = Callable[[str, str], str]


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistAccessStatus:
    """Safe diagnostic result for Spotify playlist metadata and item access."""

    spotify_playlist_id: str
    access_mode: str
    metadata_readable: bool
    track_items_readable: bool
    playlist_name: str | None = None
    metadata_failure_reason: str | None = None
    track_items_failure_reason: str | None = None

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
        _validate_failure_state(
            readable=self.metadata_readable,
            failure_reason=self.metadata_failure_reason,
            readable_error="spotify_playlist_metadata_failure_mismatch",
        )
        _validate_failure_state(
            readable=self.track_items_readable,
            failure_reason=self.track_items_failure_reason,
            readable_error="spotify_playlist_tracks_failure_mismatch",
        )


def check_spotify_playlist_access(
    spotify_playlist_id: str,
    env: Mapping[str, str | None] | None = None,
    token_provider: TokenProvider | None = None,
    playlist_payload_requester: PlaylistPayloadRequester | None = None,
    playlist_track_pages_requester: PlaylistTrackPagesRequester | None = None,
    access_mode: str = "client_credentials",
) -> SpotifyPlaylistAccessStatus:
    """Check Spotify playlist metadata and track-item access with the selected access mode."""

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
    playlist_requester = playlist_payload_requester or request_spotify_playlist_payload
    try:
        playlist_payload = playlist_requester(access_token, normalized_playlist_id)
        playlist_name = _optional_string(playlist_payload, "name", "spotify_playlist_invalid_name")
        metadata_readable = True
    except ValueError as error:
        metadata_failure_reason = str(error)

    track_items_readable = False
    track_items_failure_reason: str | None = None
    pages_requester = playlist_track_pages_requester or request_spotify_playlist_track_pages
    try:
        pages_requester(access_token, normalized_playlist_id)
        track_items_readable = True
    except ValueError as error:
        track_items_failure_reason = str(error)

    return SpotifyPlaylistAccessStatus(
        spotify_playlist_id=normalized_playlist_id,
        access_mode=normalized_access_mode,
        playlist_name=playlist_name,
        metadata_readable=metadata_readable,
        metadata_failure_reason=metadata_failure_reason,
        track_items_readable=track_items_readable,
        track_items_failure_reason=track_items_failure_reason,
    )


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


def _validate_failure_state(
    *,
    readable: bool,
    failure_reason: str | None,
    readable_error: str,
) -> None:
    if readable and failure_reason is not None:
        raise ValueError(readable_error)
    if not readable and (failure_reason is None or not failure_reason.strip()):
        raise ValueError(readable_error)


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
