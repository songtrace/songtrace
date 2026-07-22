"""Local Spotify OAuth helpers for diagnostic development workflows."""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from songtrace.providers.spotify_api_access import SPOTIFY_TOKEN_URL
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    validate_spotify_environment,
)

SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_LOCAL_REDIRECT_URI = "http://127.0.0.1:8765/callback"
SPOTIFY_PLAYLIST_READ_SCOPES = ("playlist-read-private", "playlist-read-collaborative")
SPOTIFY_LOCAL_OAUTH_STATE = "songtrace-local-oauth"

TokenPayloadRequester = Callable[[str, str, str, str], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class SpotifyAuthorizationUrl:
    """Private-safe Spotify authorization URL details."""

    url: str
    redirect_uri: str
    scopes: tuple[str, ...]
    state: str

    def __post_init__(self) -> None:
        if not self.url.strip():
            msg = "spotify_authorization_url_required"
            raise ValueError(msg)
        if not self.redirect_uri.strip():
            msg = "spotify_redirect_uri_required"
            raise ValueError(msg)
        if not self.state.strip():
            msg = "spotify_oauth_state_required"
            raise ValueError(msg)
        if not self.scopes:
            msg = "spotify_oauth_scopes_required"
            raise ValueError(msg)
        object.__setattr__(self, "url", self.url.strip())
        object.__setattr__(self, "redirect_uri", self.redirect_uri.strip())
        object.__setattr__(self, "scopes", tuple(scope.strip() for scope in self.scopes))
        object.__setattr__(self, "state", self.state.strip())


@dataclass(frozen=True, slots=True)
class SpotifyUserTokenExchangeStatus:
    """Private-safe status for a Spotify authorization-code token exchange."""

    token_request_attempted: bool
    access_token_received: bool
    token_type: str | None = None
    expires_in_seconds: int | None = None
    scopes: tuple[str, ...] = ()
    refresh_token_received: bool = False
    failure_reason: str | None = None
    _access_token: str | None = field(default=None, repr=False, compare=False)

    @property
    def access_token(self) -> str | None:
        """Return the short-lived access token for explicit local export only."""

        return self._access_token

    def __post_init__(self) -> None:
        object.__setattr__(self, "scopes", tuple(self.scopes))
        if self.access_token_received and not self._access_token:
            msg = "spotify_user_token_missing_access_token"
            raise ValueError(msg)
        if not self.access_token_received and self._access_token is not None:
            msg = "spotify_user_token_access_token_mismatch"
            raise ValueError(msg)
        if self.access_token_received and self.failure_reason is not None:
            msg = "spotify_user_token_failure_mismatch"
            raise ValueError(msg)


def build_spotify_authorization_url(
    env: Mapping[str, str | None] | None = None,
    *,
    redirect_uri: str = SPOTIFY_LOCAL_REDIRECT_URI,
    state: str = SPOTIFY_LOCAL_OAUTH_STATE,
    scopes: tuple[str, ...] = SPOTIFY_PLAYLIST_READ_SCOPES,
) -> SpotifyAuthorizationUrl:
    """Build a Spotify authorization URL without contacting Spotify."""

    values = os.environ if env is None else env
    client_id = _required_env_value(values, SPOTIFY_CLIENT_ID_ENV)
    normalized_redirect_uri = _required_text(redirect_uri, "spotify_redirect_uri_required")
    normalized_state = _required_text(state, "spotify_oauth_state_required")
    normalized_scopes = _normalized_scopes(scopes)

    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": normalized_redirect_uri,
            "response_type": "code",
            "scope": " ".join(normalized_scopes),
            "state": normalized_state,
        }
    )
    return SpotifyAuthorizationUrl(
        url=f"{SPOTIFY_AUTHORIZE_URL}?{query}",
        redirect_uri=normalized_redirect_uri,
        scopes=normalized_scopes,
        state=normalized_state,
    )


def exchange_spotify_authorization_code(
    code: str,
    env: Mapping[str, str | None] | None = None,
    *,
    redirect_uri: str = SPOTIFY_LOCAL_REDIRECT_URI,
    token_payload_requester: TokenPayloadRequester | None = None,
) -> SpotifyUserTokenExchangeStatus:
    """Exchange a Spotify authorization code for a short-lived user access token."""

    normalized_code = _required_text(code, "spotify_authorization_code_required")
    normalized_redirect_uri = _required_text(redirect_uri, "spotify_redirect_uri_required")
    values = os.environ if env is None else env
    environment = validate_spotify_environment(values)
    if not environment.is_configured:
        return SpotifyUserTokenExchangeStatus(
            token_request_attempted=False,
            access_token_received=False,
            failure_reason="missing_credentials",
        )

    requester = token_payload_requester or request_spotify_authorization_code_token_payload
    try:
        payload = requester(
            _required_env_value(values, SPOTIFY_CLIENT_ID_ENV),
            _required_env_value(values, SPOTIFY_CLIENT_SECRET_ENV),
            normalized_code,
            normalized_redirect_uri,
        )
    except ValueError as error:
        return SpotifyUserTokenExchangeStatus(
            token_request_attempted=True,
            access_token_received=False,
            failure_reason=str(error),
        )

    return _token_exchange_status_from_payload(payload)


def request_spotify_authorization_code_token_payload(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> Mapping[str, object]:
    """Request a Spotify user token payload without storing or printing tokens."""

    credentials = f"{client_id}:{client_secret}".encode()
    authorization = base64.b64encode(credentials).decode("ascii")
    body = urlencode(
        {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    request = Request(
        SPOTIFY_TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        msg = f"spotify_user_token_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = "spotify_user_token_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = "spotify_user_token_invalid_json"
        raise ValueError(msg) from error

    if not isinstance(payload, dict):
        msg = "spotify_user_token_invalid_payload"
        raise ValueError(msg)
    return cast("Mapping[str, object]", payload)


def _token_exchange_status_from_payload(
    payload: Mapping[str, object],
) -> SpotifyUserTokenExchangeStatus:
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        msg = "spotify_user_token_missing_access_token"
        raise ValueError(msg)

    expires_in = payload.get("expires_in")
    if expires_in is not None and not isinstance(expires_in, int):
        msg = "spotify_user_token_invalid_expires_in"
        raise ValueError(msg)

    return SpotifyUserTokenExchangeStatus(
        token_request_attempted=True,
        access_token_received=True,
        token_type=_optional_string(payload, "token_type"),
        expires_in_seconds=expires_in,
        scopes=_scope_tuple(payload.get("scope")),
        refresh_token_received=isinstance(payload.get("refresh_token"), str)
        and bool(cast("str", payload["refresh_token"]).strip()),
        _access_token=access_token.strip(),
    )


def _normalized_scopes(scopes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(scope.strip() for scope in scopes if scope.strip())
    if not normalized:
        msg = "spotify_oauth_scopes_required"
        raise ValueError(msg)
    if len(set(normalized)) != len(normalized):
        msg = "spotify_oauth_duplicate_scopes"
        raise ValueError(msg)
    return normalized


def _scope_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, str):
        msg = "spotify_user_token_invalid_scope"
        raise ValueError(msg)
    return tuple(scope for scope in value.split(" ") if scope)


def _optional_string(payload: Mapping[str, object], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        msg = f"spotify_user_token_invalid_{field_name}"
        raise ValueError(msg)
    normalized = value.strip()
    return normalized or None


def _required_env_value(values: Mapping[str, str | None], variable_name: str) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        msg = "missing_credentials"
        raise ValueError(msg)
    return value.strip()


def _required_text(value: str, error_code: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(error_code)
    return normalized
