"""Application boundary for loading raw evidence records."""

from __future__ import annotations

from typing import Protocol

from songtrace.application.raw_evidence_record import RawEvidenceRecord


class RawEvidenceSource(Protocol):
    """Loads raw evidence records from an application boundary."""

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load raw evidence records in deterministic order."""
        ...
