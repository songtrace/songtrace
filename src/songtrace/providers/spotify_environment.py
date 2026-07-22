"""Private-safe Spotify developer environment validation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

SPOTIFY_CLIENT_ID_ENV = "SONGTRACE_SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET_ENV = "SONGTRACE_SPOTIFY_CLIENT_SECRET"
SPOTIFY_USER_ACCESS_TOKEN_ENV = "SONGTRACE_SPOTIFY_USER_ACCESS_TOKEN"


@dataclass(frozen=True, slots=True)
class SpotifyEnvironmentStatus:
    """Private-safe status for local Spotify developer credential configuration."""

    client_id_present: bool
    client_secret_present: bool

    @property
    def is_configured(self) -> bool:
        """Return whether all required Spotify environment variables are present."""

        return self.client_id_present and self.client_secret_present

    @property
    def missing_variables(self) -> tuple[str, ...]:
        """Return missing required variable names without exposing values."""

        missing: list[str] = []
        if not self.client_id_present:
            missing.append(SPOTIFY_CLIENT_ID_ENV)
        if not self.client_secret_present:
            missing.append(SPOTIFY_CLIENT_SECRET_ENV)
        return tuple(missing)


def validate_spotify_environment(
    env: Mapping[str, str | None] | None = None,
) -> SpotifyEnvironmentStatus:
    """Validate required Spotify environment variable presence without exposing values."""

    values = os.environ if env is None else env
    return SpotifyEnvironmentStatus(
        client_id_present=_has_value(values.get(SPOTIFY_CLIENT_ID_ENV)),
        client_secret_present=_has_value(values.get(SPOTIFY_CLIENT_SECRET_ENV)),
    )


def _has_value(value: str | None) -> bool:
    return value is not None and bool(value.strip())
