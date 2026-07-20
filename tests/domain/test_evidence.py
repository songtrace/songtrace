"""Tests for the Evidence domain model."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from songtrace.domain.evidence import Evidence, EvidenceKind


def test_creates_evidence() -> None:
    observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    occurred_at = datetime(2026, 6, 30, 0, 0, tzinfo=UTC)

    evidence = Evidence(
        source="ascap",
        kind=EvidenceKind.ROYALTY_ACTIVITY,
        summary="A royalty payment was reported for Everything Is Fading.",
        observed_at=observed_at,
        occurred_at=occurred_at,
        reference="statement-2026-q2",
    )

    assert isinstance(evidence.id, UUID)
    assert evidence.source == "ascap"
    assert evidence.kind is EvidenceKind.ROYALTY_ACTIVITY
    assert evidence.observed_at == observed_at
    assert evidence.occurred_at == occurred_at
    assert evidence.reference == "statement-2026-q2"


def test_generates_unique_identifiers() -> None:
    observed_at = datetime.now(UTC)

    first = Evidence(
        source="spotify",
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track was added to a playlist.",
        observed_at=observed_at,
    )
    second = Evidence(
        source="spotify",
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track was added to a playlist.",
        observed_at=observed_at,
    )

    assert first.id != second.id


def test_evidence_is_immutable() -> None:
    evidence = Evidence(
        source="youtube",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="The video received additional views.",
        observed_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        evidence.summary = "Changed summary"  # type: ignore[misc]


@pytest.mark.parametrize("source", ["", " ", "\n"])
def test_rejects_empty_source(source: str) -> None:
    with pytest.raises(ValueError, match="source must not be empty"):
        Evidence(
            source=source,
            kind=EvidenceKind.OTHER,
            summary="Some factual evidence.",
            observed_at=datetime.now(UTC),
        )


@pytest.mark.parametrize("summary", ["", " ", "\n"])
def test_rejects_empty_summary(summary: str) -> None:
    with pytest.raises(ValueError, match="summary must not be empty"):
        Evidence(
            source="manual",
            kind=EvidenceKind.OTHER,
            summary=summary,
            observed_at=datetime.now(UTC),
        )


def test_rejects_naive_observed_at() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        Evidence(
            source="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime(2026, 7, 20, 12, 0),
        )


def test_rejects_naive_occurred_at() -> None:
    with pytest.raises(ValueError, match="occurred_at must be timezone-aware"):
        Evidence(
            source="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime.now(UTC),
            occurred_at=datetime(2026, 7, 19, 12, 0),
        )


@pytest.mark.parametrize("reference", ["", " ", "\n"])
def test_rejects_empty_reference(reference: str) -> None:
    with pytest.raises(
        ValueError,
        match="reference must not be empty when provided",
    ):
        Evidence(
            source="ascap",
            kind=EvidenceKind.ROYALTY_ACTIVITY,
            summary="Royalties were reported.",
            observed_at=datetime.now(UTC),
            reference=reference,
        )
