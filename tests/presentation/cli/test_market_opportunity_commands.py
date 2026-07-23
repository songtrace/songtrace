# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


def test_territory_market_opportunity_gap_default_text_is_private_safe(tmp_path: Path) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_market_trend_csv(market, [_market_trend_row(territory="Brazil", metric_value="85")])
    _write_performance_territory_csv(
        performance,
        [_performance_territory_row(territory="Brazil", metric_value="15")],
    )

    result = runner.invoke(app, ["territory-market-opportunity-gap", str(market), str(performance)])

    assert result.exit_code == 0
    assert "SongTrace Territory Market Opportunity Gap Report" in result.stdout
    assert "Scanned market trend rows: 1" in result.stdout
    assert "Scanned performance rows: 1" in result.stdout
    assert "Opportunities: 1" in result.stdout
    assert "Opportunity candidates" not in result.stdout
    assert "Brazil" not in result.stdout
    assert "Progressive Metal" not in result.stdout
    assert "PRIVATE_ARTIST" not in result.stdout
    assert "PRIVATE_TRACK" not in result.stdout


def test_territory_market_opportunity_gap_opportunities_are_opt_in(tmp_path: Path) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_market_trend_csv(
        market,
        [
            _market_trend_row(territory="Brazil", metric_value="85", source_name="source-a"),
            _market_trend_row(territory="Brazil", metric_value="75", source_name="source-b"),
            _market_trend_row(territory="Germany", metric_value="70"),
        ],
    )
    _write_performance_territory_csv(
        performance,
        [
            _performance_territory_row(territory="Brazil", metric_value="15"),
            _performance_territory_row(territory="Germany", metric_value="45"),
        ],
    )

    result = runner.invoke(
        app,
        [
            "territory-market-opportunity-gap",
            str(market),
            str(performance),
            "--include-opportunities",
        ],
    )

    assert result.exit_code == 0
    assert "Opportunity candidates" in result.stdout
    assert "1. Brazil / Progressive Metal" in result.stdout
    assert "2. Germany / Progressive Metal" in result.stdout
    assert result.stdout.index("Brazil") < result.stdout.index("Germany")
    assert "Confidence: high" in result.stdout
    assert "validate_local_playlist_and_media_ecosystem" in result.stdout
    assert "PRIVATE_ARTIST" not in result.stdout
    assert "PRIVATE_TRACK" not in result.stdout


def test_territory_market_opportunity_gap_json_is_deterministic(tmp_path: Path) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_market_trend_csv(
        market,
        [
            _market_trend_row(territory="Brazil", metric_value="85", source_name="source-a"),
            _market_trend_row(territory="Brazil", metric_value="75", source_name="source-b"),
            _market_trend_row(territory="Japan", genre="Power Metal", metric_value="90"),
        ],
    )
    _write_performance_territory_csv(
        performance,
        [_performance_territory_row(territory="Brazil", metric_value="20")],
    )

    result = runner.invoke(
        app,
        [
            "territory-market-opportunity-gap",
            str(market),
            str(performance),
            "--genre",
            "Progressive Metal",
            "--include-opportunities",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "matched_market_trend_rows": 2,
        "matched_performance_rows": 1,
        "missing_evidence": [
            "local_playlist_media_and_community_evidence",
            "campaign_cost_and_targeting_evidence",
            "touring_promoter_or_partner_evidence",
        ],
        "opportunities": [
            {
                "confidence": "high",
                "gap_score": "60",
                "genre": "Progressive Metal",
                "opportunity_score": "67.5",
                "performance_record_count": 1,
                "performance_score": "20",
                "performance_source_count": 1,
                "rank": 1,
                "recommended_actions": [
                    "validate_local_playlist_and_media_ecosystem",
                    "research_local_fan_communities_and_comparable_artists",
                    "test_territory_targeted_ads_or_content",
                    "identify_local_press_radio_promoter_or_touring_signals",
                ],
                "territory": "Brazil",
                "trend_record_count": 2,
                "trend_score": "80",
                "trend_source_count": 2,
            }
        ],
        "opportunity_count": 1,
        "scanned_market_trend_rows": 3,
        "scanned_performance_rows": 1,
    }
    assert "PRIVATE_ARTIST" not in result.stdout
    assert "PRIVATE_TRACK" not in result.stdout


def test_territory_market_opportunity_gap_reports_missing_performance_evidence(
    tmp_path: Path,
) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_market_trend_csv(market, [_market_trend_row(territory="Brazil", metric_value="80")])
    _write_performance_territory_csv(performance, [])

    result = runner.invoke(
        app,
        [
            "territory-market-opportunity-gap",
            str(market),
            str(performance),
            "--include-opportunities",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["opportunity_count"] == 1
    assert "artist_or_track_territory_performance_evidence" in payload["missing_evidence"]
    assert payload["opportunities"][0]["recommended_actions"][0] == (
        "establish_baseline_artist_performance_in_territory"
    )


def test_territory_market_opportunity_gap_requires_supported_csv_shape(tmp_path: Path) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_table(market, ("territory", "genre"), [{"territory": "Brazil", "genre": "Prog"}])
    _write_performance_territory_csv(performance, [_performance_territory_row()])

    result = runner.invoke(app, ["territory-market-opportunity-gap", str(market), str(performance)])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "market trends CSV is missing required field" in output
    assert "Traceback" not in output


def test_territory_market_opportunity_gap_validates_limit(tmp_path: Path) -> None:
    market = tmp_path / "market.csv"
    performance = tmp_path / "performance.csv"
    _write_market_trend_csv(market, [_market_trend_row()])
    _write_performance_territory_csv(performance, [_performance_territory_row()])

    result = runner.invoke(
        app,
        ["territory-market-opportunity-gap", str(market), str(performance), "--limit", "0"],
    )
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "limit must be at least 1" in output
    assert "Traceback" not in output
