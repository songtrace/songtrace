"""Tests for local Spotify OAuth helpers."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from email.message import Message
from io import BytesIO
from typing import cast
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyUserTokenExchangeStatus,
    build_spotify_authorization_url,
    exchange_spotify_authorization_code,
)
from songtrace.providers.spotify_oauth import request_spotify_authorization_code_token_payload


def test_build_spotify_authorization_url_contains_expected_oauth_fields() -> None:
    result = build_spotify_authorization_url(
        {SPOTIFY_CLIENT_ID_ENV: " client-id "},
        redirect_uri=" http://127.0.0.1:8765/callback ",
        state=" deterministic-state ",
    )

    parsed = urlparse(result.url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.spotify.com"
    assert parsed.path == "/authorize"
    assert query == {
        "client_id": ["client-id"],
        "redirect_uri": ["http://127.0.0.1:8765/callback"],
        "response_type": ["code"],
        "scope": ["playlist-read-private playlist-read-collaborative"],
        "state": ["deterministic-state"],
    }
    assert result.redirect_uri == "http://127.0.0.1:8765/callback"
    assert result.scopes == ("playlist-read-private", "playlist-read-collaborative")
    assert result.state == "deterministic-state"


def test_build_spotify_authorization_url_rejects_missing_client_id() -> None:
    with pytest.raises(ValueError, match="missing_credentials"):
        build_spotify_authorization_url({})


def test_build_spotify_authorization_url_rejects_blank_redirect_state_and_scopes() -> None:
    with pytest.raises(ValueError, match="spotify_redirect_uri_required"):
        build_spotify_authorization_url({SPOTIFY_CLIENT_ID_ENV: "client-id"}, redirect_uri=" ")

    with pytest.raises(ValueError, match="spotify_oauth_state_required"):
        build_spotify_authorization_url({SPOTIFY_CLIENT_ID_ENV: "client-id"}, state=" ")

    with pytest.raises(ValueError, match="spotify_oauth_scopes_required"):
        build_spotify_authorization_url({SPOTIFY_CLIENT_ID_ENV: "client-id"}, scopes=())


def test_spotify_authorization_url_is_immutable() -> None:
    result = build_spotify_authorization_url({SPOTIFY_CLIENT_ID_ENV: "client-id"})

    with pytest.raises(FrozenInstanceError):
        result.state = "changed"  # type: ignore[misc]


def test_exchange_spotify_authorization_code_success_is_private_safe() -> None:
    calls: list[tuple[str, str, str, str]] = []

    def requester(
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> dict[str, object]:
        calls.append((client_id, client_secret, code, redirect_uri))
        return {
            "access_token": "SECRET_USER_TOKEN",
            "expires_in": 3600,
            "refresh_token": "SECRET_REFRESH_TOKEN",
            "scope": "playlist-read-private playlist-read-collaborative",
            "token_type": "Bearer",
        }

    status = exchange_spotify_authorization_code(
        " code ",
        {
            SPOTIFY_CLIENT_ID_ENV: " client-id ",
            SPOTIFY_CLIENT_SECRET_ENV: " client-secret ",
        },
        redirect_uri=" http://127.0.0.1:8765/callback ",
        token_payload_requester=requester,
    )

    assert status.token_request_attempted is True
    assert status.access_token_received is True
    assert status.token_type == "Bearer"
    assert status.expires_in_seconds == 3600
    assert status.scopes == ("playlist-read-private", "playlist-read-collaborative")
    assert status.refresh_token_received is True
    assert status.failure_reason is None
    assert status.access_token == "SECRET_USER_TOKEN"
    assert calls == [("client-id", "client-secret", "code", "http://127.0.0.1:8765/callback")]
    assert "SECRET_USER_TOKEN" not in str(status)
    assert "SECRET_REFRESH_TOKEN" not in str(status)


def test_exchange_spotify_authorization_code_missing_credentials_short_circuits() -> None:
    calls: list[tuple[str, str, str, str]] = []

    def requester(
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> dict[str, object]:
        calls.append((client_id, client_secret, code, redirect_uri))
        return {"access_token": "SECRET_USER_TOKEN"}

    status = exchange_spotify_authorization_code(
        "code",
        {},
        token_payload_requester=requester,
    )

    assert status == SpotifyUserTokenExchangeStatus(
        token_request_attempted=False,
        access_token_received=False,
        failure_reason="missing_credentials",
    )
    assert calls == []


def test_exchange_spotify_authorization_code_reports_safe_request_failure() -> None:
    def requester(
        _client_id: str,
        _client_secret: str,
        _code: str,
        _redirect_uri: str,
    ) -> dict[str, object]:
        raise ValueError("spotify_user_token_http_error_400")

    status = exchange_spotify_authorization_code(
        "code",
        {
            SPOTIFY_CLIENT_ID_ENV: "SECRET_CLIENT_ID",
            SPOTIFY_CLIENT_SECRET_ENV: "SECRET_CLIENT_SECRET",
        },
        token_payload_requester=requester,
    )

    assert status.token_request_attempted is True
    assert status.access_token_received is False
    assert status.failure_reason == "spotify_user_token_http_error_400"
    assert "SECRET_CLIENT_ID" not in str(status)
    assert "SECRET_CLIENT_SECRET" not in str(status)


def test_exchange_spotify_authorization_code_rejects_blank_code() -> None:
    with pytest.raises(ValueError, match="spotify_authorization_code_required"):
        exchange_spotify_authorization_code(" ")


def test_spotify_user_token_exchange_status_is_immutable() -> None:
    status = SpotifyUserTokenExchangeStatus(
        token_request_attempted=False,
        access_token_received=False,
    )

    with pytest.raises(FrozenInstanceError):
        status.access_token_received = True  # type: ignore[misc]


def test_request_spotify_authorization_code_token_payload_sends_expected_form(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[Request] = []

    def respond(request: Request, timeout: int) -> _Response:
        captured.append(request)
        assert timeout == 10
        return _Response(
            b'{"access_token":"SECRET_USER_TOKEN","token_type":"Bearer","expires_in":3600}'
        )

    monkeypatch.setattr("songtrace.providers.spotify_oauth.urlopen", respond)

    payload = request_spotify_authorization_code_token_payload(
        "client-id",
        "client-secret",
        "authorization-code",
        "http://127.0.0.1:8765/callback",
    )

    assert payload["access_token"] == "SECRET_USER_TOKEN"
    request = captured[0]
    assert request.full_url == "https://accounts.spotify.com/api/token"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/x-www-form-urlencoded"
    assert request.get_header("Authorization") == "Basic Y2xpZW50LWlkOmNsaWVudC1zZWNyZXQ="
    request_body = cast("bytes", request.data or b"")
    assert parse_qs(request_body.decode("utf-8")) == {
        "code": ["authorization-code"],
        "grant_type": ["authorization_code"],
        "redirect_uri": ["http://127.0.0.1:8765/callback"],
    }


def test_request_spotify_authorization_code_token_payload_rejects_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_request: Request, timeout: int) -> object:
        assert timeout == 10
        raise HTTPError(
            url="https://accounts.spotify.com/api/token",
            code=400,
            msg="Bad Request",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr("songtrace.providers.spotify_oauth.urlopen", fail)

    with pytest.raises(ValueError, match="spotify_user_token_http_error_400"):
        request_spotify_authorization_code_token_payload(
            "client-id",
            "client-secret",
            "authorization-code",
            "http://127.0.0.1:8765/callback",
        )


def test_request_spotify_authorization_code_token_payload_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(_request: Request, timeout: int) -> _Response:
        assert timeout == 10
        return _Response(b"not-json")

    monkeypatch.setattr("songtrace.providers.spotify_oauth.urlopen", respond)

    with pytest.raises(ValueError, match="spotify_user_token_invalid_json"):
        request_spotify_authorization_code_token_payload(
            "client-id",
            "client-secret",
            "authorization-code",
            "http://127.0.0.1:8765/callback",
        )


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return BytesIO(self._body).read()
