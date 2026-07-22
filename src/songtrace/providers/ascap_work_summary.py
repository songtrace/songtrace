"""Private-safe ASCAP work-level CSV summary helpers."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

_DOMESTIC_REQUIRED_FIELDS = frozenset(
    {
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
    }
)
_INTERNATIONAL_INCOMING_REQUIRED_FIELDS = frozenset(
    {
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
    }
)
StatementType = Literal["domestic", "international_incoming"]
_ATTRIBUTION_MISSING_UPSTREAM_EVIDENCE = (
    "campaign_activity_logs",
    "distributor_usage_source_evidence",
    "platform_source_breakdowns",
    "playlist_placement_evidence",
    "social_post_evidence",
    "video_traffic_source_evidence",
)
_NO_MATCH_MISSING_EVIDENCE = ("matching_royalty_activity",)
_CAUSAL_ATTRIBUTION_MISSING_EVIDENCE = (
    "campaign_activity_logs",
    "in_platform_source_breakdowns",
    "playlist_placement_evidence",
    "social_post_evidence",
    "video_traffic_source_evidence",
)


@dataclass(frozen=True, slots=True)
class AscapPlatformSourceSummary:
    """Aggregate platform source summary for matching ASCAP domestic rows."""

    music_user: str
    music_user_genre: str
    performance_source_broadcast_medium: str
    performance_type_usage: str
    row_count: int
    period_count: int
    number_of_plays: Decimal
    dollars: Decimal


@dataclass(frozen=True, slots=True)
class AscapPlatformSourcesSummary:
    """Private-safe platform attribution summary for a work across ASCAP CSVs."""

    scanned_file_count: int
    matched_file_count: int
    matched_row_count: int
    platform_source_count: int
    platform_sources: tuple[AscapPlatformSourceSummary, ...]
    source_attribution_status: str
    missing_upstream_evidence: tuple[str, ...]

    def to_json(self, *, include_sources: bool = False) -> str:
        """Serialize the platform summary as deterministic JSON."""

        payload: dict[str, Any] = {
            "matched_file_count": self.matched_file_count,
            "matched_row_count": self.matched_row_count,
            "platform_source_count": self.platform_source_count,
            "scanned_file_count": self.scanned_file_count,
            "source_attribution": {
                "missing_upstream_evidence": self.missing_upstream_evidence,
                "status": self.source_attribution_status,
            },
        }
        if include_sources:
            payload["platform_sources"] = [
                {
                    "dollars": _format_decimal(source.dollars),
                    "music_user": source.music_user,
                    "music_user_genre": source.music_user_genre,
                    "number_of_plays": _format_decimal(source.number_of_plays),
                    "performance_source_broadcast_medium": (
                        source.performance_source_broadcast_medium
                    ),
                    "performance_type_usage": source.performance_type_usage,
                    "period_count": source.period_count,
                    "row_count": source.row_count,
                }
                for source in self.platform_sources
            ]
        return json.dumps(payload, sort_keys=True)


@dataclass(frozen=True, slots=True)
class AscapWorkSummary:
    """Private-safe aggregate summary for a work across ASCAP CSV statements."""

    scanned_file_count: int
    matched_file_count: int
    matched_row_count: int
    statement_type_counts: tuple[tuple[str, int], ...]
    distribution_period_counts: tuple[tuple[str, int], ...]
    territory_counts: tuple[tuple[str, int], ...]
    revenue_class_counts: tuple[tuple[str, int], ...]
    source_attribution_status: str
    missing_upstream_evidence: tuple[str, ...]
    distribution_period_count: int
    territory_count: int
    revenue_class_count: int

    def to_json(
        self, *, include_breakdowns: bool = False, include_attribution_gaps: bool = False
    ) -> str:
        """Serialize the safe summary as deterministic JSON."""

        return json.dumps(
            _to_jsonable(
                self,
                include_breakdowns=include_breakdowns,
                include_attribution_gaps=include_attribution_gaps,
            ),
            sort_keys=True,
        )


@dataclass(frozen=True, slots=True)
class _FileRows:
    path: Path
    statement_type: StatementType
    rows: tuple[dict[str, str], ...]


def summarize_ascap_work(
    paths: tuple[Path, ...],
    *,
    work_id: str | None = None,
    work_title_query: str | None = None,
) -> AscapWorkSummary:
    """Summarize matching ASCAP CSV rows without exposing private row values."""

    normalized_work_id = _optional_nonblank(work_id)
    normalized_title_query = _optional_nonblank(work_title_query)
    if normalized_work_id is None and normalized_title_query is None:
        raise ValueError("either work_id or work_title_query is required")

    csv_paths = _csv_paths(paths)
    files = tuple(_read_supported_file(path) for path in csv_paths)

    matched_file_count = 0
    matched_row_count = 0
    statement_type_counts: Counter[str] = Counter()
    distribution_period_counts: Counter[str] = Counter()
    territory_counts: Counter[str] = Counter()
    revenue_class_counts: Counter[str] = Counter()

    for file_rows in files:
        file_matched = False
        for row in file_rows.rows:
            if not _matches(row, work_id=normalized_work_id, title_query=normalized_title_query):
                continue

            file_matched = True
            matched_row_count += 1
            statement_type_counts[file_rows.statement_type] += 1
            _count_if_present(
                distribution_period_counts, _distribution_period(file_rows.statement_type, row)
            )
            _count_if_present(territory_counts, _territory(file_rows.statement_type, row))
            _count_if_present(revenue_class_counts, _revenue_class(file_rows.statement_type, row))

        if file_matched:
            matched_file_count += 1

    source_attribution_status, missing_upstream_evidence = _source_attribution_gap(
        matched_row_count
    )

    return AscapWorkSummary(
        scanned_file_count=len(files),
        matched_file_count=matched_file_count,
        matched_row_count=matched_row_count,
        statement_type_counts=tuple(sorted(statement_type_counts.items())),
        distribution_period_counts=tuple(sorted(distribution_period_counts.items())),
        territory_counts=tuple(sorted(territory_counts.items())),
        revenue_class_counts=tuple(sorted(revenue_class_counts.items())),
        source_attribution_status=source_attribution_status,
        missing_upstream_evidence=missing_upstream_evidence,
        distribution_period_count=len(distribution_period_counts),
        territory_count=len(territory_counts),
        revenue_class_count=len(revenue_class_counts),
    )


def summarize_ascap_platform_sources(
    paths: tuple[Path, ...],
    *,
    work_id: str | None = None,
    work_title_query: str | None = None,
) -> AscapPlatformSourcesSummary:
    """Summarize ASCAP domestic Music User rows as platform attribution evidence."""

    normalized_work_id = _optional_nonblank(work_id)
    normalized_title_query = _optional_nonblank(work_title_query)
    if normalized_work_id is None and normalized_title_query is None:
        raise ValueError("either work_id or work_title_query is required")

    csv_paths = _csv_paths(paths)
    files = tuple(_read_supported_file(path) for path in csv_paths)

    matched_file_count = 0
    matched_row_count = 0
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for file_rows in files:
        file_matched = False
        for row in file_rows.rows:
            if not _matches(row, work_id=normalized_work_id, title_query=normalized_title_query):
                continue

            file_matched = True
            matched_row_count += 1
            if file_rows.statement_type != "domestic":
                continue

            key = (
                row.get("Music User", ""),
                row.get("Music User Genre", ""),
                row.get("Performance Source/Broadcast Medium", ""),
                row.get("Performance Type (Usage)", ""),
            )
            group = groups.setdefault(
                key,
                {
                    "dollars": Decimal("0"),
                    "number_of_plays": Decimal("0"),
                    "periods": set(),
                    "row_count": 0,
                },
            )
            group["row_count"] += 1
            group["number_of_plays"] += _parse_decimal(row.get("Number of Plays", ""))
            group["dollars"] += _parse_decimal(row.get("Dollars", ""))
            period = _distribution_period(file_rows.statement_type, row)
            if period is not None and period.strip():
                group["periods"].add(period.strip())

        if file_matched:
            matched_file_count += 1

    platform_sources = tuple(
        sorted(
            (
                AscapPlatformSourceSummary(
                    music_user=music_user,
                    music_user_genre=music_user_genre,
                    performance_source_broadcast_medium=medium,
                    performance_type_usage=usage,
                    row_count=int(group["row_count"]),
                    period_count=len(group["periods"]),
                    number_of_plays=group["number_of_plays"],
                    dollars=group["dollars"],
                )
                for (music_user, music_user_genre, medium, usage), group in groups.items()
            ),
            key=lambda source: (
                -source.number_of_plays,
                -source.dollars,
                source.music_user.casefold(),
                source.music_user_genre.casefold(),
                source.performance_source_broadcast_medium.casefold(),
                source.performance_type_usage.casefold(),
            ),
        )
    )
    source_attribution_status, missing_upstream_evidence = _platform_source_attribution_gap(
        matched_row_count, len(platform_sources)
    )

    return AscapPlatformSourcesSummary(
        scanned_file_count=len(files),
        matched_file_count=matched_file_count,
        matched_row_count=matched_row_count,
        platform_source_count=len(platform_sources),
        platform_sources=platform_sources,
        source_attribution_status=source_attribution_status,
        missing_upstream_evidence=missing_upstream_evidence,
    )


def _csv_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    if not paths:
        raise ValueError("at least one ASCAP CSV path or directory is required")

    csv_paths: list[Path] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"ASCAP path not found: {path}")
        if path.is_dir():
            csv_paths.extend(sorted(child for child in path.rglob("*.csv") if child.is_file()))
            continue
        if path.is_file() and path.suffix.casefold() == ".csv":
            csv_paths.append(path)
            continue
        raise ValueError("ASCAP work summary paths must be CSV files or directories")

    if not csv_paths:
        raise ValueError("no ASCAP CSV files found")

    return tuple(csv_paths)


def _read_supported_file(path: Path) -> _FileRows:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if fieldnames is None:
                raise ValueError("ASCAP CSV must include a header row")
            statement_type = _statement_type(tuple(fieldnames))
            rows = tuple(
                _validated_row(row, line_number) for line_number, row in enumerate(reader, 2)
            )
    except FileNotFoundError as error:
        raise FileNotFoundError(f"ASCAP CSV file not found: {path}") from error

    return _FileRows(path=path, statement_type=statement_type, rows=rows)


def _statement_type(fieldnames: tuple[str, ...]) -> StatementType:
    header = set(fieldnames)
    if _DOMESTIC_REQUIRED_FIELDS.issubset(header):
        return "domestic"
    if _INTERNATIONAL_INCOMING_REQUIRED_FIELDS.issubset(header):
        return "international_incoming"
    raise ValueError("unsupported ASCAP CSV layout for work summary")


def _validated_row(row: dict[str | None, str | None], line_number: int) -> dict[str, str]:
    if None in row:
        raise ValueError(f"ASCAP CSV row {line_number} has too many columns")
    return {str(key): (value or "").strip() for key, value in row.items()}


def _matches(row: dict[str, str], *, work_id: str | None, title_query: str | None) -> bool:
    if work_id is not None and row.get("Work ID", "").strip() == work_id:
        return True
    return (
        title_query is not None and title_query.casefold() in row.get("Work Title", "").casefold()
    )


def _distribution_period(statement_type: StatementType, row: dict[str, str]) -> str | None:
    if statement_type == "domestic":
        return row.get("Performance Quarter") or _domestic_distribution_period(row)
    return row.get("Distribution Date")


def _domestic_distribution_period(row: dict[str, str]) -> str | None:
    year = row.get("DistributionYear", "")
    quarter = row.get("Distribution Quarter", "")
    if not year or not quarter:
        return None
    return f"{year}-Q{quarter}"


def _territory(statement_type: StatementType, row: dict[str, str]) -> str | None:
    if statement_type == "domestic":
        return row.get("Territory")
    return row.get("Country Name") or row.get("Territory")


def _revenue_class(statement_type: StatementType, row: dict[str, str]) -> str | None:
    if statement_type == "domestic":
        return row.get("Performance Type (Usage)")
    return row.get("Revenue Class Description") or row.get("Revenue Class Code")


def _optional_nonblank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _count_if_present(counter: Counter[str], value: str | None) -> None:
    if value is not None and value.strip():
        counter[value.strip()] += 1


def _source_attribution_gap(matched_row_count: int) -> tuple[str, tuple[str, ...]]:
    if matched_row_count == 0:
        return "no_matching_royalty_activity", _NO_MATCH_MISSING_EVIDENCE
    return (
        "royalty_activity_found_upstream_source_unknown",
        _ATTRIBUTION_MISSING_UPSTREAM_EVIDENCE,
    )


def _platform_source_attribution_gap(
    matched_row_count: int, platform_source_count: int
) -> tuple[str, tuple[str, ...]]:
    if matched_row_count == 0:
        return "no_matching_royalty_activity", _NO_MATCH_MISSING_EVIDENCE
    if platform_source_count == 0:
        return (
            "royalty_activity_found_platform_source_unavailable",
            ("domestic_ascap_music_user_rows",),
        )
    return (
        "platform_sources_found_causal_origin_unknown",
        _CAUSAL_ATTRIBUTION_MISSING_EVIDENCE,
    )


def _parse_decimal(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "").replace("$", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", "-", "."}:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _to_jsonable(
    summary: AscapWorkSummary, *, include_breakdowns: bool, include_attribution_gaps: bool
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "distribution_period_count": summary.distribution_period_count,
        "matched_file_count": summary.matched_file_count,
        "matched_row_count": summary.matched_row_count,
        "revenue_class_count": summary.revenue_class_count,
        "scanned_file_count": summary.scanned_file_count,
        "statement_type_counts": dict(summary.statement_type_counts),
        "territory_count": summary.territory_count,
    }
    if include_breakdowns:
        payload["breakdowns"] = {
            "distribution_periods": dict(summary.distribution_period_counts),
            "revenue_classes": dict(summary.revenue_class_counts),
            "statement_types": dict(summary.statement_type_counts),
            "territories": dict(summary.territory_counts),
        }
    if include_attribution_gaps:
        payload["source_attribution"] = {
            "missing_upstream_evidence": summary.missing_upstream_evidence,
            "status": summary.source_attribution_status,
        }
    return payload
