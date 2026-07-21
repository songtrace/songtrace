# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


def test_validate_spotify_environment_text_success_does_not_leak_values() -> None:
    result = runner.invoke(
        app,
        ["validate-spotify-environment"],
        env={
            "SONGTRACE_SPOTIFY_CLIENT_ID": "SECRET_CLIENT_ID",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET": "SECRET_CLIENT_SECRET",
        },
    )

    assert result.exit_code == 0
    assert "SongTrace Spotify Environment" in result.stdout
    assert "Client ID: present" in result.stdout
    assert "Client secret: present" in result.stdout
    assert "Configured: yes" in result.stdout
    assert "SECRET_CLIENT_ID" not in result.stdout
    assert "SECRET_CLIENT_SECRET" not in result.stdout


def test_validate_spotify_environment_json_success_does_not_leak_values() -> None:
    result = runner.invoke(
        app,
        ["validate-spotify-environment", "--output", "json"],
        env={
            "SONGTRACE_SPOTIFY_CLIENT_ID": "SECRET_CLIENT_ID",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET": "SECRET_CLIENT_SECRET",
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "client_id_present": True,
        "client_secret_present": True,
        "configured": True,
        "missing_variables": [],
    }
    assert "SECRET_CLIENT_ID" not in result.stdout
    assert "SECRET_CLIENT_SECRET" not in result.stdout


def test_validate_spotify_environment_missing_client_id_fails() -> None:
    result = runner.invoke(
        app,
        ["validate-spotify-environment"],
        env={
            "SONGTRACE_SPOTIFY_CLIENT_ID": "",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET": "SECRET_CLIENT_SECRET",
        },
    )

    assert result.exit_code == 1
    assert "Client ID: missing" in result.stdout
    assert "Client secret: present" in result.stdout
    assert "SONGTRACE_SPOTIFY_CLIENT_ID" in result.stdout
    assert "SECRET_CLIENT_SECRET" not in result.stdout


def test_validate_spotify_environment_missing_client_secret_fails() -> None:
    result = runner.invoke(
        app,
        ["validate-spotify-environment"],
        env={
            "SONGTRACE_SPOTIFY_CLIENT_ID": "SECRET_CLIENT_ID",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET": "",
        },
    )

    assert result.exit_code == 1
    assert "Client ID: present" in result.stdout
    assert "Client secret: missing" in result.stdout
    assert "SONGTRACE_SPOTIFY_CLIENT_SECRET" in result.stdout
    assert "SECRET_CLIENT_ID" not in result.stdout


def test_validate_spotify_environment_blank_values_are_missing_in_json() -> None:
    result = runner.invoke(
        app,
        ["validate-spotify-environment", "--output", "json"],
        env={
            "SONGTRACE_SPOTIFY_CLIENT_ID": " ",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET": "",
        },
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload == {
        "client_id_present": False,
        "client_secret_present": False,
        "configured": False,
        "missing_variables": [
            "SONGTRACE_SPOTIFY_CLIENT_ID",
            "SONGTRACE_SPOTIFY_CLIENT_SECRET",
        ],
    }


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


def test_validate_playlist_placement_csv_text_success(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_playlist_placement_csv(
        path,
        [
            _playlist_placement_row(id="00000000-0000-0000-0000-000000000301"),
            _playlist_placement_row(id="00000000-0000-0000-0000-000000000302"),
        ],
    )

    result = runner.invoke(app, ["validate-playlist-placement-csv", str(path)])

    assert result.exit_code == 0
    assert "SongTrace Evidence Validation" in result.stdout
    assert "Source name: local_playlist_placement_file" in result.stdout
    assert "Raw records: 2" in result.stdout
    assert "Evidence: 2" in result.stdout
    assert "00000000-0000-0000-0000-000000000301" in result.stdout
    assert "00000000-0000-0000-0000-000000000302" in result.stdout


def test_validate_playlist_placement_csv_json_success(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_playlist_placement_csv(
        path,
        [
            _playlist_placement_row(id="00000000-0000-0000-0000-000000000301"),
            _playlist_placement_row(id="00000000-0000-0000-0000-000000000302"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "validate-playlist-placement-csv",
            str(path),
            "--output",
            "json",
            "--source-name",
            "local_playlist_fixture",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_name"] == "local_playlist_fixture"
    assert payload["raw_record_count"] == 2
    assert payload["evidence_count"] == 2
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
    ]


def test_validate_playlist_placement_csv_uses_deterministic_metadata(
    tmp_path: Path,
) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_playlist_placement_csv(path, [_playlist_placement_row()])

    result = runner.invoke(
        app,
        [
            "validate-playlist-placement-csv",
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


def test_validate_playlist_placement_csv_reports_source_failure(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_playlist_placement_csv(
        path,
        [_playlist_placement_row(occurred_at="2026-07-18T12:00:00")],
    )

    result = runner.invoke(app, ["validate-playlist-placement-csv", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "field 'occurred_at' must be timezone-aware" in output
    assert "Traceback" not in output


def test_validate_playlist_placement_csv_reports_import_validation_failure(
    tmp_path: Path,
) -> None:
    path = tmp_path / "playlist-placements.csv"
    duplicate_id = "00000000-0000-0000-0000-000000000301"
    _write_playlist_placement_csv(
        path,
        [
            _playlist_placement_row(id=duplicate_id),
            _playlist_placement_row(id=duplicate_id, reference="playlist-placement:synthetic:2"),
        ],
    )

    result = runner.invoke(app, ["validate-playlist-placement-csv", str(path)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence import failed." in output
    assert "Rejected record index: 1" in output
    assert "Accepted record count: 1" in output
    assert f"duplicate evidence id: {duplicate_id}" in output
    assert "Traceback" not in output


def test_validate_playlist_placement_csv_success_output_is_privacy_safe(
    tmp_path: Path,
) -> None:
    path = tmp_path / "secret-playlist-placements.csv"
    _write_playlist_placement_csv(
        path,
        [
            _playlist_placement_row(
                summary="SECRET_PLAYLIST_NAME drove private engagement.",
                reference="SECRET_REFERENCE",
            )
        ],
    )

    result = runner.invoke(app, ["validate-playlist-placement-csv", str(path)])

    assert result.exit_code == 0
    assert "Raw records: 1" in result.stdout
    assert "Evidence: 1" in result.stdout
    assert "SECRET_PLAYLIST_NAME" not in result.stdout
    assert "SECRET_REFERENCE" not in result.stdout
    assert "secret-playlist-placements" not in result.stdout


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
