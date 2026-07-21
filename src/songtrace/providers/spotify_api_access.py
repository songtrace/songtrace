"""Private-safe Spotify API access validation."""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyEnvironmentStatus,
    validate_spotify_environment,
)

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

TokenRequester = Callable[[str, str], None]


@dataclass(frozen=True, slots=True)
class SpotifyApiAccessStatus:
    """Private-safe status for Spotify API access validation."""

    environment: SpotifyEnvironmentStatus
    token_request_attempted: bool
    access_granted: bool
    failure_reason: str | None = None


def validate_spotify_api_access(
    env: Mapping[str, str | None] | None = None,
    token_requester: TokenRequester | None = None,
) -> SpotifyApiAccessStatus:
    """Validate Spotify API access without exposing credentials or tokens."""

    values = os.environ if env is None else env
    environment = validate_spotify_environment(values)
    if not environment.is_configured:
        return SpotifyApiAccessStatus(
            environment=environment,
            token_request_attempted=False,
            access_granted=False,
            failure_reason="missing_credentials",
        )

    requester = token_requester or request_spotify_client_credentials_token
    try:
        requester(
            _required_env_value(values, SPOTIFY_CLIENT_ID_ENV),
            _required_env_value(values, SPOTIFY_CLIENT_SECRET_ENV),
        )
    except ValueError as error:
        return SpotifyApiAccessStatus(
            environment=environment,
            token_request_attempted=True,
            access_granted=False,
            failure_reason=str(error),
        )

    return SpotifyApiAccessStatus(
        environment=environment,
        token_request_attempted=True,
        access_granted=True,
    )


def request_spotify_client_credentials_token(client_id: str, client_secret: str) -> None:
    """Request and validate a Spotify client-credentials token without returning it."""

    credentials = f"{client_id}:{client_secret}".encode()
    authorization = base64.b64encode(credentials).decode("ascii")
    body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
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
        msg = f"spotify_token_http_error_{error.code}"
        raise ValueError(msg) from error
    except URLError as error:
        msg = "spotify_token_network_error"
        raise ValueError(msg) from error
    except json.JSONDecodeError as error:
        msg = "spotify_token_invalid_json"
        raise ValueError(msg) from error

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        msg = "spotify_token_missing_access_token"
        raise ValueError(msg)


def _required_env_value(values: Mapping[str, str | None], variable_name: str) -> str:
    value = values.get(variable_name)
    if value is None or not value.strip():
        msg = "missing_credentials"
        raise ValueError(msg)
    return value.strip()
