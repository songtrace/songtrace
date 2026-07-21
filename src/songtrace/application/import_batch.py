"""Application models for imported evidence batches."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from songtrace.domain.evidence import Evidence


@dataclass(frozen=True, slots=True)
class ImportBatchMetadata:
    """Metadata describing one evidence import batch."""

    id: UUID
    source_name: str
    imported_at: datetime
    record_count: int

    def __post_init__(self) -> None:
        source_name = self.source_name.strip()
        if not source_name:
            msg = "source_name must not be blank"
            raise ValueError(msg)

        if self.imported_at.tzinfo is None or self.imported_at.utcoffset() is None:
            msg = "imported_at must be timezone-aware"
            raise ValueError(msg)

        if self.record_count < 0:
            msg = "record_count must not be negative"
            raise ValueError(msg)

        object.__setattr__(self, "source_name", source_name)


@dataclass(frozen=True, slots=True)
class EvidenceImportBatch:
    """Evidence imported together with deterministic batch metadata."""

    metadata: ImportBatchMetadata
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        evidence = tuple(self.evidence)
        if self.metadata.record_count != len(evidence):
            msg = "metadata record_count must match evidence count"
            raise ValueError(msg)

        object.__setattr__(self, "evidence", evidence)
