"""Transport object for raw evidence before domain validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from songtrace.domain.evidence import EvidenceKind, EvidenceSignal


@dataclass(frozen=True, slots=True)
class RawEvidenceRecord:
    """Raw evidence data loaded at the application boundary."""

    source_name: str
    kind: EvidenceKind
    summary: str
    observed_at: datetime
    occurred_at: datetime | None = None
    reference: str | None = None
    signals: tuple[EvidenceSignal, ...] = ()

    def __post_init__(self) -> None:
        """Ensure collection fields remain immutable at the boundary."""

        object.__setattr__(self, "signals", tuple(self.signals))
