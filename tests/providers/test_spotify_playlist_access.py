"""Tests for private-safe Spotify playlist access diagnostics."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import NoReturn

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SPOTIFY_USER_ACCESS_TOKEN_ENV,
    SpotifyPlaylistAccessStatus,
    check_spotify_playlist_access,
)


def test_check_spotify_playlist_access_reports_readable_metadata_and_tracks() -> None:
    token_calls: list[tuple[str, str]] = []
    playlist_calls: list[tuple[str, str]] = []
    track_page_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "SECRET_TOKEN"

    def playlist_requester(access_token: str, playlist_id: str) -> dict[str, object]:
        playlist_calls.append((access_token, playlist_id))
        return {"id": playlist_id, "name": "Hard Rock Classics"}

    def track_pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        track_page_calls.append((access_token, playlist_id))
        return ({"items": [], "next": None},)

    status = check_spotify_playlist_access(
        " playlist-id ",
        env={
            SPOTIFY_CLIENT_ID_ENV: " SECRET_CLIENT_ID ",
            SPOTIFY_CLIENT_SECRET_ENV: " SECRET_CLIENT_SECRET ",
        },
        token_provider=token_provider,
        playlist_payload_requester=playlist_requester,
        playlist_track_pages_requester=track_pages_requester,
    )

    assert status == SpotifyPlaylistAccessStatus(
        spotify_playlist_id="playlist-id",
        access_mode="client_credentials",
        playlist_name="Hard Rock Classics",
        metadata_readable=True,
        track_items_readable=True,
    )
    assert token_calls == [("SECRET_CLIENT_ID", "SECRET_CLIENT_SECRET")]
    assert playlist_calls == [("SECRET_TOKEN", "playlist-id")]
    assert track_page_calls == [("SECRET_TOKEN", "playlist-id")]
    assert "SECRET" not in str(status)


def test_check_spotify_playlist_access_reports_metadata_failure_and_still_checks_tracks() -> None:
    track_page_calls: list[tuple[str, str]] = []

    def track_pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        track_page_calls.append((access_token, playlist_id))
        return ({"items": [], "next": None},)

    status = check_spotify_playlist_access(
        "playlist-id",
        env={
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        playlist_payload_requester=lambda _access_token, _playlist_id: (_raise_value_error)(
            "spotify_playlist_http_error_404"
        ),
        playlist_track_pages_requester=track_pages_requester,
    )

    assert status.metadata_readable is False
    assert status.metadata_failure_reason == "spotify_playlist_http_error_404"
    assert status.track_items_readable is True
    assert status.track_items_failure_reason is None
    assert track_page_calls == [("token", "playlist-id")]


def test_check_spotify_playlist_access_reports_track_items_failure() -> None:
    status = check_spotify_playlist_access(
        "playlist-id",
        env={
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        playlist_payload_requester=lambda _access_token, _playlist_id: {
            "id": "playlist-id",
            "name": "Hard Rock Classics",
        },
        playlist_track_pages_requester=lambda _access_token, _playlist_id: (_raise_value_error)(
            "spotify_playlist_tracks_http_error_403"
        ),
    )

    assert status.metadata_readable is True
    assert status.metadata_failure_reason is None
    assert status.track_items_readable is False
    assert status.track_items_failure_reason == "spotify_playlist_tracks_http_error_403"


def test_check_spotify_playlist_access_supports_user_token_mode() -> None:
    token_calls: list[tuple[str, str]] = []
    playlist_calls: list[tuple[str, str]] = []
    track_page_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "client-credentials-token"

    def playlist_requester(access_token: str, playlist_id: str) -> dict[str, object]:
        playlist_calls.append((access_token, playlist_id))
        return {"id": playlist_id, "name": "Hard Rock Classics"}

    def track_pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        track_page_calls.append((access_token, playlist_id))
        return ({"items": [], "next": None},)

    status = check_spotify_playlist_access(
        "playlist-id",
        env={SPOTIFY_USER_ACCESS_TOKEN_ENV: " SECRET_USER_TOKEN "},
        token_provider=token_provider,
        playlist_payload_requester=playlist_requester,
        playlist_track_pages_requester=track_pages_requester,
        access_mode="user_token",
    )

    assert status == SpotifyPlaylistAccessStatus(
        spotify_playlist_id="playlist-id",
        access_mode="user_token",
        playlist_name="Hard Rock Classics",
        metadata_readable=True,
        track_items_readable=True,
    )
    assert token_calls == []
    assert playlist_calls == [("SECRET_USER_TOKEN", "playlist-id")]
    assert track_page_calls == [("SECRET_USER_TOKEN", "playlist-id")]
    assert "SECRET_USER_TOKEN" not in str(status)


def test_check_spotify_playlist_access_reports_user_token_track_items_failure() -> None:
    status = check_spotify_playlist_access(
        "playlist-id",
        env={SPOTIFY_USER_ACCESS_TOKEN_ENV: "user-token"},
        playlist_payload_requester=lambda _access_token, _playlist_id: {
            "id": "playlist-id",
            "name": "Hard Rock Classics",
        },
        playlist_track_pages_requester=lambda _access_token, _playlist_id: (_raise_value_error)(
            "spotify_playlist_tracks_http_error_403"
        ),
        access_mode="user_token",
    )

    assert status.access_mode == "user_token"
    assert status.metadata_readable is True
    assert status.track_items_readable is False
    assert status.track_items_failure_reason == "spotify_playlist_tracks_http_error_403"


def test_check_spotify_playlist_access_rejects_missing_user_token() -> None:
    with pytest.raises(ValueError, match="missing_user_token"):
        check_spotify_playlist_access("playlist-id", env={}, access_mode="user_token")

    with pytest.raises(ValueError, match="missing_user_token"):
        check_spotify_playlist_access(
            "playlist-id",
            env={SPOTIFY_USER_ACCESS_TOKEN_ENV: " "},
            access_mode="user_token",
        )


def test_check_spotify_playlist_access_rejects_invalid_access_mode() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_access_mode_invalid"):
        check_spotify_playlist_access("playlist-id", env={}, access_mode="invalid")


def test_spotify_playlist_access_status_is_immutable() -> None:
    status = SpotifyPlaylistAccessStatus(
        spotify_playlist_id="playlist-id",
        access_mode="client_credentials",
        metadata_readable=True,
        track_items_readable=True,
    )

    with pytest.raises(FrozenInstanceError):
        status.track_items_readable = False  # type: ignore[misc]


def test_spotify_playlist_access_status_rejects_inconsistent_failures() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_metadata_failure_mismatch"):
        SpotifyPlaylistAccessStatus(
            spotify_playlist_id="playlist-id",
            access_mode="client_credentials",
            metadata_readable=True,
            metadata_failure_reason="spotify_playlist_http_error_404",
            track_items_readable=True,
        )

    with pytest.raises(ValueError, match="spotify_playlist_tracks_failure_mismatch"):
        SpotifyPlaylistAccessStatus(
            spotify_playlist_id="playlist-id",
            access_mode="client_credentials",
            metadata_readable=True,
            track_items_readable=False,
        )


def test_check_spotify_playlist_access_rejects_blank_playlist_id() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_id_required"):
        check_spotify_playlist_access(" ")


def test_check_spotify_playlist_access_rejects_missing_credentials() -> None:
    with pytest.raises(ValueError, match="missing_credentials"):
        check_spotify_playlist_access("playlist-id", env={})


def _raise_value_error(message: str) -> NoReturn:
    raise ValueError(message)
