# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


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
    assert "breakdowns" not in payload
    assert "source_attribution" not in payload
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_work_text_breakdowns_are_opt_in(tmp_path: Path) -> None:
    domestic = tmp_path / "domestic.csv"
    international = tmp_path / "international.csv"
    _write_table(domestic, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])
    _write_table(
        international,
        _ASCAP_INTERNATIONAL_INCOMING_COLUMNS,
        [_ascap_international_incoming_row()],
    )

    result = runner.invoke(
        app,
        [
            "summarize-ascap-work",
            str(domestic),
            str(international),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-breakdowns",
        ],
    )

    assert result.exit_code == 0
    assert "Distribution periods/dates" in result.stdout
    assert "- 01-31-2026: 1" in result.stdout
    assert "- 2Q2026: 1" in result.stdout
    assert "Territories/countries" in result.stdout
    assert "- SECRET_COUNTRY: 1" in result.stdout
    assert "Revenue classes" in result.stdout
    assert "- Performance: 1" in result.stdout
    assert "- SECRET_DESCRIPTION: 1" in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_work_default_text_omits_breakdown_labels(tmp_path: Path) -> None:
    path = tmp_path / "international.csv"
    _write_table(
        path,
        _ASCAP_INTERNATIONAL_INCOMING_COLUMNS,
        [_ascap_international_incoming_row()],
    )

    result = runner.invoke(app, ["summarize-ascap-work", str(path), "--work-id", "SECRET_WORK_ID"])

    assert result.exit_code == 0
    assert "Distribution periods/dates: 1" in result.stdout
    assert "Territories/countries: 1" in result.stdout
    assert "Revenue classes: 1" in result.stdout
    assert "01-31-2026" not in result.stdout
    assert "SECRET_COUNTRY" not in result.stdout
    assert "SECRET_DESCRIPTION" not in result.stdout


