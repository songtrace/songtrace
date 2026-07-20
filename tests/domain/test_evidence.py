"""Tests for the Evidence domain model."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from songtrace.domain.evidence import Evidence, EvidenceKind, EvidenceSignal
from songtrace.domain.evidence_source import EvidenceSource


def test_creates_evidence() -> None:
    observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    occurred_at = datetime(2026, 6, 30, 0, 0, tzinfo=UTC)

    evidence = Evidence(
        source=EvidenceSource("spotify"),
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased for Everything Is Fading.",
        observed_at=observed_at,
        occurred_at=occurred_at,
        reference="spotify-analytics:streams-week-2026-07-20",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    assert isinstance(evidence.id, UUID)
    assert evidence.source == EvidenceSource("spotify")
    assert evidence.kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert evidence.observed_at == observed_at
    assert evidence.occurred_at == occurred_at
    assert evidence.reference == "spotify-analytics:streams-week-2026-07-20"
    assert evidence.signals == (EvidenceSignal.STREAM_GROWTH,)


def test_defaults_to_no_structured_signals() -> None:
    evidence = Evidence(
        source=EvidenceSource("spotify"),
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track was added to a playlist.",
        observed_at=datetime.now(UTC),
    )

    assert evidence.signals == ()


@pytest.mark.parametrize(
    "signals",
    [
        (EvidenceSignal.STREAM_GROWTH, EvidenceSignal.STREAM_GROWTH),
        (EvidenceSignal.PLAYLIST_PLACEMENT, EvidenceSignal.SAVE_GROWTH, EvidenceSignal.SAVE_GROWTH),
    ],
)
def test_rejects_duplicate_signals(signals: tuple[EvidenceSignal, ...]) -> None:
    with pytest.raises(ValueError, match="signals must not contain duplicates"):
        Evidence(
            source=EvidenceSource("spotify"),
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime.now(UTC),
            signals=signals,
        )


@pytest.mark.parametrize(
    ("kind", "signals"),
    [
        (EvidenceKind.MEDIA_COVERAGE, (EvidenceSignal.PLAYLIST_PLACEMENT,)),
        (EvidenceKind.PLAYLIST_ACTIVITY, (EvidenceSignal.STREAM_GROWTH,)),
        (EvidenceKind.ROYALTY_ACTIVITY, (EvidenceSignal.SAVE_GROWTH,)),
    ],
)
def test_rejects_signals_incompatible_with_evidence_kind(
    kind: EvidenceKind,
    signals: tuple[EvidenceSignal, ...],
) -> None:
    with pytest.raises(ValueError, match="signal must be compatible with evidence kind"):
        Evidence(
            source=EvidenceSource("spotify"),
            kind=kind,
            summary="Evidence with an incompatible signal.",
            observed_at=datetime.now(UTC),
            signals=signals,
        )


def test_generates_unique_identifiers() -> None:
    observed_at = datetime.now(UTC)

    first = Evidence(
        source=EvidenceSource("spotify"),
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track was added to a playlist.",
        observed_at=observed_at,
    )
    second = Evidence(
        source=EvidenceSource("spotify"),
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track was added to a playlist.",
        observed_at=observed_at,
    )

    assert first.id != second.id


def test_evidence_is_immutable() -> None:
    evidence = Evidence(
        source=EvidenceSource("youtube"),
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="The video received additional views.",
        observed_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        evidence.summary = "Changed summary"  # type: ignore[misc]


@pytest.mark.parametrize("summary", ["", " ", "\n"])
def test_rejects_empty_summary(summary: str) -> None:
    with pytest.raises(ValueError, match="summary must not be empty"):
        Evidence(
            source=EvidenceSource("manual"),
            kind=EvidenceKind.OTHER,
            summary=summary,
            observed_at=datetime.now(UTC),
        )


def test_rejects_naive_observed_at() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        Evidence(
            source=EvidenceSource("spotify"),
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime(2026, 7, 20, 12, 0),
        )


def test_rejects_naive_occurred_at() -> None:
    with pytest.raises(ValueError, match="occurred_at must be timezone-aware"):
        Evidence(
            source=EvidenceSource("spotify"),
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
            source=EvidenceSource("ascap"),
            kind=EvidenceKind.ROYALTY_ACTIVITY,
            summary="Royalties were reported.",
            observed_at=datetime.now(UTC),
            reference=reference,
        )
