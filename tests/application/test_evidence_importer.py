"""Tests for importing raw evidence records into domain evidence."""

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest

from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.import_batch import EvidenceImportBatch, ImportBatchMetadata
from songtrace.application.import_validation import EvidenceImportError, ImportValidationReport
from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import Evidence, EvidenceKind, EvidenceSignal
from songtrace.domain.evidence_source import EvidenceSource as DomainEvidenceSource

_OBSERVED_AT = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
_OCCURRED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
_FALLBACK_OBSERVED_AT = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
_BATCH_ID = UUID("00000000-0000-0000-0000-000000000901")
_DUPLICATE_EVIDENCE_ID = UUID("00000000-0000-0000-0000-000000000902")


def test_successfully_imports_raw_evidence_records() -> None:
    records = (_playlist_record(), _stream_record())

    evidence = EvidenceImporter().import_records(records)

    assert len(evidence) == 2
    assert all(isinstance(item.id, UUID) for item in evidence)


def test_preserves_deterministic_ordering() -> None:
    records = (_playlist_record(), _stream_record(), _save_record())

    evidence = EvidenceImporter().import_records(records)

    assert tuple(item.summary for item in evidence) == tuple(record.summary for record in records)


def test_invalid_records_fail_import() -> None:
    records = (
        _playlist_record(),
        RawEvidenceRecord(
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime(2026, 7, 18, 12, 0),
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        EvidenceImporter(clock=lambda: datetime(2026, 7, 18, 12, 0)).import_records(records)


def test_importer_produces_expected_evidence_objects() -> None:
    record = RawEvidenceRecord(
        source_name=" Spotify Analytics ",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        observed_at=_OBSERVED_AT,
        occurred_at=_OCCURRED_AT,
        reference="spotify-analytics:streams-week-2026-07-18",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    evidence = EvidenceImporter().import_records((record,))[0]

    assert evidence.source == DomainEvidenceSource("spotify_analytics")
    assert evidence.kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert evidence.summary == record.summary
    assert evidence.observed_at == _OBSERVED_AT
    assert evidence.occurred_at == _OCCURRED_AT
    assert evidence.reference == "spotify-analytics:streams-week-2026-07-18"
    assert evidence.signals == (EvidenceSignal.STREAM_GROWTH,)


def test_importer_uses_fallback_clock_when_observed_at_is_absent() -> None:
    record = RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        occurred_at=_OCCURRED_AT,
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    evidence = EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records((record,))[0]

    assert evidence.observed_at == _FALLBACK_OBSERVED_AT


def test_importer_preserves_supplied_observed_at() -> None:
    record = RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        observed_at=_OBSERVED_AT,
        occurred_at=_OCCURRED_AT,
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    evidence = EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records((record,))[0]

    assert evidence.observed_at == _OBSERVED_AT


def test_importer_uses_one_deterministic_fallback_timestamp_per_batch() -> None:
    fallback_times = iter(
        (
            datetime(2026, 7, 20, 1, 0, tzinfo=UTC),
            datetime(2026, 7, 20, 2, 0, tzinfo=UTC),
        )
    )
    records = (
        RawEvidenceRecord(
            source_name="spotify",
            kind=EvidenceKind.PLAYLIST_ACTIVITY,
            summary="Everything Is Fading received editorial playlist placement.",
            occurred_at=_OCCURRED_AT,
            signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        ),
        RawEvidenceRecord(
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased 48% after the playlist placement.",
            occurred_at=_OCCURRED_AT,
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    evidence = EvidenceImporter(clock=lambda: next(fallback_times)).import_records(records)

    assert tuple(item.observed_at for item in evidence) == (
        datetime(2026, 7, 20, 1, 0, tzinfo=UTC),
        datetime(2026, 7, 20, 1, 0, tzinfo=UTC),
    )


def test_importer_preserves_occurred_at_when_observed_at_falls_back() -> None:
    record = RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        occurred_at=_OCCURRED_AT,
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    evidence = EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records((record,))[0]

    assert evidence.observed_at == _FALLBACK_OBSERVED_AT
    assert evidence.occurred_at == _OCCURRED_AT


def test_source_returns_immutable_tuple() -> None:
    source: RawEvidenceSource = StaticRawEvidenceSource(
        records=(_playlist_record(), _stream_record())
    )

    records = source.load()

    assert isinstance(records, tuple)
    assert records == (_playlist_record(), _stream_record())


def test_raw_evidence_record_is_immutable() -> None:
    record = _playlist_record()

    with pytest.raises(FrozenInstanceError):
        record.summary = "Changed"  # type: ignore[misc]


def test_raw_evidence_record_stores_signals_as_immutable_tuple() -> None:
    signals = [EvidenceSignal.STREAM_GROWTH]

    record = RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased.",
        signals=cast(tuple[EvidenceSignal, ...], signals),
    )
    signals.append(EvidenceSignal.SAVE_GROWTH)

    assert record.signals == (EvidenceSignal.STREAM_GROWTH,)


def test_import_batch_returns_evidence_with_metadata() -> None:
    records = (_playlist_record(), _stream_record())

    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch(records, source_name="spotify")

    assert isinstance(batch, EvidenceImportBatch)
    assert batch.metadata == ImportBatchMetadata(
        id=_BATCH_ID,
        source_name="spotify",
        imported_at=_FALLBACK_OBSERVED_AT,
        record_count=2,
    )
    assert tuple(item.summary for item in batch.evidence) == tuple(
        record.summary for record in records
    )
    assert batch.validation_report == ImportValidationReport(accepted_record_count=2)


def test_import_batch_metadata_timestamp_is_deterministic() -> None:
    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch((_playlist_record(),), source_name="spotify")

    assert batch.metadata.imported_at == _FALLBACK_OBSERVED_AT


def test_import_batch_uses_imported_at_as_fallback_observed_at() -> None:
    record = RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        occurred_at=_OCCURRED_AT,
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )

    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch((record,), source_name="spotify")

    assert batch.evidence[0].observed_at == _FALLBACK_OBSERVED_AT
    assert batch.metadata.imported_at == _FALLBACK_OBSERVED_AT


def test_import_batch_preserves_supplied_observed_at() -> None:
    record = _stream_record()

    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch((record,), source_name="spotify")

    assert batch.evidence[0].observed_at == _OBSERVED_AT


def test_import_batch_record_count_supports_empty_imports() -> None:
    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch((), source_name="spotify")

    assert batch.evidence == ()
    assert batch.metadata.record_count == 0
    assert batch.validation_report == ImportValidationReport(accepted_record_count=0)


def test_import_batch_metadata_is_immutable() -> None:
    metadata = ImportBatchMetadata(
        id=_BATCH_ID,
        source_name="spotify",
        imported_at=_FALLBACK_OBSERVED_AT,
        record_count=1,
    )

    with pytest.raises(FrozenInstanceError):
        metadata.record_count = 2  # type: ignore[misc]


def test_import_batch_result_is_immutable() -> None:
    batch = EvidenceImporter(
        clock=lambda: _FALLBACK_OBSERVED_AT,
        batch_id_factory=lambda: _BATCH_ID,
    ).import_batch((_playlist_record(),), source_name="spotify")

    with pytest.raises(FrozenInstanceError):
        batch.evidence = ()  # type: ignore[misc]


def test_import_validation_report_is_immutable() -> None:
    report = ImportValidationReport(accepted_record_count=1)

    with pytest.raises(FrozenInstanceError):
        report.accepted_record_count = 2  # type: ignore[misc]


def test_import_validation_report_rejects_negative_accepted_record_count() -> None:
    with pytest.raises(ValueError, match="accepted_record_count must not be negative"):
        ImportValidationReport(accepted_record_count=-1)


def test_import_validation_report_rejects_negative_rejected_record_index() -> None:
    with pytest.raises(ValueError, match="rejected_record_index must not be negative"):
        ImportValidationReport(
            accepted_record_count=0,
            rejected_record_index=-1,
            error_message="invalid",
        )


def test_import_validation_report_rejects_incomplete_failure_context() -> None:
    with pytest.raises(
        ValueError,
        match="rejected_record_index and error_message must both be set or both be absent",
    ):
        ImportValidationReport(accepted_record_count=0, rejected_record_index=1)


def test_import_batch_rejects_blank_source_name() -> None:
    with pytest.raises(ValueError, match="source_name must not be blank"):
        EvidenceImporter(
            clock=lambda: _FALLBACK_OBSERVED_AT,
            batch_id_factory=lambda: _BATCH_ID,
        ).import_batch((_playlist_record(),), source_name="  ")


def test_import_batch_rejects_naive_imported_at() -> None:
    with pytest.raises(ValueError, match="imported_at must be timezone-aware"):
        EvidenceImporter(
            clock=lambda: datetime(2026, 7, 20, 12, 0),
            batch_id_factory=lambda: _BATCH_ID,
        ).import_batch((_playlist_record(),), source_name="spotify")


def test_import_batch_metadata_rejects_negative_record_count() -> None:
    with pytest.raises(ValueError, match="record_count must not be negative"):
        ImportBatchMetadata(
            id=_BATCH_ID,
            source_name="spotify",
            imported_at=_FALLBACK_OBSERVED_AT,
            record_count=-1,
        )


def test_import_batch_result_rejects_mismatched_record_count() -> None:
    evidence = EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records(
        (_playlist_record(),)
    )
    metadata = ImportBatchMetadata(
        id=_BATCH_ID,
        source_name="spotify",
        imported_at=_FALLBACK_OBSERVED_AT,
        record_count=2,
    )

    with pytest.raises(ValueError, match="metadata record_count must match evidence count"):
        EvidenceImportBatch(metadata=metadata, evidence=evidence)


def test_import_batch_result_stores_evidence_as_immutable_tuple() -> None:
    evidence = list(
        EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records((_playlist_record(),))
    )
    metadata = ImportBatchMetadata(
        id=_BATCH_ID,
        source_name="spotify",
        imported_at=_FALLBACK_OBSERVED_AT,
        record_count=1,
    )

    batch = EvidenceImportBatch(
        metadata=metadata,
        evidence=cast(tuple[Evidence, ...], evidence),
    )
    evidence.clear()

    assert len(batch.evidence) == 1


def test_import_batch_does_not_return_partial_data_when_record_is_invalid() -> None:
    records = (
        _playlist_record(),
        RawEvidenceRecord(
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime(2026, 7, 18, 12, 0),
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    with pytest.raises(EvidenceImportError, match="observed_at must be timezone-aware") as exc_info:
        EvidenceImporter(
            clock=lambda: _FALLBACK_OBSERVED_AT,
            batch_id_factory=lambda: _BATCH_ID,
        ).import_batch(records, source_name="spotify")

    report = exc_info.value.report
    assert report.accepted_record_count == 1
    assert report.rejected_record_index == 1
    assert report.rejected_source_name == "spotify"
    assert report.rejected_summary == "Streams increased."
    assert report.rejected_reference is None
    assert report.error_message == "Evidence observed_at must be timezone-aware."
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_import_records_rejects_duplicate_explicit_evidence_ids() -> None:
    records = (
        RawEvidenceRecord(
            id=_DUPLICATE_EVIDENCE_ID,
            source_name="spotify",
            kind=EvidenceKind.PLAYLIST_ACTIVITY,
            summary="Everything Is Fading received editorial playlist placement.",
            observed_at=_OBSERVED_AT,
            reference="spotify-playlist:dark-metal-editorial",
            signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        ),
        RawEvidenceRecord(
            id=_DUPLICATE_EVIDENCE_ID,
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=_OBSERVED_AT,
            reference="spotify-analytics:streams-week-2026-07-18",
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    with pytest.raises(EvidenceImportError, match="duplicate evidence id") as exc_info:
        EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records(records)

    report = exc_info.value.report
    assert report.accepted_record_count == 1
    assert report.rejected_record_index == 1
    assert report.rejected_record_id == _DUPLICATE_EVIDENCE_ID
    assert report.rejected_source_name == "spotify"
    assert report.rejected_reference == "spotify-analytics:streams-week-2026-07-18"
    assert report.rejected_summary == "Streams increased."
    assert report.error_message == f"duplicate evidence id: {_DUPLICATE_EVIDENCE_ID}"


def test_import_batch_rejects_duplicate_explicit_evidence_ids() -> None:
    records = (
        RawEvidenceRecord(
            id=_DUPLICATE_EVIDENCE_ID,
            source_name="spotify",
            kind=EvidenceKind.PLAYLIST_ACTIVITY,
            summary="Everything Is Fading received editorial playlist placement.",
            observed_at=_OBSERVED_AT,
            signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        ),
        RawEvidenceRecord(
            id=_DUPLICATE_EVIDENCE_ID,
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=_OBSERVED_AT,
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    with pytest.raises(EvidenceImportError, match="duplicate evidence id") as exc_info:
        EvidenceImporter(
            clock=lambda: _FALLBACK_OBSERVED_AT,
            batch_id_factory=lambda: _BATCH_ID,
        ).import_batch(records, source_name="spotify")

    report = exc_info.value.report
    assert report.accepted_record_count == 1
    assert report.rejected_record_index == 1
    assert report.rejected_record_id == _DUPLICATE_EVIDENCE_ID


def test_importer_allows_multiple_generated_evidence_ids() -> None:
    evidence = EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records(
        (_playlist_record(), _stream_record())
    )

    assert len({item.id for item in evidence}) == 2


def test_import_records_failure_includes_validation_context() -> None:
    records = (
        _playlist_record(),
        RawEvidenceRecord(
            source_name="spotify",
            kind=EvidenceKind.AUDIENCE_ACTIVITY,
            summary="Streams increased.",
            observed_at=datetime(2026, 7, 18, 12, 0),
            reference="spotify-analytics:streams-week-2026-07-18",
            signals=(EvidenceSignal.STREAM_GROWTH,),
        ),
    )

    with pytest.raises(EvidenceImportError, match="Import failed for record 1") as exc_info:
        EvidenceImporter(clock=lambda: _FALLBACK_OBSERVED_AT).import_records(records)

    report = exc_info.value.report
    assert report.accepted_record_count == 1
    assert report.rejected_record_index == 1
    assert report.rejected_record_id is None
    assert report.rejected_reference == "spotify-analytics:streams-week-2026-07-18"
    assert report.error_message == "Evidence observed_at must be timezone-aware."


@dataclass(frozen=True, slots=True)
class StaticRawEvidenceSource:
    records: tuple[RawEvidenceRecord, ...]

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        return tuple(self.records)


def _playlist_record() -> RawEvidenceRecord:
    return RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="Everything Is Fading received editorial playlist placement.",
        observed_at=_OBSERVED_AT,
        occurred_at=_OCCURRED_AT,
        reference="spotify-playlist:dark-metal-editorial",
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
    )


def _stream_record() -> RawEvidenceRecord:
    return RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% after the playlist placement.",
        observed_at=_OBSERVED_AT,
        occurred_at=_OCCURRED_AT,
        reference="spotify-analytics:streams-week-2026-07-18",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )


def _save_record() -> RawEvidenceRecord:
    return RawEvidenceRecord(
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Save activity increased 31% after the playlist placement.",
        observed_at=_OBSERVED_AT,
        occurred_at=_OCCURRED_AT,
        reference="spotify-analytics:saves-week-2026-07-18",
        signals=(EvidenceSignal.SAVE_GROWTH,),
    )
