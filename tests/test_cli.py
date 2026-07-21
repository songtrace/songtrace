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


def test_profile_ascap_csv_layout_outputs_safe_json(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    path.write_text(
        "Work ID,Work Title,Music User,Dollars,Performance Quarter\n"
        "SECRET_WORK_ID,SECRET_WORK_TITLE,SECRET_USER,123.45,2Q2026\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["profile-ascap-csv-layout", str(path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["files"][0]["filename"] == "42278445.csv"
    assert payload["files"][0]["numeric_filename"] is True
    assert payload["files"][0]["row_count"] == 1
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_USER" not in result.stdout
    assert "123.45" not in result.stdout


def test_investigate_ascap_csv_layout_a_text_success(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row(), _ascap_layout_a_row()])

    result = runner.invoke(app, ["investigate-ascap-csv-layout-a", str(path)])

    assert result.exit_code == 0
    assert "SongTrace Evidence Investigation" in result.stdout
    assert "Evidence: 2" in result.stdout
    assert "Observations: 1" in result.stdout
    assert "Conclusions: 0" in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_investigate_ascap_csv_layout_a_json_success(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(app, ["investigate-ascap-csv-layout-a", str(path), "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 1
    assert payload["observation_count"] == 1
    assert payload["conclusion_count"] == 0
    assert payload["conclusions"] == []
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_investigate_ascap_csv_layout_a_rejects_unsupported_layout(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_table(path, _ASCAP_LAYOUT_B_COLUMNS, [_ascap_layout_b_row()])

    result = runner.invoke(app, ["investigate-ascap-csv-layout-a", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "ASCAP CSV layout A is missing required field" in output
    assert "Traceback" not in output


def test_summarize_ascap_work_text_combines_supported_statement_types(tmp_path: Path) -> None:
    domestic = tmp_path / "domestic.csv"
    international = tmp_path / "international.csv"
    _write_table(
        domestic,
        _ASCAP_LAYOUT_A_COLUMNS,
        [_ascap_layout_a_row(), _ascap_layout_a_row(work_id="OTHER_WORK")],
    )
    _write_table(
        international,
        _ASCAP_INTERNATIONAL_INCOMING_COLUMNS,
        [
            _ascap_international_incoming_row(),
            _ascap_international_incoming_row(work_id="OTHER_WORK"),
        ],
    )

    result = runner.invoke(
        app,
        ["summarize-ascap-work", str(domestic), str(international), "--work-id", "SECRET_WORK_ID"],
    )

    assert result.exit_code == 0
    assert "SongTrace ASCAP Work Summary" in result.stdout
    assert "Scanned files: 2" in result.stdout
    assert "Matched files: 2" in result.stdout
    assert "Matched rows: 2" in result.stdout
    assert "Distribution periods/dates: 2" in result.stdout
    assert "Territories/countries: 1" in result.stdout
    assert "Revenue classes: 2" in result.stdout
    assert "- domestic: 1" in result.stdout
    assert "- international_incoming: 1" in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout
    assert "domestic.csv" not in result.stdout
    assert "international.csv" not in result.stdout


def test_summarize_ascap_work_json_output_is_private_safe(tmp_path: Path) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(
        app,
        ["summarize-ascap-work", str(path), "--work-title", "secret_work", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "distribution_period_count": 1,
        "matched_file_count": 1,
        "matched_row_count": 1,
        "revenue_class_count": 1,
        "scanned_file_count": 1,
        "statement_type_counts": {"domestic": 1},
        "territory_count": 0,
    }
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_work_accepts_directory_input(tmp_path: Path) -> None:
    statements = tmp_path / "statements"
    statements.mkdir()
    _write_table(statements / "domestic.csv", _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])
    _write_table(
        statements / "international.csv",
        _ASCAP_INTERNATIONAL_INCOMING_COLUMNS,
        [_ascap_international_incoming_row()],
    )

    result = runner.invoke(
        app, ["summarize-ascap-work", str(statements), "--work-id", "SECRET_WORK_ID"]
    )

    assert result.exit_code == 0
    assert "Scanned files: 2" in result.stdout
    assert "Matched rows: 2" in result.stdout


def test_summarize_ascap_work_reports_no_matches(tmp_path: Path) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(app, ["summarize-ascap-work", str(path), "--work-id", "MISSING_WORK"])

    assert result.exit_code == 0
    assert "Matched files: 0" in result.stdout
    assert "Matched rows: 0" in result.stdout
    assert "- none: 0" in result.stdout


def test_summarize_ascap_work_requires_filter(tmp_path: Path) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(app, ["summarize-ascap-work", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "either work_id or work_title_query is required" in output
    assert "Traceback" not in output


def test_summarize_ascap_work_rejects_unsupported_layout(tmp_path: Path) -> None:
    path = tmp_path / "unsupported.csv"
    _write_table(
        path,
        ("Unsupported", "Work ID", "Work Title"),
        [{"Unsupported": "x", "Work ID": "SECRET_WORK_ID", "Work Title": "SECRET_WORK_TITLE"}],
    )

    result = runner.invoke(app, ["summarize-ascap-work", str(path), "--work-id", "SECRET_WORK_ID"])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "unsupported ASCAP CSV layout for work summary" in output
    assert "SECRET_WORK_ID" not in output
    assert "SECRET_WORK_TITLE" not in output
    assert "Traceback" not in output


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


def test_validate_evidence_text_uses_deterministic_metadata(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(
        app,
        [
            "validate-evidence",
            str(path),
            "--batch-id",
            "00000000-0000-0000-0000-000000000901",
            "--imported-at",
            "2026-07-21T12:00:00+00:00",
        ],
    )

    assert result.exit_code == 0
    assert "Batch ID: 00000000-0000-0000-0000-000000000901" in result.stdout
    assert "Imported at: 2026-07-21T12:00:00+00:00" in result.stdout


def test_validate_evidence_json_uses_deterministic_metadata(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(
        app,
        [
            "validate-evidence",
            str(path),
            "--output",
            "json",
            "--batch-id",
            "00000000-0000-0000-0000-000000000901",
            "--imported-at",
            "2026-07-21T12:00:00+00:00",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["batch_id"] == "00000000-0000-0000-0000-000000000901"
    assert payload["imported_at"] == "2026-07-21T12:00:00+00:00"


def test_validate_evidence_rejects_invalid_batch_id(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(app, ["validate-evidence", str(path), "--batch-id", "not-a-uuid"])

    assert result.exit_code != 0
    assert "batch ID must be a valid UUID" in result.output + result.stderr


def test_validate_evidence_rejects_invalid_imported_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(
        app,
        ["validate-evidence", str(path), "--imported-at", "not-a-datetime"],
    )

    assert result.exit_code != 0
    assert "imported_at must be an ISO datetime" in result.output + result.stderr


def test_validate_evidence_rejects_naive_imported_at(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_json(path, _matching_records())

    result = runner.invoke(
        app,
        ["validate-evidence", str(path), "--imported-at", "2026-07-21T12:00:00"],
    )

    assert result.exit_code != 0
    assert "imported_at must be timezone-aware" in result.output + result.stderr


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


def test_validate_evidence_accepts_royalty_reported_signal(tmp_path: Path) -> None:
    path = tmp_path / "royalty-evidence.csv"
    _write_csv(path, [_royalty_row()])

    result = runner.invoke(app, ["validate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Raw records: 1" in result.stdout
    assert "Evidence: 1" in result.stdout
    assert "00000000-0000-0000-0000-000000000901" in result.stdout


def test_investigate_evidence_extracts_royalty_observation_without_current_rules(
    tmp_path: Path,
) -> None:
    path = tmp_path / "royalty-evidence.csv"
    _write_csv(path, [_royalty_row()])

    result = runner.invoke(app, ["investigate-evidence", str(path)])

    assert result.exit_code == 0
    assert "Evidence: 1" in result.stdout
    assert "Observations: 1" in result.stdout
    assert "Conclusions: 0" in result.stdout


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
    _write_table(path, _COLUMNS, rows)


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


def _ascap_layout_a_row(*, work_id: str = "SECRET_WORK_ID") -> dict[str, str]:
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
        "Performance Type (Usage)": "Performance",
        "Credits": "1.23",
        "Dollars": "123.45",
        "Performance Quarter": "2Q2026",
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


def _ascap_international_incoming_row(*, work_id: str = "SECRET_WORK_ID") -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Party Name": "SECRET_PARTY",
        "Party ID": "SECRET_PARTY_ID",
        "Distribution Date": "01-31-2026",
        "Country Name": "SECRET_COUNTRY",
        "Performance Start Date": "01-01-2026",
        "Performance End Date": "01-31-2026",
        "Work Title": "SECRET_WORK_TITLE",
        "Work ID": work_id,
        "Revenue Class Code": "SECRET_CODE",
        "Revenue Class Description": "SECRET_DESCRIPTION",
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
