"""Import raw evidence records into validated domain evidence."""

from __future__ import annotations

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import Evidence
from songtrace.domain.evidence_source import EvidenceSource as DomainEvidenceSource


class EvidenceImporter:
    """Construct validated Evidence from raw boundary records."""

    def import_records(self, records: tuple[RawEvidenceRecord, ...]) -> tuple[Evidence, ...]:
        """Import all records or raise without returning partial data."""

        evidence = tuple(_to_evidence(record) for record in records)

        return evidence


def _to_evidence(record: RawEvidenceRecord) -> Evidence:
    return Evidence(
        source=DomainEvidenceSource(record.source_name),
        kind=record.kind,
        summary=record.summary,
        observed_at=record.observed_at,
        occurred_at=record.occurred_at,
        reference=record.reference,
        signals=record.signals,
    )
