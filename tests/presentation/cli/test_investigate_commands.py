# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


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


def test_investigate_evidence_combines_multiple_json_files_in_order(tmp_path: Path) -> None:
    playlist_path = tmp_path / "playlist-evidence.json"
    stream_path = tmp_path / "stream-evidence.json"
    save_path = tmp_path / "save-evidence.json"
    _write_json(playlist_path, [_matching_records()[0]])
    _write_json(stream_path, [_matching_records()[1]])
    _write_json(save_path, [_matching_records()[2]])

    result = runner.invoke(
        app,
        [
            "investigate-evidence",
            str(playlist_path),
            str(stream_path),
            str(save_path),
            "--output",
            "json",
        ],
    )

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


def test_investigate_evidence_later_file_failure_produces_no_partial_output(
    tmp_path: Path,
) -> None:
    valid_path = tmp_path / "valid-evidence.json"
    invalid_path = tmp_path / "invalid-evidence.json"
    _write_json(valid_path, [_matching_records()[0]])
    _write_json(
        invalid_path,
        [
            {
                "id": "00000000-0000-0000-0000-000000000202",
                "source_name": "spotify",
            }
        ],
    )

    result = runner.invoke(app, ["investigate-evidence", str(valid_path), str(invalid_path)])

    assert result.exit_code == 1
    assert "Evidence source failed." in result.stderr
    assert "SongTrace Evidence Investigation" not in result.stdout
    assert "Evidence: 1" not in result.stdout


def test_investigate_playlist_placement_csv_text_success(tmp_path: Path) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    evidence_path = tmp_path / "audience-evidence.json"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_json(evidence_path, _audience_growth_records())

    result = runner.invoke(
        app,
        ["investigate-playlist-placement-csv", str(playlist_path), str(evidence_path)],
    )

    assert result.exit_code == 0
    assert "SongTrace Evidence Investigation" in result.stdout
    assert "Evidence: 3" in result.stdout
    assert "Observations: 2" in result.stdout
    assert "Conclusions: 1" in result.stdout
    assert "Editorial playlist placement likely drove renewed listener engagement." in result.stdout


def test_investigate_playlist_placement_csv_json_success_with_traceability(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    evidence_path = tmp_path / "audience-evidence.json"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_json(evidence_path, _audience_growth_records())

    result = runner.invoke(
        app,
        [
            "investigate-playlist-placement-csv",
            str(playlist_path),
            str(evidence_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 3
    assert payload["observation_count"] == 2
    assert payload["conclusion_count"] == 1
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]
    assert set(payload["conclusions"][0]["supporting_observation_ids"]) == set(
        payload["observation_ids"]
    )


def test_investigate_playlist_placement_csv_preserves_supplemental_file_order(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    first_evidence_path = tmp_path / "first-audience-evidence.json"
    second_evidence_path = tmp_path / "second-audience-evidence.json"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_json(
        first_evidence_path,
        [
            _audience_growth_record(
                id="00000000-0000-0000-0000-000000000302", signals=["stream_growth"]
            )
        ],
    )
    _write_json(
        second_evidence_path,
        [
            _audience_growth_record(
                id="00000000-0000-0000-0000-000000000303", signals=["save_growth"]
            )
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-placement-csv",
            str(playlist_path),
            str(first_evidence_path),
            str(second_evidence_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]


def test_investigate_playlist_platform_csv_text_success(tmp_path: Path) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302", signal="stream_growth"
            ),
            _platform_activity_row(id="00000000-0000-0000-0000-000000000303", signal="save_growth"),
        ],
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-platform-csv", str(playlist_path), str(platform_path)],
    )

    assert result.exit_code == 0
    assert "SongTrace Evidence Investigation" in result.stdout
    assert "Evidence: 3" in result.stdout
    assert "Observations: 2" in result.stdout
    assert "Conclusions: 1" in result.stdout
    assert "Editorial playlist placement likely drove renewed listener engagement." in result.stdout


def test_investigate_playlist_platform_csv_json_success_with_traceability(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302", signal="stream_growth"
            ),
            _platform_activity_row(id="00000000-0000-0000-0000-000000000303", signal="save_growth"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 3
    assert payload["observation_count"] == 2
    assert payload["conclusion_count"] == 1
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]
    assert set(payload["conclusions"][0]["supporting_observation_ids"]) == set(
        payload["observation_ids"]
    )


def test_investigate_playlist_platform_csv_track_filter_keeps_matching_evidence(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    track = {
        "track_artist": "Warrel Dane",
        "track_title": "Everything Is Fading",
        "track_isrc": "USABC0800001",
    }
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row(**track)])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302",
                signal="stream_growth",
                **track,
            ),
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000303",
                signal="save_growth",
                **track,
            ),
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--track-isrc",
            "USABC0800001",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 3
    assert payload["observation_count"] == 2
    assert payload["conclusion_count"] == 1
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]


