"""Tests for the Confidence value object."""

from dataclasses import FrozenInstanceError

import pytest

from songtrace.domain.confidence import Confidence, ConfidenceLevel


def test_creates_confidence() -> None:
    confidence = Confidence(
        level=ConfidenceLevel.HIGH,
        rationale="Multiple observations support the same explanation.",
    )

    assert confidence.level is ConfidenceLevel.HIGH
    assert confidence.rationale == "Multiple observations support the same explanation."


def test_confidence_is_immutable() -> None:
    confidence = Confidence(
        level=ConfidenceLevel.MEDIUM,
        rationale="The evidence is meaningful but incomplete.",
    )

    with pytest.raises(FrozenInstanceError):
        confidence.rationale = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize("rationale", ["", " ", "\n"])
def test_rejects_empty_rationale(rationale: str) -> None:
    with pytest.raises(ValueError, match="rationale must not be empty"):
        Confidence(
            level=ConfidenceLevel.LOW,
            rationale=rationale,
        )
