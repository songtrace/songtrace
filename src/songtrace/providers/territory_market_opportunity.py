"""Provider-neutral territory market opportunity gap reporting."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

_MARKET_TREND_REQUIRED_FIELDS = frozenset(
    {
        "observed_at",
        "territory",
        "genre",
        "metric_name",
        "metric_value",
        "source_name",
        "reference",
    }
)
_PERFORMANCE_REQUIRED_FIELDS = frozenset(
    {
        "observed_at",
        "territory",
        "metric_name",
        "metric_value",
        "source_name",
        "reference",
    }
)


@dataclass(frozen=True, slots=True)
class TerritoryMarketOpportunity:
    """Ranked territory gap between market trend strength and current performance."""

    rank: int
    territory: str
    genre: str
    opportunity_score: Decimal
    trend_score: Decimal
    performance_score: Decimal
    gap_score: Decimal
    confidence: str
    trend_record_count: int
    performance_record_count: int
    trend_source_count: int
    performance_source_count: int
    recommended_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerritoryMarketOpportunityReport:
    """Deterministic territory market opportunity gap report."""

    scanned_market_trend_rows: int
    scanned_performance_rows: int
    matched_market_trend_rows: int
    matched_performance_rows: int
    opportunity_count: int
    opportunities: tuple[TerritoryMarketOpportunity, ...]
    missing_evidence: tuple[str, ...]

    def to_json(self, *, include_opportunities: bool = False) -> str:
        """Serialize the report as deterministic JSON."""

        payload: dict[str, Any] = {
            "matched_market_trend_rows": self.matched_market_trend_rows,
            "matched_performance_rows": self.matched_performance_rows,
            "missing_evidence": list(self.missing_evidence),
            "opportunity_count": self.opportunity_count,
            "scanned_market_trend_rows": self.scanned_market_trend_rows,
            "scanned_performance_rows": self.scanned_performance_rows,
        }
        if include_opportunities:
            payload["opportunities"] = [
                {
                    "confidence": opportunity.confidence,
                    "gap_score": _format_decimal(opportunity.gap_score),
                    "genre": opportunity.genre,
                    "opportunity_score": _format_decimal(opportunity.opportunity_score),
                    "performance_record_count": opportunity.performance_record_count,
                    "performance_score": _format_decimal(opportunity.performance_score),
                    "performance_source_count": opportunity.performance_source_count,
                    "rank": opportunity.rank,
                    "recommended_actions": list(opportunity.recommended_actions),
                    "territory": opportunity.territory,
                    "trend_record_count": opportunity.trend_record_count,
                    "trend_score": _format_decimal(opportunity.trend_score),
                    "trend_source_count": opportunity.trend_source_count,
                }
                for opportunity in self.opportunities
            ]
        return json.dumps(payload, sort_keys=True)


def summarize_territory_market_opportunities(
    market_trends_csv: Path,
    performance_csv: Path,
    *,
    genre: str | None = None,
    minimum_trend_score: Decimal = Decimal("50"),
    maximum_performance_score: Decimal = Decimal("50"),
    limit: int = 10,
) -> TerritoryMarketOpportunityReport:
    """Compare market trend strength with current territory performance."""

    normalized_genre = _optional_nonblank(genre)
    if limit < 1:
        raise ValueError("limit must be at least 1")

    market_rows = _read_csv_rows(market_trends_csv, _MARKET_TREND_REQUIRED_FIELDS, "market trends")
    performance_rows = _read_csv_rows(performance_csv, _PERFORMANCE_REQUIRED_FIELDS, "performance")

    filtered_market_rows = tuple(
        row
        for row in market_rows
        if normalized_genre is None or row["genre"].casefold() == normalized_genre.casefold()
    )
    filtered_performance_rows = tuple(performance_rows)

    trend_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in filtered_market_rows:
        trend_groups[(_normalize_label(row["territory"]), _normalize_label(row["genre"]))].append(
            row
        )

    performance_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in filtered_performance_rows:
        performance_groups[_normalize_label(row["territory"])].append(row)

    candidates: list[TerritoryMarketOpportunity] = []
    for (territory, trend_genre), trend_rows in trend_groups.items():
        performance_group_rows = performance_groups.get(territory, [])
        trend_score = _average_metric_value(trend_rows)
        performance_score = _average_metric_value(performance_group_rows)
        if trend_score < minimum_trend_score:
            continue
        if performance_score > maximum_performance_score:
            continue

        gap_score = trend_score - performance_score
        if gap_score <= 0:
            continue

        trend_sources = _source_count(trend_rows)
        performance_sources = _source_count(performance_group_rows)
        opportunity_score = _opportunity_score(
            trend_score,
            performance_score,
            trend_sources=trend_sources,
            performance_sources=performance_sources,
        )
        candidates.append(
            TerritoryMarketOpportunity(
                rank=0,
                territory=territory,
                genre=trend_genre,
                opportunity_score=opportunity_score,
                trend_score=trend_score,
                performance_score=performance_score,
                gap_score=gap_score,
                confidence=_confidence(
                    trend_score,
                    performance_score,
                    trend_sources=trend_sources,
                    performance_sources=performance_sources,
                ),
                trend_record_count=len(trend_rows),
                performance_record_count=len(performance_group_rows),
                trend_source_count=trend_sources,
                performance_source_count=performance_sources,
                recommended_actions=_recommended_actions(performance_group_rows),
            )
        )

    ranked = tuple(
        TerritoryMarketOpportunity(
            rank=index,
            territory=opportunity.territory,
            genre=opportunity.genre,
            opportunity_score=opportunity.opportunity_score,
            trend_score=opportunity.trend_score,
            performance_score=opportunity.performance_score,
            gap_score=opportunity.gap_score,
            confidence=opportunity.confidence,
            trend_record_count=opportunity.trend_record_count,
            performance_record_count=opportunity.performance_record_count,
            trend_source_count=opportunity.trend_source_count,
            performance_source_count=opportunity.performance_source_count,
            recommended_actions=opportunity.recommended_actions,
        )
        for index, opportunity in enumerate(
            sorted(
                candidates,
                key=lambda opportunity: (
                    -opportunity.opportunity_score,
                    -opportunity.gap_score,
                    -opportunity.trend_score,
                    opportunity.performance_score,
                    opportunity.territory.casefold(),
                    opportunity.genre.casefold(),
                ),
            )[:limit],
            start=1,
        )
    )

    return TerritoryMarketOpportunityReport(
        scanned_market_trend_rows=len(market_rows),
        scanned_performance_rows=len(performance_rows),
        matched_market_trend_rows=len(filtered_market_rows),
        matched_performance_rows=len(filtered_performance_rows),
        opportunity_count=len(ranked),
        opportunities=ranked,
        missing_evidence=_missing_evidence(filtered_market_rows, filtered_performance_rows, ranked),
    )


def _read_csv_rows(
    path: Path, required_fields: frozenset[str], description: str
) -> tuple[dict[str, str], ...]:
    if not path.exists():
        raise FileNotFoundError(f"{description} CSV not found: {path}")
    if not path.is_file() or path.suffix.casefold() != ".csv":
        raise ValueError(f"{description} path must be a CSV file")

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"{description} CSV must include a header row")
        missing_fields = sorted(required_fields.difference(fieldnames))
        if missing_fields:
            raise ValueError(f"{description} CSV is missing required field: {missing_fields[0]}")
        rows = tuple(
            _validated_row(row, line_number, description)
            for line_number, row in enumerate(reader, 2)
        )
    return rows


def _validated_row(
    row: dict[str | None, str | None], line_number: int, description: str
) -> dict[str, str]:
    if None in row:
        raise ValueError(f"{description} CSV row {line_number} has too many columns")
    return {str(key): (value or "").strip() for key, value in row.items()}


def _average_metric_value(rows: list[dict[str, str]]) -> Decimal:
    if not rows:
        return Decimal("0")
    values = [_parse_decimal(row.get("metric_value", "")) for row in rows]
    return sum(values, Decimal("0")) / Decimal(len(values))


def _source_count(rows: list[dict[str, str]]) -> int:
    return len(
        {row.get("source_name", "").casefold() for row in rows if row.get("source_name", "")}
    )


def _opportunity_score(
    trend_score: Decimal,
    performance_score: Decimal,
    *,
    trend_sources: int,
    performance_sources: int,
) -> Decimal:
    source_bonus = Decimal(min(trend_sources + performance_sources, 4)) * Decimal("2.5")
    return (trend_score - performance_score) + source_bonus


def _confidence(
    trend_score: Decimal,
    performance_score: Decimal,
    *,
    trend_sources: int,
    performance_sources: int,
) -> str:
    if trend_score >= Decimal("70") and performance_score <= Decimal("30") and trend_sources >= 2:
        return "high"
    if trend_score >= Decimal("60") and performance_score <= Decimal("40"):
        return "medium"
    if trend_sources >= 1:
        return "low"
    return "insufficient"


def _recommended_actions(performance_rows: list[dict[str, str]]) -> tuple[str, ...]:
    base_actions = [
        "validate_local_playlist_and_media_ecosystem",
        "research_local_fan_communities_and_comparable_artists",
        "test_territory_targeted_ads_or_content",
        "identify_local_press_radio_promoter_or_touring_signals",
    ]
    if not performance_rows:
        return ("establish_baseline_artist_performance_in_territory", *base_actions)
    return tuple(base_actions)


def _missing_evidence(
    market_rows: tuple[dict[str, str], ...],
    performance_rows: tuple[dict[str, str], ...],
    opportunities: tuple[TerritoryMarketOpportunity, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    if not market_rows:
        missing.append("matching_market_trend_evidence")
    if not performance_rows:
        missing.append("artist_or_track_territory_performance_evidence")
    if market_rows and not opportunities:
        missing.append("market_trend_artist_performance_gap")
    if opportunities:
        missing.extend(
            [
                "local_playlist_media_and_community_evidence",
                "campaign_cost_and_targeting_evidence",
                "touring_promoter_or_partner_evidence",
            ]
        )
    return tuple(missing)


def _parse_decimal(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    if cleaned in {"", "-", "."}:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _normalize_label(value: str) -> str:
    return " ".join(value.strip().split())


def _optional_nonblank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
