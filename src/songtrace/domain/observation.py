"""Domain entity representing a factual observation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ObservationKind(StrEnum):
    """Provider-neutral categories of extracted observations."""

    PLAYLIST_SAVE_GROWTH = "playlist_save_growth"
    PLAYLIST_STREAM_GROWTH = "playlist_stream_growth"


@dataclass(frozen=True, slots=True)
class Observation:
    """A factual pattern or relationship supported by evidence."""

    kind: ObservationKind
    summary: str
    supporting_evidence_ids: tuple[UUID, ...]
    observed_at: datetime
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate observation invariants."""

        if not self.summary.strip():
            raise ValueError("summary must not be empty")

        if not self.supporting_evidence_ids:
            raise ValueError("observation must reference at least one supporting evidence item")

        if len(set(self.supporting_evidence_ids)) != len(self.supporting_evidence_ids):
            raise ValueError("supporting_evidence_ids must not contain duplicates")

        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
