"""Tests for loading raw evidence records from CSV files."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application.csv_raw_evidence_source import CsvRawEvidenceSource
from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal

_COLUMNS = (
    "id",
    "source_name",
    "kind",
    "summary",
    "occurred_at",
    "observed_at",
    "reference",
    "signals",
)


def test_successfully_loads_csv_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())
    source: RawEvidenceSource = CsvRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 3
    assert records[0].id == UUID("00000000-0000-0000-0000-000000000201")
    assert records[0].source_name == "spotify"
    assert records[0].summary == "Everything Is Fading received editorial playlist placement."


def test_preserves_record_order(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())

    records = CsvRawEvidenceSource(path).load()

    assert tuple(record.id for record in records) == (
        UUID("00000000-0000-0000-0000-000000000201"),
        UUID("00000000-0000-0000-0000-000000000202"),
        UUID("00000000-0000-0000-0000-000000000203"),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())

    records = CsvRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_converts_enum_values(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())

    records = CsvRawEvidenceSource(path).load()

    assert records[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert records[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert records[1].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert records[1].signals == (EvidenceSignal.STREAM_GROWTH,)


def test_parses_multiple_semicolon_separated_signals(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    row = _row(signals="stream_growth;save_growth")
    _write_csv(path, [row])

    records = CsvRawEvidenceSource(path).load()

    assert records[0].signals == (EvidenceSignal.STREAM_GROWTH, EvidenceSignal.SAVE_GROWTH)


def test_parses_timezone_aware_occurred_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())

    records = CsvRawEvidenceSource(path).load()

    assert records[0].occurred_at == datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def test_observed_at_is_absent_when_csv_field_is_blank(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(observed_at="")])

    records = CsvRawEvidenceSource(path).load()

    assert records[0].observed_at is None


def test_parses_optional_timezone_aware_observed_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(observed_at="2026-07-20T12:00:00+00:00")])

    records = CsvRawEvidenceSource(path).load()

    assert records[0].observed_at == datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="Evidence CSV file not found"):
        CsvRawEvidenceSource(path).load()


def test_missing_header_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="must include a header row"):
        CsvRawEvidenceSource(path).load()


def test_missing_required_column_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=[column for column in _COLUMNS if column != "summary"]
        )
        writer.writeheader()

    with pytest.raises(ValueError, match="missing required field"):
        CsvRawEvidenceSource(path).load()


def test_missing_required_row_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(summary="")])

    with pytest.raises(ValueError, match="missing field 'summary'"):
        CsvRawEvidenceSource(path).load()


def test_too_many_columns_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    path.write_text(
        ",".join(_COLUMNS) + "\n" + ",".join(_row().values()) + ",extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too many columns"):
        CsvRawEvidenceSource(path).load()


def test_invalid_evidence_kind_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(kind="not_a_kind")])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        CsvRawEvidenceSource(path).load()


def test_invalid_evidence_signal_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(signals="not_a_signal")])

    with pytest.raises(ValueError, match="invalid EvidenceSignal"):
        CsvRawEvidenceSource(path).load()


def test_invalid_datetime_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(occurred_at="not-a-datetime")])

    with pytest.raises(ValueError, match="must be an ISO datetime"):
        CsvRawEvidenceSource(path).load()


def test_naive_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(occurred_at="2026-07-18T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        CsvRawEvidenceSource(path).load()


def test_naive_observed_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, [_row(observed_at="2026-07-20T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        CsvRawEvidenceSource(path).load()


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    invalid_row = _row(
        id="00000000-0000-0000-0000-000000000299",
        kind="not_a_kind",
    )
    _write_csv(path, [_row(), invalid_row])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        CsvRawEvidenceSource(path).load()


def test_loaded_records_are_compatible_with_evidence_importer(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _rows())

    records = CsvRawEvidenceSource(path).load()
    fallback_observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    evidence = EvidenceImporter(clock=lambda: fallback_observed_at).import_records(records)

    assert tuple(item.id for item in evidence) == tuple(record.id for record in records)
    assert tuple(item.summary for item in evidence) == tuple(record.summary for record in records)
    assert tuple(item.occurred_at for item in evidence) == tuple(
        record.occurred_at for record in records
    )
    assert all(item.observed_at == fallback_observed_at for item in evidence)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(_COLUMNS)
        writer.writerows([row[column] for column in _COLUMNS] for row in rows)


def _rows() -> list[dict[str, str]]:
    return [
        _row(
            id="00000000-0000-0000-0000-000000000201",
            kind="playlist_activity",
            summary="Everything Is Fading received editorial playlist placement.",
            reference="spotify-playlist:dark-metal-editorial",
            signals="playlist_placement",
        ),
        _row(
            id="00000000-0000-0000-0000-000000000202",
            kind="audience_activity",
            summary="Streams increased 48% after the playlist placement.",
            reference="spotify-analytics:streams-week-2026-07-18",
            signals="stream_growth",
        ),
        _row(
            id="00000000-0000-0000-0000-000000000203",
            kind="audience_activity",
            summary="Save activity increased 31% after the playlist placement.",
            reference="spotify-analytics:saves-week-2026-07-18",
            signals="save_growth",
        ),
    ]


def _row(
    *,
    id: str = "00000000-0000-0000-0000-000000000201",
    source_name: str = "spotify",
    kind: str = "playlist_activity",
    summary: str = "Everything Is Fading received editorial playlist placement.",
    occurred_at: str = "2026-07-18T12:00:00+00:00",
    observed_at: str = "",
    reference: str = "spotify-playlist:dark-metal-editorial",
    signals: str = "playlist_placement",
) -> dict[str, str]:
    return {
        "id": id,
        "source_name": source_name,
        "kind": kind,
        "summary": summary,
        "occurred_at": occurred_at,
        "observed_at": observed_at,
        "reference": reference,
        "signals": signals,
    }
