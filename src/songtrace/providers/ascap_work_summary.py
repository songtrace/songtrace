"""Private-safe ASCAP work-level CSV summary helpers."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class AscapWorkSummary:
    """Private-safe aggregate summary for a work across ASCAP CSV statements."""

    scanned_file_count: int
    matched_file_count: int
    matched_row_count: int
    statement_type_counts: tuple[tuple[str, int], ...]
    distribution_period_count: int
    territory_count: int
    revenue_class_count: int

    def to_json(self) -> str:
        """Serialize the safe summary as deterministic JSON."""

        return json.dumps(_to_jsonable(self), sort_keys=True)


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
    distribution_periods: set[str] = set()
    territories: set[str] = set()
    revenue_classes: set[str] = set()

    for file_rows in files:
        file_matched = False
        for row in file_rows.rows:
            if not _matches(row, work_id=normalized_work_id, title_query=normalized_title_query):
                continue

            file_matched = True
            matched_row_count += 1
            statement_type_counts[file_rows.statement_type] += 1
            _add_if_present(
                distribution_periods, _distribution_period(file_rows.statement_type, row)
            )
            _add_if_present(territories, _territory(file_rows.statement_type, row))
            _add_if_present(revenue_classes, _revenue_class(file_rows.statement_type, row))

        if file_matched:
            matched_file_count += 1

    return AscapWorkSummary(
        scanned_file_count=len(files),
        matched_file_count=matched_file_count,
        matched_row_count=matched_row_count,
        statement_type_counts=tuple(sorted(statement_type_counts.items())),
        distribution_period_count=len(distribution_periods),
        territory_count=len(territories),
        revenue_class_count=len(revenue_classes),
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


def _add_if_present(values: set[str], value: str | None) -> None:
    if value is not None and value.strip():
        values.add(value.strip())


def _to_jsonable(summary: AscapWorkSummary) -> dict[str, Any]:
    return {
        "distribution_period_count": summary.distribution_period_count,
        "matched_file_count": summary.matched_file_count,
        "matched_row_count": summary.matched_row_count,
        "revenue_class_count": summary.revenue_class_count,
        "scanned_file_count": summary.scanned_file_count,
        "statement_type_counts": dict(summary.statement_type_counts),
        "territory_count": summary.territory_count,
    }
