"""Application models for evidence import validation reporting."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ImportValidationReport:
    """Provider-neutral validation report for one evidence import attempt."""

    accepted_record_count: int
    rejected_record_index: int | None = None
    rejected_source_name: str | None = None
    rejected_reference: str | None = None
    rejected_summary: str | None = None
    rejected_record_id: UUID | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.accepted_record_count < 0:
            msg = "accepted_record_count must not be negative"
            raise ValueError(msg)

        if self.rejected_record_index is not None and self.rejected_record_index < 0:
            msg = "rejected_record_index must not be negative"
            raise ValueError(msg)

        has_rejection_context = self.rejected_record_index is not None
        has_error = self.error_message is not None
        if has_rejection_context != has_error:
            msg = "rejected_record_index and error_message must both be set or both be absent"
            raise ValueError(msg)

    @property
    def is_successful(self) -> bool:
        """Return whether the import attempt completed without rejection."""

        return self.rejected_record_index is None


class EvidenceImportError(ValueError):
    """Raised when raw evidence import fails with validation context."""

    def __init__(self, report: ImportValidationReport) -> None:
        if report.is_successful:
            msg = "import validation report must describe a rejected record"
            raise ValueError(msg)

        rejected_record = report.rejected_record_index
        error_message = report.error_message or "unknown validation error"
        super().__init__(f"Import failed for record {rejected_record}: {error_message}")
        self.report = report
