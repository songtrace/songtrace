"""Tests for importing raw evidence records into domain evidence."""

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest

from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.evidence_source import EvidenceSource as DomainEvidenceSource

_OBSERVED_AT = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
_OCCURRED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
_FALLBACK_OBSERVED_AT = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


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
