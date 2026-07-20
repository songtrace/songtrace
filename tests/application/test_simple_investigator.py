"""Tests for the first deterministic investigation service."""

from datetime import UTC, datetime
from uuid import uuid4

from songtrace.application.rule_catalog import RuleCatalog
from songtrace.application.simple_investigator import SimpleInvestigator
from songtrace.domain.confidence import Confidence, ConfidenceLevel
from songtrace.domain.investigation_rule import InvestigationRule
from songtrace.domain.observation import Observation, ObservationKind


def test_infers_playlist_conclusion_from_catalog_rule() -> None:
    created_at = datetime(2026, 7, 20, 21, 0, tzinfo=UTC)
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    save_observation = _observation(ObservationKind.PLAYLIST_SAVE_GROWTH)

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
    assert conclusion.confidence.level is ConfidenceLevel.HIGH
    assert conclusion.confidence.rationale == (
        "Stream and save activity both increased after the playlist placement."
    )
    assert conclusion.created_at == created_at


def test_uses_exact_matching_observation_ids() -> None:
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    save_observation = _observation(ObservationKind.PLAYLIST_SAVE_GROWTH)

    result = SimpleInvestigator().investigate(observations=(stream_observation, save_observation))

    assert result.conclusions[0].supporting_observation_ids == (
        stream_observation.id,
        save_observation.id,
    )


def test_returns_no_conclusion_when_required_observation_kind_is_missing() -> None:
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)

    result = SimpleInvestigator().investigate(observations=(stream_observation,))

    assert result.observations == (stream_observation,)
    assert result.conclusions == ()


def test_ignores_keyword_looking_summary_text() -> None:
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

    result = SimpleInvestigator().investigate(
        observations=(stream_observation, second_stream_observation)
    )

    assert result.conclusions == ()


def test_matching_observation_ids_follow_rule_order_when_observations_are_reordered() -> None:
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    save_observation = _observation(ObservationKind.PLAYLIST_SAVE_GROWTH)

    result = SimpleInvestigator().investigate(observations=(save_observation, stream_observation))

    assert result.conclusions[0].supporting_observation_ids == (
        stream_observation.id,
        save_observation.id,
    )


def test_evaluates_supplied_catalog() -> None:
    created_at = datetime(2026, 7, 20, 21, 0, tzinfo=UTC)
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    custom_rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
        conclusion_statement="Playlist placement is associated with stream growth.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A stream-growth observation is present.",
        ),
    )
    catalog = RuleCatalog(rules=(custom_rule,))

    result = SimpleInvestigator(clock=lambda: created_at, rule_catalog=catalog).investigate(
        observations=(stream_observation,)
    )

    assert len(result.conclusions) == 1
    assert result.conclusions[0].statement == "Playlist placement is associated with stream growth."
    assert result.conclusions[0].supporting_observation_ids == (stream_observation.id,)
    assert result.conclusions[0].confidence == custom_rule.confidence
    assert result.conclusions[0].created_at == created_at


def test_each_matching_rule_produces_conclusion_and_non_matching_rules_are_ignored() -> None:
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    stream_rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
        conclusion_statement="Stream growth is present.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A stream-growth observation is present.",
        ),
    )
    save_rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_SAVE_GROWTH,),
        conclusion_statement="Save growth is present.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A save-growth observation is present.",
        ),
    )
    catalog = RuleCatalog(rules=(stream_rule, save_rule))

    result = SimpleInvestigator(rule_catalog=catalog).investigate(
        observations=(stream_observation,)
    )

    assert [conclusion.statement for conclusion in result.conclusions] == [
        "Stream growth is present."
    ]


def test_matching_conclusions_preserve_catalog_order() -> None:
    stream_observation = _observation(ObservationKind.PLAYLIST_STREAM_GROWTH)
    save_observation = _observation(ObservationKind.PLAYLIST_SAVE_GROWTH)
    first_rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_SAVE_GROWTH,),
        conclusion_statement="Save growth is present.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A save-growth observation is present.",
        ),
    )
    second_rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
        conclusion_statement="Stream growth is present.",
        confidence=Confidence(
            level=ConfidenceLevel.MEDIUM,
            rationale="A stream-growth observation is present.",
        ),
    )
    catalog = RuleCatalog(rules=(first_rule, second_rule))

    result = SimpleInvestigator(rule_catalog=catalog).investigate(
        observations=(stream_observation, save_observation)
    )

    assert [conclusion.statement for conclusion in result.conclusions] == [
        "Save growth is present.",
        "Stream growth is present.",
    ]


def _observation(kind: ObservationKind) -> Observation:
    return Observation(
        kind=kind,
        summary=f"{kind.value} observation.",
        supporting_evidence_ids=(uuid4(),),
        observed_at=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
    )
