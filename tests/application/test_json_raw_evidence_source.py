"""Tests for loading raw evidence records from JSON files."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.json_raw_evidence_source import JsonRawEvidenceSource
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal


def test_successfully_loads_json_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())
    source: RawEvidenceSource = JsonRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 3
    assert records[0].id == UUID("00000000-0000-0000-0000-000000000101")
    assert records[0].source_name == "spotify"
    assert records[0].summary == "Everything Is Fading received editorial playlist placement."


def test_preserves_record_order(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())

    records = JsonRawEvidenceSource(path).load()

    assert tuple(record.id for record in records) == (
        UUID("00000000-0000-0000-0000-000000000101"),
        UUID("00000000-0000-0000-0000-000000000102"),
        UUID("00000000-0000-0000-0000-000000000103"),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())

    records = JsonRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_converts_enum_values(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())

    records = JsonRawEvidenceSource(path).load()

    assert records[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert records[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert records[1].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert records[1].signals == (EvidenceSignal.STREAM_GROWTH,)


def test_parses_timezone_aware_occurred_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())

    records = JsonRawEvidenceSource(path).load()

    assert records[0].occurred_at == datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def test_observed_at_is_absent_when_json_field_is_absent(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, [_record()])

    records = JsonRawEvidenceSource(path).load()

    assert records[0].observed_at is None


def test_parses_optional_timezone_aware_observed_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    observed_at = "2026-07-20T12:00:00+00:00"
    _write_json(path, [_record(observed_at=observed_at)])

    records = JsonRawEvidenceSource(path).load()

    assert records[0].observed_at == datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Evidence JSON file not found"):
        JsonRawEvidenceSource(path).load()


def test_invalid_json_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="Evidence JSON is invalid"):
        JsonRawEvidenceSource(path).load()


def test_non_array_top_level_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, {"records": _records()})

    with pytest.raises(ValueError, match="top-level value must be an array"):
        JsonRawEvidenceSource(path).load()


def test_non_object_array_item_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, [_record(), "not-an-object"])

    with pytest.raises(ValueError, match="item at index 1 must be an object"):
        JsonRawEvidenceSource(path).load()


def test_missing_required_field_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record()
    del record["summary"]
    _write_json(path, [record])

    with pytest.raises(ValueError, match="missing field 'summary'"):
        JsonRawEvidenceSource(path).load()


def test_invalid_evidence_kind_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record(kind="not_a_kind")
    _write_json(path, [record])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        JsonRawEvidenceSource(path).load()


def test_invalid_evidence_signal_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record(signals=["not_a_signal"])
    _write_json(path, [record])

    with pytest.raises(ValueError, match="invalid EvidenceSignal"):
        JsonRawEvidenceSource(path).load()


def test_invalid_datetime_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record(occurred_at="not-a-datetime")
    _write_json(path, [record])

    with pytest.raises(ValueError, match="must be an ISO datetime"):
        JsonRawEvidenceSource(path).load()


def test_naive_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record(occurred_at="2026-07-18T12:00:00")
    _write_json(path, [record])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        JsonRawEvidenceSource(path).load()


def test_naive_observed_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    record = _record(observed_at="2026-07-20T12:00:00")
    _write_json(path, [record])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        JsonRawEvidenceSource(path).load()


def test_no_partial_result_when_later_record_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    invalid_record = _record(
        id="00000000-0000-0000-0000-000000000199",
        kind="not_a_kind",
    )
    _write_json(path, [_record(), invalid_record])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        JsonRawEvidenceSource(path).load()


def test_loaded_records_are_compatible_with_evidence_importer(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _records())

    records = JsonRawEvidenceSource(path).load()
    fallback_observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    evidence = EvidenceImporter(clock=lambda: fallback_observed_at).import_records(records)

    assert tuple(item.id for item in evidence) == tuple(record.id for record in records)
    assert tuple(item.summary for item in evidence) == tuple(record.summary for record in records)
    assert tuple(item.occurred_at for item in evidence) == tuple(
        record.occurred_at for record in records
    )
    assert all(item.observed_at == fallback_observed_at for item in evidence)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _records() -> list[dict[str, object]]:
    return [
        _record(
            id="00000000-0000-0000-0000-000000000101",
            kind="playlist_activity",
            summary="Everything Is Fading received editorial playlist placement.",
            reference="spotify-playlist:dark-metal-editorial",
            signals=["playlist_placement"],
        ),
        _record(
            id="00000000-0000-0000-0000-000000000102",
            kind="audience_activity",
            summary="Streams increased 48% after the playlist placement.",
            reference="spotify-analytics:streams-week-2026-07-18",
            signals=["stream_growth"],
        ),
        _record(
            id="00000000-0000-0000-0000-000000000103",
            kind="audience_activity",
            summary="Save activity increased 31% after the playlist placement.",
            reference="spotify-analytics:saves-week-2026-07-18",
            signals=["save_growth"],
        ),
    ]


def _record(
    *,
    id: str = "00000000-0000-0000-0000-000000000101",
    source_name: str = "spotify",
    kind: str = "playlist_activity",
    summary: str = "Everything Is Fading received editorial playlist placement.",
    occurred_at: str = "2026-07-18T12:00:00+00:00",
    observed_at: str | None = None,
    reference: str = "spotify-playlist:dark-metal-editorial",
    signals: list[str] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": id,
        "source_name": source_name,
        "kind": kind,
        "summary": summary,
        "occurred_at": occurred_at,
        "reference": reference,
        "signals": signals or ["playlist_placement"],
    }

    if observed_at is not None:
        record["observed_at"] = observed_at

    return record