def test_investigate_playlist_platform_csv_track_filter_excludes_non_matching_evidence(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    target_track = {
        "track_artist": "Warrel Dane",
        "track_title": "Everything Is Fading",
        "track_isrc": "USABC0800001",
    }
    other_track = {
        "track_artist": "Warrel Dane",
        "track_title": "Brother",
        "track_isrc": "USABC0800002",
    }
    _write_playlist_placement_csv(
        path=playlist_path,
        rows=[
            _playlist_placement_row(**target_track),
            _playlist_placement_row(id="00000000-0000-0000-0000-000000000304", **other_track),
        ],
    )
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302",
                signal="stream_growth",
                **target_track,
            ),
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000303",
                signal="save_growth",
                **target_track,
            ),
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000305",
                signal="stream_growth",
                **other_track,
            ),
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--track-isrc",
            "USABC0800001",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]
    assert payload["conclusion_count"] == 1


def test_investigate_playlist_platform_csv_track_filter_excludes_missing_track_identity(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302", signal="stream_growth"
            ),
            _platform_activity_row(id="00000000-0000-0000-0000-000000000303", signal="save_growth"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 0
    assert payload["observation_count"] == 0
    assert payload["conclusion_count"] == 0
    assert payload["evidence_ids"] == []


def test_investigate_playlist_platform_csv_track_filter_requires_artist_and_title(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(path=platform_path, rows=[_platform_activity_row()])

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--track-isrc",
            "USABC0800001",
        ],
    )
    output = result.output + result.stderr

    assert result.exit_code != 0
    assert "Invalid value" in output
    assert "track filtering" in output
    assert "Traceback" not in output


def test_investigate_playlist_platform_csv_track_filter_uses_exact_isrc(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    track = {
        "track_artist": "Warrel Dane",
        "track_title": "Everything Is Fading",
        "track_isrc": "USABC0800001",
    }
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row(**track)])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302",
                signal="stream_growth",
                **track,
            )
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(platform_path),
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--track-isrc",
            "USABC0800002",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_count"] == 0
    assert payload["observation_count"] == 0


