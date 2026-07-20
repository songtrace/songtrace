"""Tests for the first deterministic investigation service."""

from datetime import UTC, datetime
from uuid import uuid4

from songtrace.application.simple_investigator import SimpleInvestigator
from songtrace.domain.confidence import ConfidenceLevel
from songtrace.domain.observation import Observation, ObservationKind


def test_infers_playlist_conclusion_from_matching_observation_kinds() -> None:
    created_at = datetime(2026, 7, 20, 21, 0, tzinfo=UTC)

    stream_observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(uuid4(), uuid4()),
        observed_at=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
    )
    save_observation = Observation(
        kind=ObservationKind.PLAYLIST_SAVE_GROWTH,
        summary="Save activity increased after playlist placement.",
        supporting_evidence_ids=(uuid4(), uuid4()),
        observed_at=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
    )

    investigator = SimpleInvestigator(clock=lambda: created_at)

    result = investigator.investigate(observations=(stream_observation, save_observation))

    assert result.observations == (
        stream_observation,
        save_observation,
    )
    assert len(result.conclusions) == 1

    conclusion = result.conclusions[0]

    assert (
        conclusion.statement
        == "Editorial playlist placement likely drove renewed listener engagement."
    )
    assert conclusion.supporting_observation_ids == (
        stream_observation.id,
        save_observation.id,
    )
    assert conclusion.confidence.level is ConfidenceLevel.HIGH
    assert conclusion.created_at == created_at


def test_returns_no_conclusion_when_save_observation_is_missing() -> None:
    stream_observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )

    investigator = SimpleInvestigator()

    result = investigator.investigate(observations=(stream_observation,))

    assert result.observations == (stream_observation,)
    assert result.conclusions == ()


def test_summary_text_does_not_control_matching() -> None:
    stream_observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Listener behavior changed after a curated feature.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )
    save_observation = Observation(
        kind=ObservationKind.PLAYLIST_SAVE_GROWTH,
        summary="Collection behavior changed after a curated feature.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )

    investigator = SimpleInvestigator()

    result = investigator.investigate(observations=(stream_observation, save_observation))

    assert len(result.conclusions) == 1


def test_summary_keywords_do_not_match_without_required_observation_kinds() -> None:
    stream_observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Streams increased after playlist placement.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )
    second_stream_observation = Observation(
        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        summary="Save activity increased after playlist placement.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime.now(UTC),
    )

    investigator = SimpleInvestigator()

    result = investigator.investigate(observations=(stream_observation, second_stream_observation))

    assert result.conclusions == ()
