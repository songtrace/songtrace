from __future__ import annotations

import csv
import json
from pathlib import Path
from zipfile import ZipFile

from typer.testing import CliRunner

from songtrace.presentation.cli.main import app

runner = CliRunner()

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
_PLAYLIST_PLACEMENT_COLUMNS = (
    "id",
    "source_name",
    "summary",
    "occurred_at",
    "observed_at",
    "reference",
)
_PLATFORM_ACTIVITY_COLUMNS = (
    "id",
    "source_name",
    "summary",
    "occurred_at",
    "observed_at",
    "reference",
    "signal",
)
_ASCAP_LAYOUT_A_COLUMNS = (
    "DistributionYear",
    "Distribution Quarter",
    "Statement Recipient ID",
    "Statement Recipient Name",
    "Party ID",
    "Party Name",
    "Performance Source/Broadcast Medium",
    "Music User Genre",
    "Music User",
    "Work ID",
    "Work Title",
    "Number of Plays",
    "Performance Type (Usage)",
    "Credits",
    "Dollars",
    "Performance Quarter",
)
_ASCAP_LAYOUT_B_COLUMNS = (
    "File Type",
    "Statement Recipient Name",
    "Statement Recipient ID",
    "Distribution Date",
    "Work Title",
    "Work ID",
    "$ Amount",
)
_ASCAP_INTERNATIONAL_INCOMING_COLUMNS = (
    "File Type",
    "Statement Recipient Name",
    "Statement Recipient ID",
    "Party Name",
    "Party ID",
    "Distribution Date",
    "Country Name",
    "Performance Start Date",
    "Performance End Date",
    "Work Title",
    "Work ID",
    "Revenue Class Code",
    "Revenue Class Description",
    "$ Amount",
    "Role Type",
    "Type Of Right",
    "Territory",
)


__all__ = (
    "_ASCAP_INTERNATIONAL_INCOMING_COLUMNS",
    "_ASCAP_LAYOUT_A_COLUMNS",
    "_ASCAP_LAYOUT_B_COLUMNS",
    "_PLATFORM_ACTIVITY_COLUMNS",
    "_PLAYLIST_PLACEMENT_COLUMNS",
    "Path",
    "_ascap_international_incoming_row",
    "_ascap_layout_a_row",
    "_ascap_layout_b_row",
    "_audience_growth_record",
    "_audience_growth_records",
    "_column_name",
    "_escape_xml",
    "_inline_string_cell",
    "_matching_records",
    "_matching_rows",
    "_platform_activity_row",
    "_playlist_placement_row",
    "_record",
    "_row",
    "_royalty_row",
    "_write_csv",
    "_write_json",
    "_write_platform_activity_csv",
    "_write_playlist_placement_csv",
    "_write_table",
    "_write_xlsx",
    "app",
    "json",
    "runner",
)


