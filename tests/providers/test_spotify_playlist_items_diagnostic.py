"""Tests for private-safe Spotify playlist item diagnostics."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from typing import NoReturn
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SPOTIFY_USER_ACCESS_TOKEN_ENV,
    SpotifyPlaylistItemsDiagnostic,
    diagnose_spotify_playlist_items,
)
from songtrace.providers.spotify_playlist_items_diagnostic import (
    request_spotify_minimal_playlist_track_items,
)


def test_diagnose_spotify_playlist_items_reports_all_probes_readable() -> None:
    calls: list[tuple[str, str]] = []

    def pages_requester(access_token: str, playlist_id: str) -> tuple[dict[str, object], ...]:
        calls.append((access_token, playlist_id))
        return ({"items": [], "next": None},)

    status = diagnose_spotify_playlist_items(
        " playlist-id ",
        env={
            SPOTIFY_CLIENT_ID_ENV: " client-id ",
            SPOTIFY_CLIENT_SECRET_ENV: " client-secret ",
        },
        token_provider=lambda client_id, client_secret: f"token-for-{client_id}-{client_secret}",
        playlist_payload_requester=lambda access_token, playlist_id: {
            "id": playlist_id,
            "name": "Hard Rock Classics",
        },
        playlist_track_pages_requester=pages_requester,
        minimal_track_items_requester=lambda access_token, playlist_id: {"items": []},
    )

    assert status == SpotifyPlaylistItemsDiagnostic(
        spotify_playlist_id="playlist-id",
        access_mode="client_credentials",
        playlist_name="Hard Rock Classics",
        metadata_readable=True,
        track_pages_readable=True,
        minimal_track_items_readable=True,
    )
    assert calls == [("token-for-client-id-client-secret", "playlist-id")]
    assert "client-secret" not in str(status)
    assert "token-for" not in str(status)


def test_diagnose_spotify_playlist_items_detects_request_shape_difference() -> None:
    status = diagnose_spotify_playlist_items(
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
        playlist_track_pages_requester=lambda _access_token, _playlist_id: _raise_value_error(
            "spotify_playlist_tracks_http_error_403"
        ),
        minimal_track_items_requester=lambda _access_token, _playlist_id: {"items": []},
    )

    assert status.track_pages_readable is False
    assert status.track_pages_failure_reason == "spotify_playlist_tracks_http_error_403"
    assert status.minimal_track_items_readable is True
    assert status.minimal_track_items_failure_reason is None


def test_diagnose_spotify_playlist_items_reports_both_track_item_failures() -> None:
    status = diagnose_spotify_playlist_items(
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
        playlist_track_pages_requester=lambda _access_token, _playlist_id: _raise_value_error(
            "spotify_playlist_tracks_http_error_403"
        ),
        minimal_track_items_requester=lambda _access_token, _playlist_id: _raise_value_error(
            "spotify_playlist_minimal_tracks_http_error_403"
        ),
    )

    assert status.metadata_readable is True
    assert status.track_pages_readable is False
    assert status.track_pages_failure_reason == "spotify_playlist_tracks_http_error_403"
    assert status.minimal_track_items_readable is False
    assert (
        status.minimal_track_items_failure_reason
        == "spotify_playlist_minimal_tracks_http_error_403"
    )


def test_diagnose_spotify_playlist_items_reports_metadata_failure_safely() -> None:
    status = diagnose_spotify_playlist_items(
        "playlist-id",
        env={
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        playlist_payload_requester=lambda _access_token, _playlist_id: _raise_value_error(
            "spotify_playlist_http_error_404"
        ),
        playlist_track_pages_requester=lambda _access_token, _playlist_id: ({"items": []},),
        minimal_track_items_requester=lambda _access_token, _playlist_id: {"items": []},
    )

    assert status.metadata_readable is False
    assert status.metadata_failure_reason == "spotify_playlist_http_error_404"
    assert status.track_pages_readable is True
    assert status.minimal_track_items_readable is True


def test_diagnose_spotify_playlist_items_supports_user_token_mode() -> None:
    token_calls: list[tuple[str, str]] = []
    probe_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "client-token"

    def minimal_requester(access_token: str, playlist_id: str) -> dict[str, object]:
        probe_calls.append((access_token, playlist_id))
        return {"items": []}

    status = diagnose_spotify_playlist_items(
        "playlist-id",
        env={SPOTIFY_USER_ACCESS_TOKEN_ENV: " SECRET_USER_TOKEN "},
        token_provider=token_provider,
        playlist_payload_requester=lambda _access_token, _playlist_id: {
            "name": "Hard Rock Classics"
        },
        playlist_track_pages_requester=lambda _access_token, _playlist_id: ({"items": []},),
        minimal_track_items_requester=minimal_requester,
        access_mode="user_token",
    )

    assert status.access_mode == "user_token"
    assert status.metadata_readable is True
    assert status.track_pages_readable is True
    assert status.minimal_track_items_readable is True
    assert token_calls == []
    assert probe_calls == [("SECRET_USER_TOKEN", "playlist-id")]
    assert "SECRET_USER_TOKEN" not in str(status)


def test_diagnose_spotify_playlist_items_rejects_missing_user_token() -> None:
    with pytest.raises(ValueError, match="missing_user_token"):
        diagnose_spotify_playlist_items("playlist-id", env={}, access_mode="user_token")


def test_spotify_playlist_items_diagnostic_is_immutable() -> None:
    status = SpotifyPlaylistItemsDiagnostic(
        spotify_playlist_id="playlist-id",
        access_mode="client_credentials",
        metadata_readable=True,
        track_pages_readable=True,
        minimal_track_items_readable=True,
    )

    with pytest.raises(FrozenInstanceError):
        status.track_pages_readable = False  # type: ignore[misc]


def test_request_spotify_minimal_playlist_track_items_uses_minimal_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[Request] = []

    def respond(request: Request, timeout: int) -> _Response:
        captured.append(request)
        assert timeout == 10
        return _Response(b'{"items":[]}')

    monkeypatch.setattr("songtrace.providers.spotify_playlist_items_diagnostic.urlopen", respond)

    payload = request_spotify_minimal_playlist_track_items("SECRET_TOKEN", "playlist id")

    assert payload == {"items": []}
    request = captured[0]
    assert request.full_url == "https://api.spotify.com/v1/playlists/playlist%20id/tracks?limit=1"
    assert request.get_header("Authorization") == "Bearer SECRET_TOKEN"


def test_request_spotify_minimal_playlist_track_items_reports_http_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: Request, timeout: int) -> object:
        assert timeout == 10
        raise HTTPError(
            url="https://api.spotify.com/v1/playlists/playlist-id/tracks?limit=1",
            code=403,
            msg="Forbidden",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_playlist_items_diagnostic.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_playlist_minimal_tracks_http_error_403"):
        request_spotify_minimal_playlist_track_items("SECRET_TOKEN", "playlist-id")


def _raise_value_error(message: str) -> NoReturn:
    raise ValueError(message)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()