def test_investigate_playlist_platform_csv_preserves_platform_file_order(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    first_platform_path = tmp_path / "first-platform-activity.csv"
    second_platform_path = tmp_path / "second-platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(
        path=first_platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302", signal="stream_growth"
            )
        ],
    )
    _write_platform_activity_csv(
        path=second_platform_path,
        rows=[
            _platform_activity_row(id="00000000-0000-0000-0000-000000000303", signal="save_growth")
        ],
    )

    result = runner.invoke(
        app,
        [
            "investigate-playlist-platform-csv",
            str(playlist_path),
            str(first_platform_path),
            str(second_platform_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["evidence_ids"] == [
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
    ]


def test_investigate_playlist_platform_csv_requires_platform_file(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])

    result = runner.invoke(app, ["investigate-playlist-platform-csv", str(playlist_path)])
    output = result.output + result.stderr

    assert result.exit_code != 0
    assert "Missing argument" in output
    assert "platform_files" in output
    assert "Traceback" not in output


def test_investigate_playlist_platform_csv_reports_platform_source_failure(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_platform_activity_csv(
        path=platform_path,
        rows=[_platform_activity_row(occurred_at="2026-07-19T12:00:00")],
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-platform-csv", str(playlist_path), str(platform_path)],
    )
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "field 'occurred_at' must be timezone-aware" in output
    assert "Traceback" not in output


def test_investigate_playlist_platform_csv_success_output_is_privacy_safe(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "secret-playlist-placements.csv"
    platform_path = tmp_path / "secret-platform-activity.csv"
    _write_playlist_placement_csv(
        path=playlist_path,
        rows=[
            _playlist_placement_row(
                summary="SECRET_PLAYLIST_NAME drove private engagement.",
                reference="SECRET_PLAYLIST_REFERENCE",
            )
        ],
    )
    _write_platform_activity_csv(
        path=platform_path,
        rows=[
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000302",
                summary="SECRET_STREAM_SOURCE increased streams.",
                reference="SECRET_STREAM_REFERENCE",
                signal="stream_growth",
            ),
            _platform_activity_row(
                id="00000000-0000-0000-0000-000000000303",
                summary="SECRET_SAVE_SOURCE increased saves.",
                reference="SECRET_SAVE_REFERENCE",
                signal="save_growth",
            ),
        ],
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-platform-csv", str(playlist_path), str(platform_path)],
    )

    assert result.exit_code == 0
    assert "Conclusions: 1" in result.stdout
    assert "SECRET_PLAYLIST_NAME" not in result.stdout
    assert "SECRET_PLAYLIST_REFERENCE" not in result.stdout
    assert "SECRET_STREAM_SOURCE" not in result.stdout
    assert "SECRET_STREAM_REFERENCE" not in result.stdout
    assert "SECRET_SAVE_SOURCE" not in result.stdout
    assert "SECRET_SAVE_REFERENCE" not in result.stdout
    assert "secret-playlist-placements" not in result.stdout
    assert "secret-platform-activity" not in result.stdout


def test_investigate_playlist_placement_csv_missing_required_kind_produces_no_conclusion(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    evidence_path = tmp_path / "audience-evidence.json"
    _write_playlist_placement_csv(path=playlist_path, rows=[_playlist_placement_row()])
    _write_json(
        evidence_path,
        [
            _audience_growth_record(
                id="00000000-0000-0000-0000-000000000302", signals=["stream_growth"]
            )
        ],
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-placement-csv", str(playlist_path), str(evidence_path)],
    )

    assert result.exit_code == 0
    assert "Evidence: 2" in result.stdout
    assert "Observations: 1" in result.stdout
    assert "Conclusions: 0" in result.stdout
    assert (
        "Editorial playlist placement likely drove renewed listener engagement."
        not in result.stdout
    )


def test_investigate_playlist_placement_csv_reports_source_failure(tmp_path: Path) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    evidence_path = tmp_path / "audience-evidence.json"
    _write_playlist_placement_csv(
        path=playlist_path,
        rows=[_playlist_placement_row(occurred_at="2026-07-18T12:00:00")],
    )
    _write_json(evidence_path, _audience_growth_records())

    result = runner.invoke(
        app,
        ["investigate-playlist-placement-csv", str(playlist_path), str(evidence_path)],
    )
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "field 'occurred_at' must be timezone-aware" in output
    assert "Traceback" not in output


def test_investigate_playlist_placement_csv_reports_import_validation_failure(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    evidence_path = tmp_path / "audience-evidence.json"
    duplicate_id = "00000000-0000-0000-0000-000000000301"
    _write_playlist_placement_csv(
        path=playlist_path, rows=[_playlist_placement_row(id=duplicate_id)]
    )
    _write_json(
        evidence_path, [_audience_growth_record(id=duplicate_id, signals=["stream_growth"])]
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-placement-csv", str(playlist_path), str(evidence_path)],
    )
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence import failed." in output
    assert "Rejected record index: 1" in output
    assert "Accepted record count: 1" in output
    assert f"duplicate evidence id: {duplicate_id}" in output
    assert "Traceback" not in output


def test_investigate_playlist_placement_csv_success_output_is_privacy_safe(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "secret-playlist-placements.csv"
    evidence_path = tmp_path / "secret-audience-evidence.json"
    _write_playlist_placement_csv(
        path=playlist_path,
        rows=[
            _playlist_placement_row(
                summary="SECRET_PLAYLIST_NAME drove private engagement.",
                reference="SECRET_PLAYLIST_REFERENCE",
            )
        ],
    )
    _write_json(
        evidence_path,
        [
            _audience_growth_record(
                id="00000000-0000-0000-0000-000000000302",
                summary="SECRET_STREAM_SOURCE increased streams.",
                reference="SECRET_STREAM_REFERENCE",
                signals=["stream_growth"],
            ),
            _audience_growth_record(
                id="00000000-0000-0000-0000-000000000303",
                summary="SECRET_SAVE_SOURCE increased saves.",
                reference="SECRET_SAVE_REFERENCE",
                signals=["save_growth"],
            ),
        ],
    )

    result = runner.invoke(
        app,
        ["investigate-playlist-placement-csv", str(playlist_path), str(evidence_path)],
    )

    assert result.exit_code == 0
    assert "Conclusions: 1" in result.stdout
    assert "SECRET_PLAYLIST_NAME" not in result.stdout
    assert "SECRET_PLAYLIST_REFERENCE" not in result.stdout
    assert "SECRET_STREAM_SOURCE" not in result.stdout
    assert "SECRET_STREAM_REFERENCE" not in result.stdout
    assert "SECRET_SAVE_SOURCE" not in result.stdout
    assert "SECRET_SAVE_REFERENCE" not in result.stdout
    assert "secret-playlist-placements" not in result.stdout
    assert "secret-audience-evidence" not in result.stdout


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
