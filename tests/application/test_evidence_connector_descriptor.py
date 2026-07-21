"""Tests for evidence connector capability descriptors."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from songtrace.application.evidence_connector_descriptor import (
    EvidenceConnectorDescriptor,
    EvidenceIngestionMethod,
)
from songtrace.domain.evidence import EvidenceKind


def test_creates_valid_evidence_connector_descriptor() -> None:
    descriptor = EvidenceConnectorDescriptor(
        source_name=" Spotify for Artists ",
        authentication_method=" OAuth ",
        supported_ingestion_methods=(EvidenceIngestionMethod.OAUTH_API,),
        produced_evidence_kinds=(
            EvidenceKind.AUDIENCE_ACTIVITY,
            EvidenceKind.PLAYLIST_ACTIVITY,
        ),
        freshness_characteristics=" Daily reporting lag. ",
        reliability_characteristics=" Account-authorized platform analytics. ",
    )

    assert descriptor.source_name == "Spotify for Artists"
    assert descriptor.authentication_method == "OAuth"
    assert descriptor.supported_ingestion_methods == (EvidenceIngestionMethod.OAUTH_API,)
    assert descriptor.produced_evidence_kinds == (
        EvidenceKind.AUDIENCE_ACTIVITY,
        EvidenceKind.PLAYLIST_ACTIVITY,
    )
    assert descriptor.freshness_characteristics == "Daily reporting lag."
    assert descriptor.reliability_characteristics == "Account-authorized platform analytics."


def test_descriptor_allows_no_authentication_method() -> None:
    descriptor = EvidenceConnectorDescriptor(
        source_name="CSV upload",
        supported_ingestion_methods=(EvidenceIngestionMethod.CSV_IMPORT,),
        produced_evidence_kinds=(EvidenceKind.ROYALTY_ACTIVITY,),
        freshness_characteristics="Freshness depends on the uploaded file.",
        reliability_characteristics="Depends on user-provided source export.",
    )

    assert descriptor.authentication_method is None


def test_descriptor_is_immutable() -> None:
    descriptor = _descriptor()

    with pytest.raises(FrozenInstanceError):
        descriptor.source_name = "Changed"  # type: ignore[misc]


def test_descriptor_stores_collections_as_immutable_tuples() -> None:
    methods = [EvidenceIngestionMethod.CSV_IMPORT]
    kinds = [EvidenceKind.ROYALTY_ACTIVITY]

    descriptor = EvidenceConnectorDescriptor(
        source_name="Royalty statement upload",
        supported_ingestion_methods=cast(tuple[EvidenceIngestionMethod, ...], methods),
        produced_evidence_kinds=cast(tuple[EvidenceKind, ...], kinds),
        freshness_characteristics="Freshness depends on statement period.",
        reliability_characteristics="Depends on statement source and format.",
    )
    methods.append(EvidenceIngestionMethod.PDF_REPORT)
    kinds.append(EvidenceKind.OTHER)

    assert descriptor.supported_ingestion_methods == (EvidenceIngestionMethod.CSV_IMPORT,)
    assert descriptor.produced_evidence_kinds == (EvidenceKind.ROYALTY_ACTIVITY,)


def test_descriptor_rejects_blank_source_name() -> None:
    with pytest.raises(ValueError, match="source_name must not be blank"):
        _descriptor(source_name="  ")


def test_descriptor_rejects_blank_authentication_method() -> None:
    with pytest.raises(ValueError, match="authentication_method must not be blank"):
        _descriptor(authentication_method="  ")


def test_descriptor_rejects_empty_ingestion_methods() -> None:
    with pytest.raises(ValueError, match="supported_ingestion_methods must not be empty"):
        _descriptor(supported_ingestion_methods=())


def test_descriptor_rejects_duplicate_ingestion_methods() -> None:
    with pytest.raises(ValueError, match="supported_ingestion_methods must not contain duplicates"):
        _descriptor(
            supported_ingestion_methods=(
                EvidenceIngestionMethod.CSV_IMPORT,
                EvidenceIngestionMethod.CSV_IMPORT,
            )
        )


def test_descriptor_rejects_empty_evidence_kinds() -> None:
    with pytest.raises(ValueError, match="produced_evidence_kinds must not be empty"):
        _descriptor(produced_evidence_kinds=())


def test_descriptor_rejects_duplicate_evidence_kinds() -> None:
    with pytest.raises(ValueError, match="produced_evidence_kinds must not contain duplicates"):
        _descriptor(
            produced_evidence_kinds=(
                EvidenceKind.AUDIENCE_ACTIVITY,
                EvidenceKind.AUDIENCE_ACTIVITY,
            )
        )


def test_descriptor_rejects_blank_freshness_characteristics() -> None:
    with pytest.raises(ValueError, match="freshness_characteristics must not be blank"):
        _descriptor(freshness_characteristics=" ")


def test_descriptor_rejects_blank_reliability_characteristics() -> None:
    with pytest.raises(ValueError, match="reliability_characteristics must not be blank"):
        _descriptor(reliability_characteristics=" ")


def _descriptor(
    *,
    source_name: str = "CSV upload",
    authentication_method: str | None = None,
    supported_ingestion_methods: tuple[EvidenceIngestionMethod, ...] = (
        EvidenceIngestionMethod.CSV_IMPORT,
    ),
    produced_evidence_kinds: tuple[EvidenceKind, ...] = (EvidenceKind.AUDIENCE_ACTIVITY,),
    freshness_characteristics: str = "Freshness depends on upload cadence.",
    reliability_characteristics: str = "Reliability depends on source export quality.",
) -> EvidenceConnectorDescriptor:
    return EvidenceConnectorDescriptor(
        source_name=source_name,
        authentication_method=authentication_method,
        supported_ingestion_methods=supported_ingestion_methods,
        produced_evidence_kinds=produced_evidence_kinds,
        freshness_characteristics=freshness_characteristics,
        reliability_characteristics=reliability_characteristics,
    )
