"""Tests for Spotify connector capability planning metadata."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from songtrace.application import EvidenceConnectorDescriptor, EvidenceIngestionMethod
from songtrace.domain.evidence import EvidenceKind
from songtrace.providers import spotify_connector_descriptor


def test_spotify_connector_descriptor_describes_planned_capabilities() -> None:
    descriptor = spotify_connector_descriptor()

    assert descriptor.source_name == "spotify"
    assert descriptor.authentication_method is not None
    assert "OAuth" in descriptor.authentication_method
    assert descriptor.supported_ingestion_methods == (
        EvidenceIngestionMethod.REST_API,
        EvidenceIngestionMethod.OAUTH_API,
        EvidenceIngestionMethod.CSV_IMPORT,
    )
    assert descriptor.produced_evidence_kinds == (
        EvidenceKind.AUDIENCE_ACTIVITY,
        EvidenceKind.PLAYLIST_ACTIVITY,
    )
    assert "reporting lag" in descriptor.freshness_characteristics
    assert "direct or a proxy" in descriptor.reliability_characteristics


def test_spotify_connector_descriptor_returns_immutable_descriptor() -> None:
    descriptor = spotify_connector_descriptor()

    assert isinstance(descriptor, EvidenceConnectorDescriptor)
    with pytest.raises(FrozenInstanceError):
        descriptor.source_name = "changed"  # type: ignore[misc]


def test_spotify_connector_descriptor_does_not_expose_api_behavior() -> None:
    descriptor = spotify_connector_descriptor()

    assert not hasattr(descriptor, "load")
    assert not hasattr(descriptor, "client")
    assert not hasattr(descriptor, "token")