def test_summarize_ascap_work_json_breakdowns_are_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "international.csv"
    _write_table(
        path,
        _ASCAP_INTERNATIONAL_INCOMING_COLUMNS,
        [
            _ascap_international_incoming_row(
                distribution_date="02-28-2026",
                country="ZZ_COUNTRY",
                revenue_class_description="ZZ_DESCRIPTION",
            ),
            _ascap_international_incoming_row(
                distribution_date="01-31-2026",
                country="AA_COUNTRY",
                revenue_class_description="AA_DESCRIPTION",
            ),
        ],
    )

    result = runner.invoke(
        app,
        [
            "summarize-ascap-work",
            str(path),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-breakdowns",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["breakdowns"] == {
        "distribution_periods": {"01-31-2026": 1, "02-28-2026": 1},
        "revenue_classes": {"AA_DESCRIPTION": 1, "ZZ_DESCRIPTION": 1},
        "statement_types": {"international_incoming": 2},
        "territories": {"AA_COUNTRY": 1, "ZZ_COUNTRY": 1},
    }
    assert result.stdout.index("01-31-2026") < result.stdout.index("02-28-2026")
    assert result.stdout.index("AA_COUNTRY") < result.stdout.index("ZZ_COUNTRY")
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_work_text_attribution_gaps_are_opt_in(tmp_path: Path) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(
        app,
        [
            "summarize-ascap-work",
            str(path),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-attribution-gaps",
        ],
    )

    assert result.exit_code == 0
    assert "Source attribution" in result.stdout
    assert "Status: royalty_activity_found_upstream_source_unknown" in result.stdout
    assert "- campaign_activity_logs" in result.stdout
    assert "- distributor_usage_source_evidence" in result.stdout
    assert "- platform_source_breakdowns" in result.stdout
    assert "- playlist_placement_evidence" in result.stdout
    assert "- social_post_evidence" in result.stdout
    assert "- video_traffic_source_evidence" in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_work_default_text_omits_attribution_gaps(tmp_path: Path) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(app, ["summarize-ascap-work", str(path), "--work-id", "SECRET_WORK_ID"])

    assert result.exit_code == 0
    assert "Source attribution" not in result.stdout
    assert "platform_source_breakdowns" not in result.stdout


def test_summarize_ascap_work_json_attribution_gaps_are_deterministic(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(
        app,
        [
            "summarize-ascap-work",
            str(path),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-attribution-gaps",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_attribution"] == {
        "missing_upstream_evidence": [
            "campaign_activity_logs",
            "distributor_usage_source_evidence",
            "platform_source_breakdowns",
            "playlist_placement_evidence",
            "social_post_evidence",
            "video_traffic_source_evidence",
        ],
        "status": "royalty_activity_found_upstream_source_unknown",
    }
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_platform_sources_default_text_omits_source_labels(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row(music_user="SPOTIFY")])

    result = runner.invoke(
        app,
        ["summarize-ascap-platform-sources", str(path), "--work-id", "SECRET_WORK_ID"],
    )

    assert result.exit_code == 0
    assert "SongTrace ASCAP Platform Sources" in result.stdout
    assert "Matched rows: 1" in result.stdout
    assert "Platform sources: 1" in result.stdout
    assert "Status: platform_sources_found_causal_origin_unknown" in result.stdout
    assert "SPOTIFY" not in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout
    assert "123.45" not in result.stdout


def test_summarize_ascap_platform_sources_text_sources_are_opt_in(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(
        path,
        _ASCAP_LAYOUT_A_COLUMNS,
        [
            _ascap_layout_a_row(
                music_user="SPOTIFY",
                music_user_genre="Interactive",
                performance_source_broadcast_medium="GN-IS",
                number_of_plays="100",
                dollars="10.25",
            ),
            _ascap_layout_a_row(
                music_user="TIKTOK",
                music_user_genre="Audio and Music Videos",
                performance_source_broadcast_medium="GN-AM",
                number_of_plays="250",
                dollars="0.50",
            ),
            _ascap_layout_a_row(work_id="OTHER_WORK", music_user="PRIVATE_OTHER"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "summarize-ascap-platform-sources",
            str(path),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-sources",
        ],
    )

    assert result.exit_code == 0
    assert "Platform source breakdown" in result.stdout
    assert "- TIKTOK: 250 plays, $0.50" in result.stdout
    assert "- SPOTIFY: 100 plays, $10.25" in result.stdout
    assert result.stdout.index("TIKTOK") < result.stdout.index("SPOTIFY")
    assert "PRIVATE_OTHER" not in result.stdout
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout


def test_summarize_ascap_platform_sources_json_sources_are_deterministic(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(
        path,
        _ASCAP_LAYOUT_A_COLUMNS,
        [
            _ascap_layout_a_row(music_user="SPOTIFY", number_of_plays="100", dollars="10.25"),
            _ascap_layout_a_row(music_user="SPOTIFY", number_of_plays="50", dollars="5.25"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "summarize-ascap-platform-sources",
            str(path),
            "--work-id",
            "SECRET_WORK_ID",
            "--include-sources",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["platform_source_count"] == 1
    assert payload["source_attribution"] == {
        "missing_upstream_evidence": [
            "campaign_activity_logs",
            "in_platform_source_breakdowns",
            "playlist_placement_evidence",
            "social_post_evidence",
            "video_traffic_source_evidence",
        ],
        "status": "platform_sources_found_causal_origin_unknown",
    }
    assert payload["platform_sources"] == [
        {
            "dollars": "15.5",
            "music_user": "SPOTIFY",
            "music_user_genre": "Digital",
            "number_of_plays": "150",
            "performance_source_broadcast_medium": "Streaming",
            "performance_type_usage": "Performance",
            "period_count": 1,
            "row_count": 2,
        }
    ]
    assert "SECRET_WORK_ID" not in result.stdout
    assert "SECRET_WORK_TITLE" not in result.stdout


def test_summarize_ascap_work_attribution_gaps_report_no_match_status(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domestic.csv"
    _write_table(path, _ASCAP_LAYOUT_A_COLUMNS, [_ascap_layout_a_row()])

    result = runner.invoke(
        app,
        [
            "summarize-ascap-work",
            str(path),
            "--work-id",
            "MISSING_WORK",
            "--include-attribution-gaps",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_attribution"] == {
        "missing_upstream_evidence": ["matching_royalty_activity"],
        "status": "no_matching_royalty_activity",
    }


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