def _write_json(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(records), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    _write_table(path, _COLUMNS, rows)


def _write_playlist_placement_csv(path: Path, rows: list[dict[str, str]]) -> None:
    _write_table(path, _PLAYLIST_PLACEMENT_COLUMNS, rows)


def _write_platform_activity_csv(path: Path, rows: list[dict[str, str]]) -> None:
    _write_table(path, _PLATFORM_ACTIVITY_COLUMNS, rows)


def _write_table(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows([row[column] for column in columns] for row in rows)


def _write_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    row_values = [_COLUMNS, *(tuple(row[column] for column in _COLUMNS) for row in rows)]
    sheet_rows: list[str] = []

    for row_index, row in enumerate(row_values, start=1):
        cells = "".join(
            _inline_string_cell(row_index, column_index, value)
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


def _inline_string_cell(row_index: int, column_index: int, value: str) -> str:
    reference = f"{_column_name(column_index)}{row_index}"
    return f'<c r="{reference}" t="inlineStr"><is><t>{_escape_xml(value)}</t></is></c>'


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


def _matching_records() -> list[dict[str, object]]:
    return [
        _record(
            id="00000000-0000-0000-0000-000000000201",
            kind="playlist_activity",
            summary="Everything Is Fading received editorial playlist placement.",
            reference="spotify-playlist:dark-metal-editorial",
            signals=["playlist_placement"],
        ),
        _record(
            id="00000000-0000-0000-0000-000000000202",
            kind="audience_activity",
            summary="Streams increased 48% after the playlist placement.",
            reference="spotify-analytics:streams-week-2026-07-18",
            signals=["stream_growth"],
        ),
        _record(
            id="00000000-0000-0000-0000-000000000203",
            kind="audience_activity",
            summary="Save activity increased 31% after the playlist placement.",
            reference="spotify-analytics:saves-week-2026-07-18",
            signals=["save_growth"],
        ),
    ]


def _matching_rows() -> list[dict[str, str]]:
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


def _audience_growth_records() -> list[dict[str, object]]:
    return [
        _audience_growth_record(
            id="00000000-0000-0000-0000-000000000302",
            signals=["stream_growth"],
        ),
        _audience_growth_record(
            id="00000000-0000-0000-0000-000000000303",
            signals=["save_growth"],
        ),
    ]


def _audience_growth_record(
    *,
    id: str,
    summary: str = "Synthetic audience growth followed the playlist placement.",
    reference: str = "audience-growth:synthetic",
    signals: list[str],
) -> dict[str, object]:
    return _record(
        id=id,
        source_name="local_audience_export",
        kind="audience_activity",
        summary=summary,
        reference=reference,
        signals=signals,
    )


def _record(
    *,
    id: str = "00000000-0000-0000-0000-000000000201",
    source_name: str = "spotify",
    kind: str = "playlist_activity",
    summary: str = "Everything Is Fading received editorial playlist placement.",
    occurred_at: str = "2026-07-18T12:00:00+00:00",
    observed_at: str | None = None,
    reference: str = "spotify-playlist:dark-metal-editorial",
    signals: list[str],
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": id,
        "source_name": source_name,
        "kind": kind,
        "summary": summary,
        "occurred_at": occurred_at,
        "reference": reference,
        "signals": signals,
    }
    if observed_at is not None:
        record["observed_at"] = observed_at
    return record


def _ascap_layout_a_row(
    *,
    work_id: str = "SECRET_WORK_ID",
    performance_quarter: str = "2Q2026",
    performance_type: str = "Performance",
) -> dict[str, str]:
    return {
        "DistributionYear": "2026",
        "Distribution Quarter": "2",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Party ID": "SECRET_PARTY_ID",
        "Party Name": "SECRET_PARTY",
        "Performance Source/Broadcast Medium": "Streaming",
        "Music User Genre": "Digital",
        "Music User": "SECRET_USER",
        "Work ID": work_id,
        "Work Title": "SECRET_WORK_TITLE",
        "Number of Plays": "10",
        "Performance Type (Usage)": performance_type,
        "Credits": "1.23",
        "Dollars": "123.45",
        "Performance Quarter": performance_quarter,
    }


def _ascap_layout_b_row() -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Distribution Date": "01-31-2026",
        "Work Title": "SECRET_WORK_TITLE",
        "Work ID": "SECRET_WORK_ID",
        "$ Amount": "123.45",
    }


def _ascap_international_incoming_row(
    *,
    work_id: str = "SECRET_WORK_ID",
    distribution_date: str = "01-31-2026",
    country: str = "SECRET_COUNTRY",
    revenue_class_description: str = "SECRET_DESCRIPTION",
) -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Party Name": "SECRET_PARTY",
        "Party ID": "SECRET_PARTY_ID",
        "Distribution Date": distribution_date,
        "Country Name": country,
        "Performance Start Date": "01-01-2026",
        "Performance End Date": "01-31-2026",
        "Work Title": "SECRET_WORK_TITLE",
        "Work ID": work_id,
        "Revenue Class Code": "SECRET_CODE",
        "Revenue Class Description": revenue_class_description,
        "$ Amount": "123.45",
        "Role Type": "Writer",
        "Type Of Right": "Performance",
        "Territory": "SECRET_TERRITORY",
    }


def _royalty_row() -> dict[str, str]:
    return _row(
        id="00000000-0000-0000-0000-000000000901",
        source_name="local_statement_upload",
        kind="royalty_activity",
        summary="Royalties were reported for a synthetic statement period.",
        occurred_at="2026-06-30T23:59:00+00:00",
        observed_at="2026-07-21T12:00:00+00:00",
        reference="royalty-statement:synthetic:2026-q2",
        signals="royalty_reported",
    )


def _platform_activity_row(
    *,
    id: str = "00000000-0000-0000-0000-000000000302",
    source_name: str = "local_platform_export",
    summary: str = "Synthetic platform activity was reported.",
    occurred_at: str = "2026-07-19T12:00:00+00:00",
    observed_at: str = "",
    reference: str = "platform-activity:synthetic:1",
    signal: str = "stream_growth",
) -> dict[str, str]:
    return {
        "id": id,
        "source_name": source_name,
        "summary": summary,
        "occurred_at": occurred_at,
        "observed_at": observed_at,
        "reference": reference,
        "signal": signal,
    }


def _playlist_placement_row(
    *,
    id: str = "00000000-0000-0000-0000-000000000301",
    source_name: str = "local_playlist_export",
    summary: str = "Synthetic playlist placement was reported.",
    occurred_at: str = "2026-07-18T12:00:00+00:00",
    observed_at: str = "",
    reference: str = "playlist-placement:synthetic:1",
) -> dict[str, str]:
    return {
        "id": id,
        "source_name": source_name,
        "summary": summary,
        "occurred_at": occurred_at,
        "observed_at": observed_at,
        "reference": reference,
    }


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
