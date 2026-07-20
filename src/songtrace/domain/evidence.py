"""Domain model for evidence collected during an investigation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from songtrace.domain.evidence_source import EvidenceSource


class EvidenceKind(StrEnum):
    """Provider-neutral categories of investigation evidence."""

    AUDIENCE_ACTIVITY = "audience_activity"
    CHART_ACTIVITY = "chart_activity"
    MEDIA_COVERAGE = "media_coverage"
    PLAYLIST_ACTIVITY = "playlist_activity"
    ROYALTY_ACTIVITY = "royalty_activity"
    SOCIAL_ACTIVITY = "social_activity"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Evidence:
    """An immutable fact collected during a song investigation.

    Evidence records what happened without interpreting why it happened.
    Interpretation belongs to observations and conclusions.
    """

    source: EvidenceSource
    kind: EvidenceKind
    summary: str
    observed_at: datetime
    occurred_at: datetime | None = None
    reference: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate the domain invariants for evidence."""

        if not self.summary.strip():
            raise ValueError("Evidence summary must not be empty.")

        if self.observed_at.tzinfo is None:
            raise ValueError("Evidence observed_at must be timezone-aware.")

        if self.occurred_at is not None and self.occurred_at.tzinfo is None:
            raise ValueError("Evidence occurred_at must be timezone-aware.")

        if self.reference is not None and not self.reference.strip():
            raise ValueError("Evidence reference must not be empty when provided.")
