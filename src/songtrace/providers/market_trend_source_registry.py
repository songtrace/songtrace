"""Provider-neutral market trend source strategy registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

MarketTrendSignalCategory = Literal[
    "streaming_chart_demand",
    "social_velocity",
    "search_intent",
    "playlist_ecosystem",
    "live_touring_demand",
    "media_press_radio",
    "comparable_artist_signal",
    "royalty_outcome_evidence",
    "commercial_music_intelligence",
]
MarketTrendAccessModel = Literal[
    "public",
    "user_authorized",
    "commercial_private",
    "manual_capture",
]
MarketTrendSupportLevel = Literal["none", "indirect", "partial", "strong"]
MarketTrendFreshness = Literal["near_real_time", "daily_weekly", "monthly_quarterly", "lagging"]
MarketTrendDepth = Literal["snapshot", "limited_history", "historical"]
MarketTrendRiskLevel = Literal["low", "medium", "high"]
MarketTrendCostLevel = Literal["free", "low", "paid", "enterprise"]
MarketTrendPriority = Literal["P0", "P1", "P2"]


@dataclass(frozen=True, slots=True)
class MarketTrendSourceCandidate:
    """Candidate source for market trend evidence and opportunity validation."""

    source_id: str
    name: str
    category: MarketTrendSignalCategory
    access_model: MarketTrendAccessModel
    priority: MarketTrendPriority
    territory_support: MarketTrendSupportLevel
    genre_support: MarketTrendSupportLevel
    freshness: MarketTrendFreshness
    historical_depth: MarketTrendDepth
    provenance_strength: MarketTrendSupportLevel
    cost_level: MarketTrendCostLevel
    legal_terms_risk: MarketTrendRiskLevel
    recommended_use: str
    limitations: tuple[str, ...]
    next_validation_actions: tuple[str, ...]

    @property
    def strategy_score(self) -> int:
        """Rank practical usefulness before building deeper connectors."""

        return (
            _SUPPORT_SCORE[self.territory_support]
            + _SUPPORT_SCORE[self.genre_support]
            + _SUPPORT_SCORE[self.provenance_strength]
            + _FRESHNESS_SCORE[self.freshness]
            + _DEPTH_SCORE[self.historical_depth]
            + _ACCESS_SCORE[self.access_model]
            + _COST_SCORE[self.cost_level]
            + _RISK_SCORE[self.legal_terms_risk]
            + _PRIORITY_SCORE[self.priority]
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the candidate as deterministic JSON-friendly data."""

        return {
            "access_model": self.access_model,
            "category": self.category,
            "cost_level": self.cost_level,
            "freshness": self.freshness,
            "genre_support": self.genre_support,
            "historical_depth": self.historical_depth,
            "legal_terms_risk": self.legal_terms_risk,
            "limitations": list(self.limitations),
            "name": self.name,
            "next_validation_actions": list(self.next_validation_actions),
            "priority": self.priority,
            "provenance_strength": self.provenance_strength,
            "recommended_use": self.recommended_use,
            "source_id": self.source_id,
            "strategy_score": self.strategy_score,
            "territory_support": self.territory_support,
        }


_SUPPORT_SCORE: dict[MarketTrendSupportLevel, int] = {
    "strong": 12,
    "partial": 8,
    "indirect": 4,
    "none": 0,
}
_FRESHNESS_SCORE: dict[MarketTrendFreshness, int] = {
    "near_real_time": 12,
    "daily_weekly": 9,
    "monthly_quarterly": 5,
    "lagging": 2,
}
_DEPTH_SCORE: dict[MarketTrendDepth, int] = {
    "historical": 10,
    "limited_history": 6,
    "snapshot": 3,
}
_ACCESS_SCORE: dict[MarketTrendAccessModel, int] = {
    "manual_capture": 9,
    "public": 8,
    "user_authorized": 7,
    "commercial_private": 5,
}
_COST_SCORE: dict[MarketTrendCostLevel, int] = {
    "free": 8,
    "low": 6,
    "paid": 4,
    "enterprise": 1,
}
_RISK_SCORE: dict[MarketTrendRiskLevel, int] = {
    "low": 8,
    "medium": 4,
    "high": 0,
}
_PRIORITY_SCORE: dict[MarketTrendPriority, int] = {
    "P0": 8,
    "P1": 4,
    "P2": 1,
}


