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


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "SongTrace 0.1.0" in result.stdout


def test_investigate() -> None:
    result = runner.invoke(
        app,
        [
            "investigate",
            "--artist",
            "Warrel Dane",
            "--track",
            "Everything Is Fading",
        ],
    )

    assert result.exit_code == 0
    assert "SongTrace Investigation" in result.stdout
    assert "Warrel Dane" in result.stdout
    assert "Everything Is Fading" in result.stdout
    assert "Awaiting evidence" in result.stdout


def test_validate_evidence_text_success(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["validate-evidence", str(path)])

    assert result.exit_code == 0
    assert "SongTrace Evidence Validation" in result.stdout
    assert "Batch ID:" in result.stdout
    assert "Source name: local_file" in result.stdout
    assert "Imported at:" in result.stdout
    assert "Raw records: 3" in result.stdout
    assert "Evidence: 3" in result.stdout
    assert "Evidence IDs:" in result.stdout
    assert "00000000-0000-0000-0000-000000000201" in result.stdout


def test_validate_evidence_json_success(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["validate-evidence", str(path), "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["batch_id"]
    assert payload["source_name"] == "local_file"
    assert payload["imported_at"]
    assert payload["raw_record_count"] == 3
    assert payload["evidence_count"] == 3
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000201",
        "00000000-0000-0000-0000-000000000202",
        "00000000-0000-0000-0000-000000000203",
    ]


def test_validate_evidence_uses_custom_source_name(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(
        app,
        ["validate-evidence", str(path), "--source-name", "local_statement_upload"],
    )

    assert result.exit_code == 0
    assert "Source name: local_statement_upload" in result.stdout


def test_validate_evidence_default_source_name_does_not_expose_local_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private-royalty-statement.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["validate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Source name: local_file" in result.stdout
    assert str(path) not in result.stdout
    assert "private-royalty-statement" not in result.stdout


def test_validate_evidence_rejects_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "evidence.txt"
    path.write_text("not evidence", encoding="utf-8")

    result = runner.invoke(app, ["validate-evidence", str(path)])

    assert result.exit_code != 0
    assert "unsupported evidence file extension" in result.output + result.stderr


def test_validate_evidence_reports_raw_source_failure(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text("not json", encoding="utf-8")

    result = runner.invoke(app, ["validate-evidence", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "Evidence JSON is invalid" in output
    assert "Traceback" not in output


def test_validate_evidence_reports_import_validation_failure(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(
        path,
        [
            _record(signals=["playlist_placement"]),
            _record(
                id="00000000-0000-0000-0000-000000000202",
                kind="playlist_activity",
                summary="Stream growth was mislabeled as playlist activity.",
                reference="spotify-analytics:bad-row",
                signals=["stream_growth"],
            ),
        ],
    )

    result = runner.invoke(app, ["validate-evidence", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence import failed." in output
    assert "Rejected record index: 1" in output
    assert "Accepted record count: 1" in output
    assert "Evidence signal must be compatible with evidence kind." in output
    assert "Traceback" not in output


def test_validate_evidence_does_not_require_observations_or_conclusions(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, [_record(signals=["playlist_placement"])])

    result = runner.invoke(app, ["validate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Raw records: 1" in result.stdout
    assert "Evidence: 1" in result.stdout
    assert "Observations" not in result.stdout
    assert "Conclusions" not in result.stdout


def test_investigate_evidence_json_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code == 0
    assert "SongTrace Evidence Investigation" in result.stdout
    assert "Evidence: 3" in result.stdout
    assert "Observations: 2" in result.stdout
    assert "Conclusions: 1" in result.stdout
    assert "Editorial playlist placement likely drove renewed listener engagement." in result.stdout


def test_investigate_evidence_csv_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.csv"
    _write_csv(path, _matching_rows())

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Evidence: 3" in result.stdout
    assert "Observations: 2" in result.stdout
    assert "Conclusions: 1" in result.stdout


def test_investigate_evidence_json_output_success(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["investigate-evidence", str(path), "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 3
    assert payload["observation_count"] == 2
    assert payload["conclusion_count"] == 1
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000201",
        "00000000-0000-0000-0000-000000000202",
        "00000000-0000-0000-0000-000000000203",
    ]


def test_investigate_evidence_json_output_includes_traceability_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["investigate-evidence", str(path), "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    conclusion = payload["conclusions"][0]
    assert conclusion["statement"] == (
        "Editorial playlist placement likely drove renewed listener engagement."
    )
    assert conclusion["confidence_level"] == "high"
    assert set(conclusion["supporting_observation_ids"]) == set(payload["observation_ids"])


def test_investigate_evidence_rejects_unsupported_output_format(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["investigate-evidence", str(path), "--output", "yaml"])

    assert result.exit_code != 0
    assert "unsupported output format" in result.output + result.stderr


def test_investigate_evidence_xlsx_file(tmp_path: Path) -> None:
    path = tmp_path / "evidence.xlsx"
    _write_xlsx(path, _matching_rows())

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Evidence: 3" in result.stdout
    assert "Observations: 2" in result.stdout
    assert "Conclusions: 1" in result.stdout


def test_investigate_evidence_rejects_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "evidence.txt"
    path.write_text("not evidence", encoding="utf-8")

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code != 0
    assert "unsupported evidence file extension" in result.output + result.stderr


def test_investigate_evidence_reports_no_conclusion_path(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, [_record(signals=["playlist_placement"])])

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Evidence: 1" in result.stdout
    assert "Observations: 0" in result.stdout
    assert "Conclusions: 0" in result.stdout
    assert (
        "Editorial playlist placement likely drove renewed listener engagement."
        not in result.stdout
    )


def test_investigate_evidence_reports_import_validation_failure(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(
        path,
        [
            _record(
                id="00000000-0000-0000-0000-000000000201",
                signals=["playlist_placement"],
            ),
            _record(
                id="00000000-0000-0000-0000-000000000202",
                source_name="spotify",
                kind="playlist_activity",
                summary="Stream growth was mislabeled as playlist activity.",
                reference="spotify-analytics:bad-row",
                signals=["stream_growth"],
            ),
        ],
    )

    result = runner.invoke(app, ["investigate-evidence", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence import failed." in output
    assert "Rejected record index: 1" in output
    assert "Accepted record count: 1" in output
    assert "Source: spotify" in output
    assert "Reference: spotify-analytics:bad-row" in output
    assert "Record ID: 00000000-0000-0000-0000-000000000202" in output
    assert "Evidence signal must be compatible with evidence kind." in output
    assert "Traceback" not in output


def test_investigate_evidence_reports_raw_source_failure(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text("not json", encoding="utf-8")

    result = runner.invoke(app, ["investigate-evidence", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "Evidence JSON is invalid" in output
    assert "Traceback" not in output


def test_investigate_evidence_validation_failure_uses_text_error_when_json_requested(
    tmp_path: Path,
) -> None:
    path = tmp_path / "evidence.json"
    path.write_text("not json", encoding="utf-8")

    result = runner.invoke(app, ["investigate-evidence", str(path), "--output", "json"])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "Evidence JSON is invalid" in output
    assert not output.strip().startswith("{")
    assert "Traceback" not in output


def _write_json(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(records), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(_COLUMNS)
        writer.writerows([row[column] for column in _COLUMNS] for row in rows)


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
