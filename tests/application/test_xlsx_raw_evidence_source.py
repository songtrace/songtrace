"""Tests for loading raw evidence records from XLSX files."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

import pytest

from songtrace.application.evidence_importer import EvidenceImporter
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.application.xlsx_raw_evidence_source import XlsxRawEvidenceSource
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


def test_successfully_loads_xlsx_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())
    source: RawEvidenceSource = XlsxRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 3
    assert records[0].id == UUID("00000000-0000-0000-0000-000000000201")
    assert records[0].source_name == "spotify"
    assert records[0].summary == "Everything Is Fading received editorial playlist placement."


def test_preserves_record_order(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())

    records = XlsxRawEvidenceSource(path).load()

    assert tuple(record.id for record in records) == (
        UUID("00000000-0000-0000-0000-000000000201"),
        UUID("00000000-0000-0000-0000-000000000202"),
        UUID("00000000-0000-0000-0000-000000000203"),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())

    records = XlsxRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_converts_enum_values(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert records[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert records[1].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert records[1].signals == (EvidenceSignal.STREAM_GROWTH,)


def test_parses_multiple_semicolon_separated_signals(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    row = _row(signals="stream_growth;save_growth")
    _write_xlsx(path, [row])

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].signals == (EvidenceSignal.STREAM_GROWTH, EvidenceSignal.SAVE_GROWTH)


def test_blank_signals_cell_loads_empty_signal_tuple(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    row = _row(kind="royalty_activity", signals="")
    _write_xlsx(path, [row])

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].kind is EvidenceKind.ROYALTY_ACTIVITY
    assert records[0].signals == ()


def test_parses_timezone_aware_occurred_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].occurred_at == datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def test_observed_at_is_absent_when_xlsx_cell_is_blank(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(observed_at="")])

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].observed_at is None


def test_parses_optional_timezone_aware_observed_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(observed_at="2026-07-20T12:00:00+00:00")])

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].observed_at == datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError, match="Evidence XLSX file not found"):
        XlsxRawEvidenceSource(path).load()


def test_invalid_xlsx_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    path.write_text("not a zip workbook", encoding="utf-8")

    with pytest.raises(ValueError, match="Evidence XLSX file is invalid"):
        XlsxRawEvidenceSource(path).load()


def test_missing_header_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx_rows(path, [])

    with pytest.raises(ValueError, match="must include a header row"):
        XlsxRawEvidenceSource(path).load()


def test_missing_required_column_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    columns = tuple(column for column in _COLUMNS if column != "summary")
    _write_xlsx_rows(path, [columns])

    with pytest.raises(ValueError, match="missing required field"):
        XlsxRawEvidenceSource(path).load()


def test_missing_required_row_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(summary="")])

    with pytest.raises(ValueError, match="missing field 'summary'"):
        XlsxRawEvidenceSource(path).load()


def test_too_many_cells_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx_rows(path, [_COLUMNS, (*tuple(_row().values()), "extra")])

    with pytest.raises(ValueError, match="too many cells"):
        XlsxRawEvidenceSource(path).load()


def test_invalid_evidence_kind_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(kind="not_a_kind")])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        XlsxRawEvidenceSource(path).load()


def test_invalid_evidence_signal_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(signals="not_a_signal")])

    with pytest.raises(ValueError, match="invalid EvidenceSignal"):
        XlsxRawEvidenceSource(path).load()


def test_invalid_datetime_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(occurred_at="not-a-datetime")])

    with pytest.raises(ValueError, match="must be an ISO datetime"):
        XlsxRawEvidenceSource(path).load()


def test_naive_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(occurred_at="2026-07-18T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        XlsxRawEvidenceSource(path).load()


def test_naive_observed_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, [_row(observed_at="2026-07-20T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        XlsxRawEvidenceSource(path).load()


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    invalid_row = _row(
        id="00000000-0000-0000-0000-000000000299",
        kind="not_a_kind",
    )
    _write_xlsx(path, [_row(), invalid_row])

    with pytest.raises(ValueError, match="invalid EvidenceKind"):
        XlsxRawEvidenceSource(path).load()


def test_loaded_records_are_compatible_with_evidence_importer(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _rows())

    records = XlsxRawEvidenceSource(path).load()
    fallback_observed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    evidence = EvidenceImporter(clock=lambda: fallback_observed_at).import_records(records)

    assert tuple(item.id for item in evidence) == tuple(record.id for record in records)
    assert tuple(item.summary for item in evidence) == tuple(record.summary for record in records)
    assert tuple(item.occurred_at for item in evidence) == tuple(
        record.occurred_at for record in records
    )
    assert all(item.observed_at == fallback_observed_at for item in evidence)


def test_loads_shared_string_cells(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx_rows(path, [_COLUMNS, tuple(_row().values())], use_shared_strings=True)

    records = XlsxRawEvidenceSource(path).load()

    assert records[0].summary == "Everything Is Fading received editorial playlist placement."


def _write_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    _write_xlsx_rows(path, [_COLUMNS, *(tuple(row[column] for column in _COLUMNS) for row in rows)])


def _write_xlsx_rows(
    path: Path,
    rows: list[tuple[str, ...]],
    *,
    use_shared_strings: bool = False,
) -> None:
    shared_strings: list[str] = []
    sheet_rows: list[str] = []

    for row_index, row in enumerate(rows, start=1):
        cells = "".join(
            _shared_string_cell(row_index, column_index, value, shared_strings)
            if use_shared_strings
            else _inline_string_cell(row_index, column_index, value)
            for column_index, value in enumerate(row, start=1)
        )
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        "</worksheet>"
    )

    with ZipFile(path, "w") as workbook:
        workbook.writestr("[Content_Types].xml", "")
        workbook.writestr("_rels/.rels", "")
        workbook.writestr("xl/workbook.xml", "")
        workbook.writestr("xl/_rels/workbook.xml.rels", "")
        workbook.writestr("xl/worksheets/sheet1.xml", worksheet)
        if use_shared_strings:
            workbook.writestr("xl/sharedStrings.xml", _shared_strings_xml(shared_strings))


def _inline_string_cell(row_index: int, column_index: int, value: str) -> str:
    reference = f"{_column_name(column_index)}{row_index}"
    return f'<c r="{reference}" t="inlineStr"><is><t>{_escape_xml(value)}</t></is></c>'


def _shared_string_cell(
    row_index: int,
    column_index: int,
    value: str,
    shared_strings: list[str],
) -> str:
    reference = f"{_column_name(column_index)}{row_index}"
    shared_strings.append(value)
    shared_string_index = len(shared_strings) - 1
    return f'<c r="{reference}" t="s"><v>{shared_string_index}</v></c>'


def _shared_strings_xml(shared_strings: list[str]) -> str:
    items = "".join(f"<si><t>{_escape_xml(value)}</t></si>" for value in shared_strings)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"{items}"
        "</sst>"
    )


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


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
