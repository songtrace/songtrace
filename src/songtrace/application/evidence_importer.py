"""Import raw evidence records into validated domain evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from songtrace.application.import_batch import EvidenceImportBatch, ImportBatchMetadata
from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import Evidence
from songtrace.domain.evidence_source import EvidenceSource as DomainEvidenceSource


class EvidenceImporter:
    """Construct validated Evidence from raw boundary records."""

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
        batch_id_factory: Callable[[], UUID] | None = None,
    ) -> None:
        self._clock = clock or _utc_now
        self._batch_id_factory = batch_id_factory or uuid4

    def import_records(self, records: tuple[RawEvidenceRecord, ...]) -> tuple[Evidence, ...]:
        """Import all records or raise without returning partial data."""

        fallback_observed_at = self._clock()
        evidence = tuple(_to_evidence(record, fallback_observed_at) for record in records)

        return evidence

    def import_batch(
        self,
        records: tuple[RawEvidenceRecord, ...],
        *,
        source_name: str,
    ) -> EvidenceImportBatch:
        """Import all records and return immutable batch metadata."""

        imported_at = self._clock()
        evidence = tuple(_to_evidence(record, imported_at) for record in records)
        metadata = ImportBatchMetadata(
            id=self._batch_id_factory(),
            source_name=source_name,
            imported_at=imported_at,
            record_count=len(evidence),
        )

        return EvidenceImportBatch(metadata=metadata, evidence=evidence)


def _to_evidence(record: RawEvidenceRecord, fallback_observed_at: datetime) -> Evidence:
    observed_at = record.observed_at or fallback_observed_at

    if record.id is not None:
        return Evidence(
            source=DomainEvidenceSource(record.source_name),
            kind=record.kind,
            summary=record.summary,
            observed_at=observed_at,
            occurred_at=record.occurred_at,
            reference=record.reference,
            signals=record.signals,
            id=record.id,
        )

    return Evidence(
        source=DomainEvidenceSource(record.source_name),
        kind=record.kind,
        summary=record.summary,
        observed_at=observed_at,
        occurred_at=record.occurred_at,
        reference=record.reference,
        signals=record.signals,
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)
