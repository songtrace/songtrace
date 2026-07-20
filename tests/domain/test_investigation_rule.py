"""Tests for immutable investigation rule definitions."""

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from songtrace.domain.confidence import Confidence, ConfidenceLevel
from songtrace.domain.investigation_rule import InvestigationRule
from songtrace.domain.observation import ObservationKind


def test_creates_investigation_rule() -> None:
    confidence = _confidence()

    rule = InvestigationRule(
        required_observation_kinds=(
            ObservationKind.PLAYLIST_STREAM_GROWTH,
            ObservationKind.PLAYLIST_SAVE_GROWTH,
        ),
        conclusion_statement="Playlist placement likely drove renewed engagement.",
        confidence=confidence,
    )

    assert rule.required_observation_kinds == (
        ObservationKind.PLAYLIST_STREAM_GROWTH,
        ObservationKind.PLAYLIST_SAVE_GROWTH,
    )
    assert rule.conclusion_statement == "Playlist placement likely drove renewed engagement."
    assert rule.confidence == confidence


def test_stores_required_observation_kinds_as_immutable_tuple() -> None:
    required_kinds = [ObservationKind.PLAYLIST_STREAM_GROWTH]

    rule = InvestigationRule(
        required_observation_kinds=cast(tuple[ObservationKind, ...], required_kinds),
        conclusion_statement="Playlist placement likely drove renewed engagement.",
        confidence=_confidence(),
    )
    required_kinds.append(ObservationKind.PLAYLIST_SAVE_GROWTH)

    assert rule.required_observation_kinds == (ObservationKind.PLAYLIST_STREAM_GROWTH,)


def test_rejects_empty_required_observation_kinds() -> None:
    with pytest.raises(ValueError, match="rule must require at least one observation kind"):
        InvestigationRule(
            required_observation_kinds=(),
            conclusion_statement="Playlist placement likely drove renewed engagement.",
            confidence=_confidence(),
        )


def test_rejects_duplicate_required_observation_kinds() -> None:
    with pytest.raises(ValueError, match="required_observation_kinds must not contain duplicates"):
        InvestigationRule(
            required_observation_kinds=(
                ObservationKind.PLAYLIST_STREAM_GROWTH,
                ObservationKind.PLAYLIST_STREAM_GROWTH,
            ),
            conclusion_statement="Playlist placement likely drove renewed engagement.",
            confidence=_confidence(),
        )


@pytest.mark.parametrize("conclusion_statement", ["", " ", "\n"])
def test_rejects_empty_conclusion_statement(conclusion_statement: str) -> None:
    with pytest.raises(ValueError, match="conclusion_statement must not be empty"):
        InvestigationRule(
            required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
            conclusion_statement=conclusion_statement,
            confidence=_confidence(),
        )


def test_investigation_rule_is_immutable() -> None:
    rule = InvestigationRule(
        required_observation_kinds=(ObservationKind.PLAYLIST_STREAM_GROWTH,),
        conclusion_statement="Playlist placement likely drove renewed engagement.",
        confidence=_confidence(),
    )

    with pytest.raises(FrozenInstanceError):
        rule.conclusion_statement = "Changed"  # type: ignore[misc]


def _confidence() -> Confidence:
    return Confidence(
        level=ConfidenceLevel.HIGH,
        rationale="Multiple observations support the same explanation.",
    )
