"""Tests for private-safe Spotify API access validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    validate_spotify_api_access,
)
from songtrace.providers.spotify_api_access import request_spotify_client_credentials_token


def test_validate_spotify_api_access_missing_credentials_short_circuits_without_http_call() -> None:
    calls: list[tuple[str, str]] = []

    status = validate_spotify_api_access(
        {},
        token_requester=lambda client_id, client_secret: calls.append((client_id, client_secret)),
    )

    assert status.environment.is_configured is False
    assert status.token_request_attempted is False
    assert status.access_granted is False
    assert status.failure_reason == "missing_credentials"
    assert calls == []


def test_validate_spotify_api_access_success() -> None:
    calls: list[tuple[str, str]] = []

    status = validate_spotify_api_access(
        {
            SPOTIFY_CLIENT_ID_ENV: " client-id ",
            SPOTIFY_CLIENT_SECRET_ENV: " client-secret ",
        },
        token_requester=lambda client_id, client_secret: calls.append((client_id, client_secret)),
    )

    assert status.environment.is_configured is True
    assert status.token_request_attempted is True
    assert status.access_granted is True
    assert status.failure_reason is None
    assert calls == [("client-id", "client-secret")]


def test_validate_spotify_api_access_failure_is_private_safe() -> None:
    def fail(_client_id: str, _client_secret: str) -> None:
        raise ValueError("spotify_token_http_error_401")

    status = validate_spotify_api_access(
        {
            SPOTIFY_CLIENT_ID_ENV: "SECRET_CLIENT_ID",
            SPOTIFY_CLIENT_SECRET_ENV: "SECRET_CLIENT_SECRET",
        },
        token_requester=fail,
    )

    assert status.token_request_attempted is True
    assert status.access_granted is False
    assert status.failure_reason == "spotify_token_http_error_401"
    assert "SECRET" not in str(status)


def test_spotify_api_access_status_is_immutable() -> None:
    status = validate_spotify_api_access({})

    with pytest.raises(FrozenInstanceError):
        status.access_granted = True  # type: ignore[misc]


def test_request_spotify_client_credentials_token_accepts_successful_token_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b'{"access_token":"SECRET_TOKEN"}')

    monkeypatch.setattr("songtrace.providers.spotify_api_access.urlopen", respond)

    result = request_spotify_client_credentials_token("client-id", "client-secret")

    assert result is None


def test_request_spotify_client_credentials_token_rejects_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: object, timeout: int) -> object:
        raise HTTPError(
            url="https://accounts.spotify.com/api/token",
            code=401,
            msg="Unauthorized",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_api_access.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_token_http_error_401"):
        request_spotify_client_credentials_token("client-id", "client-secret")


def test_request_spotify_client_credentials_token_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b"not-json")

    monkeypatch.setattr("songtrace.providers.spotify_api_access.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_token_invalid_json"):
        request_spotify_client_credentials_token("client-id", "client-secret")


def test_request_spotify_client_credentials_token_rejects_missing_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: object, timeout: int) -> _Response:
        return _Response(b'{"token_type":"Bearer"}')

    monkeypatch.setattr("songtrace.providers.spotify_api_access.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_token_missing_access_token"):
        request_spotify_client_credentials_token("client-id", "client-secret")


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()
