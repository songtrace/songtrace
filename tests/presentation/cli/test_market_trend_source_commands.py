# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


def test_market_trend_sources_lists_strategy_candidates() -> None:
    result = runner.invoke(app, ["market-trend-sources"])

    assert result.exit_code == 0
    assert "SongTrace Market Trend Source Strategy" in result.stdout
    assert "Purpose: choose upstream market trend evidence before deeper adapters." in result.stdout
    assert "google_trends" in result.stdout
    assert "tiktok_creative_center_and_sound_pages" in result.stdout
    assert "ascap_bmi_pro_and_distributor_reports" in result.stdout
    assert "no APIs, scraping, or private files are read" in result.stdout


def test_market_trend_sources_filters_by_priority_and_category() -> None:
    result = runner.invoke(
        app,
        [
            "market-trend-sources",
            "--priority",
            "P0",
            "--category",
            "search_intent",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_count"] >= 2
    assert {source["priority"] for source in payload["sources"]} == {"P0"}
    assert {source["category"] for source in payload["sources"]} == {"search_intent"}
    assert "google_trends" in [source["source_id"] for source in payload["sources"]]


def test_market_trend_source_shows_one_candidate() -> None:
    result = runner.invoke(app, ["market-trend-source", "google_trends"])

    assert result.exit_code == 0
    assert "SongTrace Market Trend Source Candidate" in result.stdout
    assert "Source ID: google_trends" in result.stdout
    assert "Name: Google Trends" in result.stdout
    assert "Early search-interest signal" in result.stdout
    assert "capture_terms_for_target_artist_song_genre_and_comparables" in result.stdout


def test_market_trend_source_json_is_deterministic() -> None:
    result = runner.invoke(app, ["market-trend-source", "google_trends", "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_count"] == 1
    assert payload["sources"][0]["source_id"] == "google_trends"
    assert payload["sources"][0]["access_model"] == "manual_capture"
    assert payload["sources"][0]["legal_terms_risk"] == "low"
    assert payload["sources"][0]["limitations"]


def test_market_trend_sources_rejects_unknown_priority() -> None:
    result = runner.invoke(app, ["market-trend-sources", "--priority", "P9"])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "priority must be P0, P1, or P2" in output
    assert "Traceback" not in output


def test_market_trend_source_rejects_unknown_source() -> None:
    result = runner.invoke(app, ["market-trend-source", "missing"])
    output = result.output + result.stderr

    assert result.exit_code == 1
    assert "Evidence source failed." in output
    assert "unknown market trend source: missing" in output
    assert "Traceback" not in output
