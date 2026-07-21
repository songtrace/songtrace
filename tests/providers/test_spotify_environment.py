"""Tests for private-safe Spotify environment validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from songtrace.providers import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyEnvironmentStatus,
    validate_spotify_environment,
)


def test_validate_spotify_environment_reports_present_credentials() -> None:
    status = validate_spotify_environment(
        {
            SPOTIFY_CLIENT_ID_ENV: "client-id",
            SPOTIFY_CLIENT_SECRET_ENV: "client-secret",
        }
    )

    assert status.client_id_present is True
    assert status.client_secret_present is True
    assert status.is_configured is True
    assert status.missing_variables == ()


def test_validate_spotify_environment_reports_missing_client_id() -> None:
    status = validate_spotify_environment({SPOTIFY_CLIENT_SECRET_ENV: "client-secret"})

    assert status.client_id_present is False
    assert status.client_secret_present is True
    assert status.is_configured is False
    assert status.missing_variables == (SPOTIFY_CLIENT_ID_ENV,)


def test_validate_spotify_environment_reports_missing_client_secret() -> None:
    status = validate_spotify_environment({SPOTIFY_CLIENT_ID_ENV: "client-id"})

    assert status.client_id_present is True
    assert status.client_secret_present is False
    assert status.is_configured is False
    assert status.missing_variables == (SPOTIFY_CLIENT_SECRET_ENV,)


def test_validate_spotify_environment_treats_blank_values_as_missing() -> None:
    status = validate_spotify_environment(
        {
            SPOTIFY_CLIENT_ID_ENV: "  ",
            SPOTIFY_CLIENT_SECRET_ENV: "",
        }
    )

    assert status.client_id_present is False
    assert status.client_secret_present is False
    assert status.is_configured is False
    assert status.missing_variables == (
        SPOTIFY_CLIENT_ID_ENV,
        SPOTIFY_CLIENT_SECRET_ENV,
    )


def test_spotify_environment_status_is_immutable() -> None:
    status = SpotifyEnvironmentStatus(client_id_present=True, client_secret_present=True)

    with pytest.raises(FrozenInstanceError):
        status.client_id_present = False  # type: ignore[misc]
