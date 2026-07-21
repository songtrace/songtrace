"""Tests for private-safe Spotify track metadata lookup."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyTrackMetadata,
    lookup_spotify_track_metadata,
)
from songtrace.providers.spotify_track_lookup import request_spotify_track_payload

_VALID_PAYLOAD: dict[str, object] = {
    "id": "spotify-track-id",
    "name": "Everything Is Fading",
    "artists": [{"name": "Warrel Dane"}],
    "album": {"name": "Praises to the War Machine"},
    "external_ids": {"isrc": "USABC0800001"},
}


def test_lookup_spotify_track_metadata_returns_safe_metadata() -> None:
    token_calls: list[tuple[str, str]] = []
    track_calls: list[tuple[str, str]] = []

    def token_provider(client_id: str, client_secret: str) -> str:
        token_calls.append((client_id, client_secret))
        return "SECRET_TOKEN"

    def track_payload_requester(access_token: str, track_id: str) -> dict[str, object]:
        track_calls.append((access_token, track_id))
        return _VALID_PAYLOAD

    metadata = lookup_spotify_track_metadata(
        " spotify-track-id ",
        {
            SPOTIFY_CLIENT_ID_ENV: " SECRET_CLIENT_ID ",
            SPOTIFY_CLIENT_SECRET_ENV: " SECRET_CLIENT_SECRET ",
        },
        token_provider=token_provider,
        track_payload_requester=track_payload_requester,
    )

    assert metadata == SpotifyTrackMetadata(
        spotify_track_id="spotify-track-id",
        title="Everything Is Fading",
        artist_names=("Warrel Dane",),
        album_name="Praises to the War Machine",
        isrc="USABC0800001",
    )
    assert token_calls == [("SECRET_CLIENT_ID", "SECRET_CLIENT_SECRET")]
    assert track_calls == [("SECRET_TOKEN", "spotify-track-id")]
    assert "SECRET" not in str(metadata)


def test_lookup_spotify_track_metadata_allows_missing_optional_isrc() -> None:
    payload = {
        "id": "spotify-track-id",
        "name": "Everything Is Fading",
        "artists": [{"name": "Warrel Dane"}],
        "album": {"name": "Praises to the War Machine"},
    }

    metadata = lookup_spotify_track_metadata(
        "spotify-track-id",
        {
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        },
        token_provider=lambda _client_id, _client_secret: "token",
        track_payload_requester=lambda _access_token, _track_id: payload,
    )

    assert metadata.isrc is None


def test_lookup_spotify_track_metadata_rejects_blank_track_id_without_token_request() -> None:
    calls: list[tuple[str, str]] = []

    with pytest.raises(ValueError, match="spotify_track_id_required"):
        lookup_spotify_track_metadata(
            " ",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
            token_provider=lambda client_id, client_secret: (
                calls.append((client_id, client_secret)) or "token"
            ),
            track_payload_requester=lambda _access_token, _track_id: _VALID_PAYLOAD,
        )

    assert calls == []


def test_lookup_spotify_track_metadata_rejects_missing_credentials() -> None:
    with pytest.raises(ValueError, match="missing_credentials"):
        lookup_spotify_track_metadata(
            "spotify-track-id",
            {},
            token_provider=lambda _client_id, _client_secret: "SECRET_TOKEN",
            track_payload_requester=lambda _access_token, _track_id: _VALID_PAYLOAD,
        )


def test_lookup_spotify_track_metadata_rejects_missing_required_fields() -> None:
    payload = {
        "id": "spotify-track-id",
        "artists": [{"name": "Warrel Dane"}],
    }

    with pytest.raises(ValueError, match="spotify_track_missing_name"):
        lookup_spotify_track_metadata(
            "spotify-track-id",
            {
                SPOTIFY_CLIENT_ID_ENV: "client-id",
                SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
            },
            token_provider=lambda _client_id, _client_secret: "token",
            track_payload_requester=lambda _access_token, _track_id: payload,
        )


def test_spotify_track_metadata_is_immutable() -> None:
    metadata = SpotifyTrackMetadata(
        spotify_track_id="spotify-track-id",
        title="Everything Is Fading",
        artist_names=("Warrel Dane",),
    )

    with pytest.raises(FrozenInstanceError):
        metadata.title = "Changed"  # type: ignore[misc]


def test_request_spotify_track_payload_parses_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b'{"id":"spotify-track-id","name":"Everything Is Fading","artists":[]}')

    monkeypatch.setattr("songtrace.providers.spotify_track_lookup.urlopen", respond)

    payload = request_spotify_track_payload("SECRET_TOKEN", "spotify-track-id")

    assert payload["id"] == "spotify-track-id"


def test_request_spotify_track_payload_rejects_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: object, timeout: int) -> object:
        raise HTTPError(
            url="https://api.spotify.com/v1/tracks/spotify-track-id",
            code=404,
            msg="Not Found",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_track_lookup.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_track_http_error_404"):
        request_spotify_track_payload("SECRET_TOKEN", "spotify-track-id")


def test_request_spotify_track_payload_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b"not-json")

    monkeypatch.setattr("songtrace.providers.spotify_track_lookup.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_track_invalid_json"):
        request_spotify_track_payload("SECRET_TOKEN", "spotify-track-id")


def test_request_spotify_track_payload_rejects_non_object_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b"[]")

    monkeypatch.setattr("songtrace.providers.spotify_track_lookup.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_track_invalid_payload"):
        request_spotify_track_payload("SECRET_TOKEN", "spotify-track-id")


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()
