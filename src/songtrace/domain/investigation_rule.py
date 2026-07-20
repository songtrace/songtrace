"""Domain knowledge rules for deriving conclusions from observations."""

from __future__ import annotations

from dataclasses import dataclass

from songtrace.domain.confidence import Confidence
from songtrace.domain.observation import ObservationKind


@dataclass(frozen=True, slots=True)
class InvestigationRule:
    """Immutable rule data describing which observations support a conclusion."""

    required_observation_kinds: tuple[ObservationKind, ...]
    conclusion_statement: str
    confidence: Confidence

    def __post_init__(self) -> None:
        """Validate rule invariants."""

        object.__setattr__(
            self,
            "required_observation_kinds",
            tuple(self.required_observation_kinds),
        )

        if not self.required_observation_kinds:
            raise ValueError("rule must require at least one observation kind")

        if len(set(self.required_observation_kinds)) != len(self.required_observation_kinds):
            raise ValueError("required_observation_kinds must not contain duplicates")

        if not self.conclusion_statement.strip():
            raise ValueError("conclusion_statement must not be empty")
