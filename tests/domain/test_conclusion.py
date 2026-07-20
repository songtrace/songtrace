"""Tests for the Conclusion domain entity."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from songtrace.domain.conclusion import Conclusion
from songtrace.domain.confidence import Confidence, ConfidenceLevel


def make_confidence() -> Confidence:
    return Confidence(
        level=ConfidenceLevel.HIGH,
        rationale="Multiple observations support the same explanation.",
    )


def test_creates_conclusion() -> None:
    observation_id = uuid4()
    created_at = datetime(2026, 7, 20, 20, 0, tzinfo=UTC)

    conclusion = Conclusion(
        statement="Playlist placement likely drove renewed engagement.",
        supporting_observation_ids=(observation_id,),
        confidence=make_confidence(),
        created_at=created_at,
    )

    assert isinstance(conclusion.id, UUID)
    assert conclusion.statement == "Playlist placement likely drove renewed engagement."
    assert conclusion.supporting_observation_ids == (observation_id,)
    assert conclusion.confidence == make_confidence()
    assert conclusion.created_at == created_at


def test_generates_unique_identifiers() -> None:
    observation_id = uuid4()
    created_at = datetime.now(UTC)

    first = Conclusion(
        statement="Playlist placement likely drove renewed engagement.",
        supporting_observation_ids=(observation_id,),
        confidence=make_confidence(),
        created_at=created_at,
    )
    second = Conclusion(
        statement="Playlist placement likely drove renewed engagement.",
        supporting_observation_ids=(observation_id,),
        confidence=make_confidence(),
        created_at=created_at,
    )

    assert first.id != second.id


def test_conclusion_is_immutable() -> None:
    conclusion = Conclusion(
        statement="Playlist placement likely drove renewed engagement.",
        supporting_observation_ids=(uuid4(),),
        confidence=make_confidence(),
        created_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        conclusion.statement = "Changed statement"  # type: ignore[misc]


@pytest.mark.parametrize("statement", ["", " ", "\n"])
def test_rejects_empty_statement(statement: str) -> None:
    with pytest.raises(ValueError, match="statement must not be empty"):
        Conclusion(
            statement=statement,
            supporting_observation_ids=(uuid4(),),
            confidence=make_confidence(),
            created_at=datetime.now(UTC),
        )


def test_rejects_empty_supporting_observation_ids() -> None:
    with pytest.raises(
        ValueError,
        match="conclusion must reference at least one supporting observation",
    ):
        Conclusion(
            statement="Playlist placement likely drove renewed engagement.",
            supporting_observation_ids=(),
            confidence=make_confidence(),
            created_at=datetime.now(UTC),
        )


def test_rejects_duplicate_supporting_observation_ids() -> None:
    observation_id = uuid4()

    with pytest.raises(
        ValueError,
        match="supporting_observation_ids must not contain duplicates",
    ):
        Conclusion(
            statement="Playlist placement likely drove renewed engagement.",
            supporting_observation_ids=(observation_id, observation_id),
            confidence=make_confidence(),
            created_at=datetime.now(UTC),
        )


def test_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        Conclusion(
            statement="Playlist placement likely drove renewed engagement.",
            supporting_observation_ids=(uuid4(),),
            confidence=make_confidence(),
            created_at=datetime(2026, 7, 20, 20, 0),
        )
