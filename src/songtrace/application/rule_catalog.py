"""Catalog of deterministic investigation rules."""

from __future__ import annotations

from dataclasses import dataclass, field

from songtrace.domain.confidence import Confidence, ConfidenceLevel
from songtrace.domain.investigation_rule import InvestigationRule
from songtrace.domain.observation import ObservationKind


@dataclass(frozen=True, slots=True)
class RuleCatalog:
    """Supplies immutable investigation rules to application services."""

    rules: tuple[InvestigationRule, ...] = field(
        default_factory=lambda: (_playlist_engagement_rule(),)
    )

    def __post_init__(self) -> None:
        """Ensure rules are exposed as an immutable tuple."""

        object.__setattr__(self, "rules", tuple(self.rules))


def _playlist_engagement_rule() -> InvestigationRule:
    return InvestigationRule(
        required_observation_kinds=(
            ObservationKind.PLAYLIST_STREAM_GROWTH,
            ObservationKind.PLAYLIST_SAVE_GROWTH,
        ),
        conclusion_statement=(
            "Editorial playlist placement likely drove renewed listener engagement."
        ),
        confidence=Confidence(
            level=ConfidenceLevel.HIGH,
            rationale="Stream and save activity both increased after the playlist placement.",
        ),
    )
