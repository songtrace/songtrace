"""Tests for the Observation domain entity."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from songtrace.domain.observation import Observation, ObservationKind


def test_creates_observation() -> None:
    evidence_id = uuid4()
    observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)

    observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(evidence_id,),
        observed_at=observed_at,
    )

    assert isinstance(observation.id, UUID)
    assert observation.kind is ObservationKind.PLAYLIST_STREAM_GROWTH
    assert observation.summary == "Streams increased after playlist placement."
    assert observation.supporting_evidence_ids == (evidence_id,)
    assert observation.observed_at == observed_at


def test_generates_unique_identifiers() -> None:
    evidence_id = uuid4()
    observed_at = datetime.now(UTC)

    first = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(evidence_id,),
        observed_at=observed_at,
    )
    second = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(evidence_id,),
        observed_at=observed_at,
    )

    assert first.id != second.id


def test_observation_is_immutable() -> None:
    observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        observation.summary = "Changed summary"  # type: ignore[misc]


@pytest.mark.parametrize("summary", ["", " ", "\n"])
def test_rejects_empty_summary(summary: str) -> None:
    with pytest.raises(ValueError, match="summary must not be empty"):
        Observation(
            kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
            summary=summary,
            supporting_evidence_ids=(uuid4(),),
            observed_at=datetime.now(UTC),
        )


def test_rejects_empty_supporting_evidence_ids() -> None:
    with pytest.raises(
        ValueError,
        match="observation must reference at least one supporting evidence item",
    ):
        Observation(
            kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
            summary="Streams increased after playlist placement.",
            supporting_evidence_ids=(),
            observed_at=datetime.now(UTC),
        )


def test_rejects_duplicate_supporting_evidence_ids() -> None:
    evidence_id = uuid4()

    with pytest.raises(
        ValueError,
        match="supporting_evidence_ids must not contain duplicates",
    ):
        Observation(
            kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
            summary="Streams increased after playlist placement.",
            supporting_evidence_ids=(evidence_id, evidence_id),
            observed_at=datetime.now(UTC),
        )


def test_rejects_naive_observed_at() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        Observation(
            kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
            summary="Streams increased after playlist placement.",
            supporting_evidence_ids=(uuid4(),),
            observed_at=datetime(2026, 7, 20, 12, 0),
        )