_MARKET_TREND_SOURCE_CANDIDATES: tuple[MarketTrendSourceCandidate, ...] = (
    MarketTrendSourceCandidate(
        source_id="google_trends",
        name="Google Trends",
        category="search_intent",
        access_model="manual_capture",
        priority="P0",
        territory_support="strong",
        genre_support="indirect",
        freshness="daily_weekly",
        historical_depth="historical",
        provenance_strength="partial",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Early search-interest signal for territories, genres, songs, artists, and "
            "comparable terms."
        ),
        limitations=(
            "Search interest is not music consumption by itself.",
            "Term selection and regional language variants require careful normalization.",
            "Small-volume queries may be unavailable or noisy.",
        ),
        next_validation_actions=(
            "capture_terms_for_target_artist_song_genre_and_comparables",
            "compare_target_territory_interest_against_known_performance_territories",
            "record_manual_export_or_screenshot_as_market_trend_evidence",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="youtube_charts_and_search",
        name="YouTube Charts and YouTube Search",
        category="streaming_chart_demand",
        access_model="manual_capture",
        priority="P0",
        territory_support="strong",
        genre_support="indirect",
        freshness="daily_weekly",
        historical_depth="limited_history",
        provenance_strength="partial",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Validate territory-level video demand, discovery behavior, and comparable "
            "artist momentum."
        ),
        limitations=(
            "Charts may not expose niche genre detail consistently.",
            "Search result ordering can vary by account, location, and time.",
            "Manual captures need timestamped references for reproducibility.",
        ),
        next_validation_actions=(
            "capture_territory_chart_or_search_snapshots_for_comparable_artists",
            "compare_video_velocity_against_streaming_or_social_signals",
            "treat_results_as_observations_not_causal_proof",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="tiktok_creative_center_and_sound_pages",
        name="TikTok Creative Center and sound pages",
        category="social_velocity",
        access_model="manual_capture",
        priority="P0",
        territory_support="partial",
        genre_support="indirect",
        freshness="near_real_time",
        historical_depth="limited_history",
        provenance_strength="partial",
        cost_level="free",
        legal_terms_risk="medium",
        recommended_use=(
            "Find short-form social velocity that may precede streaming, search, or "
            "royalty outcomes."
        ),
        limitations=(
            "Public availability and territory filters can vary.",
            "Sound pages may not reliably map to official recordings or rights ownership.",
            "Automation should not proceed without terms review.",
        ),
        next_validation_actions=(
            "manually_capture_sound_usage_velocity_for_target_and_comparables",
            "record_whether_official_audio_or_user_generated_audio_is_observed",
            "corroborate_with_search_streaming_or_ascap_platform_evidence",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="shazam_charts",
        name="Shazam Charts",
        category="search_intent",
        access_model="manual_capture",
        priority="P0",
        territory_support="strong",
        genre_support="indirect",
        freshness="daily_weekly",
        historical_depth="snapshot",
        provenance_strength="strong",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Detect territory-level active discovery intent where listeners are trying "
            "to identify tracks."
        ),
        limitations=(
            "Charts surface only tracks with enough Shazam activity.",
            "Genre context must be inferred from artists, tracks, or external metadata.",
            "Absence from a chart is weak negative evidence.",
        ),
        next_validation_actions=(
            "capture_relevant_territory_charts_for_target_and_comparable_tracks",
            "use_as_active_discovery_signal_not_full_market_size_measure",
            "compare_against_streaming_and_social_velocity_sources",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="chartmetric_soundcharts_viberate",
        name="Chartmetric, Soundcharts, Viberate, or similar commercial intelligence",
        category="commercial_music_intelligence",
        access_model="commercial_private",
        priority="P1",
        territory_support="strong",
        genre_support="partial",
        freshness="daily_weekly",
        historical_depth="historical",
        provenance_strength="strong",
        cost_level="enterprise",
        legal_terms_risk="low",
        recommended_use=(
            "High-value licensed source for cross-platform artist, track, playlist, "
            "social, and territory intelligence."
        ),
        limitations=(
            "May require paid access or partnership.",
            "Export rights and redistribution terms must be confirmed.",
            "Coverage and scoring methods may be opaque.",
        ),
        next_validation_actions=(
            "trial_or_request_sample_exports_for_target_artist_and_comparables",
            "evaluate_export_fields_against_provider_neutral_market_trend_shape",
            "confirm_license_terms_before_connector_development",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="spotify_charts_public",
        name="Spotify Charts public exports",
        category="streaming_chart_demand",
        access_model="manual_capture",
        priority="P1",
        territory_support="strong",
        genre_support="none",
        freshness="daily_weekly",
        historical_depth="limited_history",
        provenance_strength="strong",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Confirm territory-level streaming demand for tracks that reach public "
            "chart thresholds."
        ),
        limitations=(
            "Niche artists or catalog tracks may not appear.",
            "Genre and scene must be inferred externally.",
            "Public Spotify API playlist limitations make this insufficient alone.",
        ),
        next_validation_actions=(
            "use_public_chart_exports_when_target_or_comparable_tracks_chart",
            "avoid_treating_non_charting_as_absence_of_demand",
            "combine_with_search_social_playlist_or_commercial_intelligence_sources",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="bandsintown_songkick_festival_lineups",
        name="Bandsintown, Songkick, and festival lineups",
        category="live_touring_demand",
        access_model="manual_capture",
        priority="P1",
        territory_support="strong",
        genre_support="partial",
        freshness="daily_weekly",
        historical_depth="limited_history",
        provenance_strength="partial",
        cost_level="free",
        legal_terms_risk="medium",
        recommended_use=(
            "Validate whether territory opportunity is actionable through touring, "
            "promoters, venues, and festivals."
        ),
        limitations=(
            "Live-event listings indicate market infrastructure, not guaranteed fan demand.",
            "Automation and API availability require terms review.",
            "Genre mapping may require comparable artist and festival context.",
        ),
        next_validation_actions=(
            "map_comparable_artist_tour_activity_by_territory",
            "capture_genre_relevant_festivals_venues_and_promoters",
            "use_to_convert_opportunity_gap_into_actionable_market_plan",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="playlist_tracker_exports",
        name="Playlist tracker exports or user-authorized playlist intelligence",
        category="playlist_ecosystem",
        access_model="user_authorized",
        priority="P1",
        territory_support="partial",
        genre_support="partial",
        freshness="daily_weekly",
        historical_depth="historical",
        provenance_strength="strong",
        cost_level="paid",
        legal_terms_risk="low",
        recommended_use=(
            "Determine whether playlists or curators provide reachable distribution "
            "paths in a territory or scene."
        ),
        limitations=(
            "Public Spotify APIs are limited for exhaustive placement discovery.",
            "Territory attribution is often inferred from playlist metadata or "
            "follower composition.",
            "Licensed or user-authorized access may be required.",
        ),
        next_validation_actions=(
            "identify_available_playlist_tracker_exports",
            "profile_fields_for_playlist_genre_territory_followers_and_add_dates",
            "use_as_corroborating_distribution_path_evidence",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="reddit_discord_fan_communities",
        name="Reddit, Discord, and fan communities",
        category="social_velocity",
        access_model="manual_capture",
        priority="P2",
        territory_support="indirect",
        genre_support="strong",
        freshness="near_real_time",
        historical_depth="historical",
        provenance_strength="indirect",
        cost_level="free",
        legal_terms_risk="medium",
        recommended_use=(
            "Understand niche genre communities, language, comparable artists, and "
            "organic fan discussion."
        ),
        limitations=(
            "Territory is often unavailable or self-reported.",
            "Private communities require permission and should not be scraped casually.",
            "Discussion volume can be noisy and vulnerable to spam or campaign effects.",
        ),
        next_validation_actions=(
            "manually_review_public_genre_communities_for_territory_clues",
            "capture_only_public_or_authorized_references",
            "use_as_qualitative_context_for_recommendations",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="local_press_radio_blogs_podcasts",
        name="Local press, radio, blogs, and podcasts",
        category="media_press_radio",
        access_model="manual_capture",
        priority="P1",
        territory_support="strong",
        genre_support="strong",
        freshness="daily_weekly",
        historical_depth="historical",
        provenance_strength="partial",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Find culturally specific validation and outreach paths for a target "
            "territory or scene."
        ),
        limitations=(
            "Coverage is fragmented and difficult to normalize.",
            "Manual curation is likely needed before automation.",
            "Mentions may reflect publicity rather than organic demand.",
        ),
        next_validation_actions=(
            "build_manual_watchlist_for_target_genre_and_territories",
            "capture_mentions_of_comparable_artists_and_scene_activity",
            "translate_verified_sources_into_outreach_or_campaign_actions",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="meta_tiktok_google_ads_audience_estimates",
        name="Meta, TikTok, and Google Ads audience estimates",
        category="comparable_artist_signal",
        access_model="user_authorized",
        priority="P2",
        territory_support="strong",
        genre_support="partial",
        freshness="daily_weekly",
        historical_depth="snapshot",
        provenance_strength="partial",
        cost_level="low",
        legal_terms_risk="low",
        recommended_use=(
            "Translate observed opportunity gaps into practical test audiences and estimated reach."
        ),
        limitations=(
            "Audience estimates are planning signals, not organic demand proof.",
            "Platform taxonomy may not map cleanly to niche genres.",
            "Using this source may require ad-account access.",
        ),
        next_validation_actions=(
            "compare_target_genre_comparable_artist_and_interest_audiences_by_territory",
            "record_estimates_as_campaign_planning_evidence",
            "tie_recommendations_to_small_budget_tests_before_scaling",
        ),
    ),
    MarketTrendSourceCandidate(
        source_id="ascap_bmi_pro_and_distributor_reports",
        name="ASCAP, BMI/PRO, and distributor reports",
        category="royalty_outcome_evidence",
        access_model="user_authorized",
        priority="P0",
        territory_support="partial",
        genre_support="none",
        freshness="lagging",
        historical_depth="historical",
        provenance_strength="strong",
        cost_level="free",
        legal_terms_risk="low",
        recommended_use=(
            "Confirm monetized outcomes and platform or territory activity after the fact."
        ),
        limitations=(
            "Usually lagging and cannot explain causal origin alone.",
            "Territory, platform, and usage granularity varies by statement type.",
            "Private reports must remain outside the repository unless redacted.",
        ),
        next_validation_actions=(
            "use_as_high_confidence_commercial_outcome_evidence",
            "corroborate_with_upstream_social_search_streaming_or_playlist_signals",
            "preserve_platform_sources_found_causal_origin_unknown_when_needed",
        ),
    ),
)


def list_market_trend_source_candidates(
    *,
    priority: str | None = None,
    category: str | None = None,
) -> tuple[MarketTrendSourceCandidate, ...]:
    """Return ranked market trend source candidates for strategy planning."""

    candidates = _MARKET_TREND_SOURCE_CANDIDATES
    if priority is not None:
        candidates = tuple(candidate for candidate in candidates if candidate.priority == priority)
    if category is not None:
        candidates = tuple(candidate for candidate in candidates if candidate.category == category)
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.priority,
                -candidate.strategy_score,
                candidate.category,
                candidate.source_id,
            ),
        )
    )


def get_market_trend_source_candidate(source_id: str) -> MarketTrendSourceCandidate:
    """Return one market trend source candidate by source ID."""

    normalized_source_id = source_id.strip().casefold()
    for candidate in _MARKET_TREND_SOURCE_CANDIDATES:
        if candidate.source_id.casefold() == normalized_source_id:
            return candidate
    raise ValueError(f"unknown market trend source: {source_id}")


def market_trend_source_candidates_to_json(
    candidates: tuple[MarketTrendSourceCandidate, ...],
) -> str:
    """Serialize candidate source strategy data as deterministic JSON."""

    payload = {
        "source_count": len(candidates),
        "sources": [candidate.to_dict() for candidate in candidates],
    }
    return json.dumps(payload, sort_keys=True)


def validate_market_trend_source_registry() -> None:
    """Validate registry invariants at test and startup boundaries."""

    if not _MARKET_TREND_SOURCE_CANDIDATES:
        raise ValueError("market trend source registry must not be empty")

    seen_source_ids: set[str] = set()
    seen_categories: set[str] = set()
    seen_priorities: set[str] = set()
    for candidate in _MARKET_TREND_SOURCE_CANDIDATES:
        if not candidate.source_id or candidate.source_id.strip() != candidate.source_id:
            raise ValueError("market trend source IDs must be nonblank and normalized")
        if candidate.source_id in seen_source_ids:
            raise ValueError(f"duplicate market trend source ID: {candidate.source_id}")
        if not candidate.limitations:
            raise ValueError(f"market trend source missing limitations: {candidate.source_id}")
        if not candidate.next_validation_actions:
            raise ValueError(
                f"market trend source missing validation actions: {candidate.source_id}"
            )
        if not candidate.recommended_use:
            raise ValueError(f"market trend source missing recommended use: {candidate.source_id}")
        seen_source_ids.add(candidate.source_id)
        seen_categories.add(candidate.category)
        seen_priorities.add(candidate.priority)

    required_categories = {
        "streaming_chart_demand",
        "social_velocity",
        "search_intent",
        "playlist_ecosystem",
        "live_touring_demand",
        "media_press_radio",
        "comparable_artist_signal",
        "royalty_outcome_evidence",
        "commercial_music_intelligence",
    }
    missing_categories = sorted(required_categories.difference(seen_categories))
    if missing_categories:
        raise ValueError(f"market trend source registry missing category: {missing_categories[0]}")

    if "P0" not in seen_priorities:
        raise ValueError("market trend source registry must include P0 sources")
