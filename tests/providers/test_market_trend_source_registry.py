import json

import pytest

from songtrace.providers.market_trend_source_registry import (
    get_market_trend_source_candidate,
    list_market_trend_source_candidates,
    market_trend_source_candidates_to_json,
    validate_market_trend_source_registry,
)


def test_market_trend_source_registry_is_valid() -> None:
    validate_market_trend_source_registry()


@pytest.mark.parametrize(
    "source_id",
    [
        "google_trends",
        "tiktok_creative_center_and_sound_pages",
        "ascap_bmi_pro_and_distributor_reports",
    ],
)
def test_market_trend_source_candidate_can_be_loaded_by_id(source_id: str) -> None:
    candidate = get_market_trend_source_candidate(source_id)

    assert candidate.source_id == source_id
    assert candidate.recommended_use
    assert candidate.limitations
    assert candidate.next_validation_actions
    assert candidate.strategy_score > 0


def test_market_trend_source_candidates_are_ranked_deterministically() -> None:
    candidates = list_market_trend_source_candidates()

    assert len(candidates) >= 10
    assert candidates[0].priority == "P0"
    assert "google_trends" in [candidate.source_id for candidate in candidates[:5]]
    assert [candidate.source_id for candidate in candidates] == [
        candidate.source_id for candidate in list_market_trend_source_candidates()
    ]


def test_market_trend_source_candidates_can_be_filtered_by_priority_and_category() -> None:
    candidates = list_market_trend_source_candidates(priority="P0", category="search_intent")

    assert candidates
    assert {candidate.priority for candidate in candidates} == {"P0"}
    assert {candidate.category for candidate in candidates} == {"search_intent"}


def test_market_trend_source_candidates_json_is_deterministic() -> None:
    candidates = list_market_trend_source_candidates(priority="P0")
    payload = json.loads(market_trend_source_candidates_to_json(candidates))

    assert payload["source_count"] == len(candidates)
    assert payload["sources"][0]["source_id"] == candidates[0].source_id
    assert payload["sources"][0]["strategy_score"] == candidates[0].strategy_score
    assert payload == json.loads(market_trend_source_candidates_to_json(candidates))


def test_unknown_market_trend_source_candidate_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="unknown market trend source: missing"):
        get_market_trend_source_candidate("missing")
