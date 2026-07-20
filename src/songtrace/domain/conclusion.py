"""Domain entity representing an inferred conclusion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from songtrace.domain.confidence import Confidence


@dataclass(frozen=True, slots=True)
class Conclusion:
    """An inference supported by one or more observations."""

    statement: str
    supporting_observation_ids: tuple[UUID, ...]
    confidence: Confidence
    created_at: datetime
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement must not be empty")

        if not self.supporting_observation_ids:
            raise ValueError("conclusion must reference at least one supporting observation")

        if len(set(self.supporting_observation_ids)) != len(self.supporting_observation_ids):
            raise ValueError("supporting_observation_ids must not contain duplicates")

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
