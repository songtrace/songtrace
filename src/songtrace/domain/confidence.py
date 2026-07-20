"""Confidence assigned to a domain conclusion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConfidenceLevel(StrEnum):
    """Relative strength of a conclusion."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class Confidence:
    """Confidence level with an explanation for the assessment."""

    level: ConfidenceLevel
    rationale: str

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("rationale must not be empty")
