"""Private-safe ASCAP CSV layout profiling helper."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

_DATE_PERIOD_COLUMNS = (
    "Distribution Date",
    "DistributionYear",
    "Distribution Quarter",
    "Original Distribution Date",
    "Performance Start Date",
    "Performance End Date",
    "Performance Quarter",
)
_NUMERIC_COLUMNS = (
    "$ Amount",
    "CA%",
    "Credits",
    "DistributionYear",
    "Dollars",
    "Duration",
    "EE Share",
    "Number of Plays",
    "Premium Credits",
    "Premium Dollars",
)
_ROW_GRAIN_CANDIDATES = (
    ("Work ID",),
    ("Work ID", "Music User"),
    ("Work ID", "Music User", "Performance Source/Broadcast Medium"),
    ("Work ID", "Music User", "Performance Source/Broadcast Medium", "Performance Type (Usage)"),
    ("Work ID", "Music User Genre"),
    ("Work ID", "Performance Source/Broadcast Medium"),
    ("Work ID", "Performance Type (Usage)"),
)


@dataclass(frozen=True, slots=True)
class AscapCsvColumnProfile:
    """Safe aggregate profile for one CSV column."""

    name: str
    nonblank_count: int
    blank_count: int
    distinct_nonblank_count: int
    status: str


@dataclass(frozen=True, slots=True)
class AscapCsvNumericProfile:
    """Safe numeric parsing profile for one CSV column."""

    column: str
    parsed_count: int
    blank_count: int
    failed_count: int
    positive_row_count: int
    zero_row_count: int
    negative_row_count: int


@dataclass(frozen=True, slots=True)
class AscapCsvRowGrainProfile:
    """Safe row-grain candidate profile."""

    columns: tuple[str, ...]
    available: bool
    distinct_key_count: int | None
    duplicate_row_count: int | None


@dataclass(frozen=True, slots=True)
class AscapCsvFileProfile:
    """Private-safe ASCAP CSV file layout profile."""

    filename: str
    numeric_filename: bool
    row_count: int
    column_count: int
    header: tuple[str, ...]
    columns: tuple[AscapCsvColumnProfile, ...]
    date_period_masks: dict[str, dict[str, int]]
    numeric_profiles: tuple[AscapCsvNumericProfile, ...]
    row_grain_profiles: tuple[AscapCsvRowGrainProfile, ...]
    exact_duplicate_full_row_count: int


@dataclass(frozen=True, slots=True)
class AscapCsvLayoutProfile:
    """Private-safe ASCAP CSV layout profile for one or more files."""

    files: tuple[AscapCsvFileProfile, ...]
    unique_header_shape_count: int
    common_columns: tuple[str, ...]

    def to_json(self) -> str:
        """Serialize the safe profile as deterministic JSON."""

        return json.dumps(_to_jsonable(self), sort_keys=True)


def profile_ascap_csv_layout(paths: tuple[Path, ...]) -> AscapCsvLayoutProfile:
    """Profile ASCAP CSV layouts without exposing row values or sensitive measures."""

    if not paths:
        raise ValueError("at least one ASCAP CSV path is required")

    file_profiles = tuple(_profile_file(path) for path in paths)
    headers = tuple(file_profile.header for file_profile in file_profiles)
    common_columns = _common_columns(headers)

    return AscapCsvLayoutProfile(
        files=file_profiles,
        unique_header_shape_count=len(set(headers)),
        common_columns=common_columns,
    )


def _profile_file(path: Path) -> AscapCsvFileProfile:
    header, rows = _read_csv(path)
    columns = tuple(_profile_column(name, rows) for name in header)

    return AscapCsvFileProfile(
        filename=path.name,
        numeric_filename=path.stem.isdigit(),
        row_count=len(rows),
        column_count=len(header),
        header=tuple(header),
        columns=columns,
        date_period_masks=_date_period_masks(header, rows),
        numeric_profiles=tuple(
            _numeric_profile(column, rows) for column in _present_numeric_columns(header)
        ),
        row_grain_profiles=tuple(
            _row_grain_profile(columns, header, rows) for columns in _ROW_GRAIN_CANDIDATES
        ),
        exact_duplicate_full_row_count=_exact_duplicate_full_row_count(header, rows),
    )


def _read_csv(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if fieldnames is None:
                raise ValueError(f"ASCAP CSV must include a header row: {path}")
            rows = tuple(dict(row) for row in reader)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"ASCAP CSV file not found: {path}") from error

    return tuple(fieldnames), rows


def _profile_column(name: str, rows: tuple[dict[str, str], ...]) -> AscapCsvColumnProfile:
    values = tuple(_cell(row, name) for row in rows)
    nonblank_values = tuple(value for value in values if value)
    distinct_nonblank_count = len(set(nonblank_values))
    status = _column_status(len(nonblank_values), distinct_nonblank_count)

    return AscapCsvColumnProfile(
        name=name,
        nonblank_count=len(nonblank_values),
        blank_count=len(rows) - len(nonblank_values),
        distinct_nonblank_count=distinct_nonblank_count,
        status=status,
    )


def _column_status(nonblank_count: int, distinct_nonblank_count: int) -> str:
    if nonblank_count == 0:
        return "empty_all_rows"
    if distinct_nonblank_count == 1:
        return "constant_nonblank"
    return "variable"


def _date_period_masks(
    header: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> dict[str, dict[str, int]]:
    masks: dict[str, dict[str, int]] = {}
    for column in _DATE_PERIOD_COLUMNS:
        if column in header:
            counter = Counter(_shape_mask(_cell(row, column)) for row in rows)
            masks[column] = dict(sorted(counter.items()))
    return masks


def _shape_mask(value: str) -> str:
    if not value:
        return "<empty>"

    masked: list[str] = []
    for character in value:
        if character.isdigit():
            masked.append("9")
        elif character.isalpha():
            masked.append("A")
        elif character.isspace():
            masked.append(" ")
        else:
            masked.append(character)
    return "".join(masked)


def _present_numeric_columns(header: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(column for column in _NUMERIC_COLUMNS if column in header)


def _numeric_profile(column: str, rows: tuple[dict[str, str], ...]) -> AscapCsvNumericProfile:
    parsed_count = 0
    blank_count = 0
    failed_count = 0
    positive_row_count = 0
    zero_row_count = 0
    negative_row_count = 0

    for row in rows:
        value = _cell(row, column).replace(",", "").replace("$", "")
        if not value:
            blank_count += 1
            continue

        try:
            number = Decimal(value)
        except InvalidOperation:
            failed_count += 1
            continue

        parsed_count += 1
        if number > 0:
            positive_row_count += 1
        elif number == 0:
            zero_row_count += 1
        else:
            negative_row_count += 1

    return AscapCsvNumericProfile(
        column=column,
        parsed_count=parsed_count,
        blank_count=blank_count,
        failed_count=failed_count,
        positive_row_count=positive_row_count,
        zero_row_count=zero_row_count,
        negative_row_count=negative_row_count,
    )


def _row_grain_profile(
    columns: tuple[str, ...], header: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> AscapCsvRowGrainProfile:
    if not all(column in header for column in columns):
        return AscapCsvRowGrainProfile(
            columns=columns,
            available=False,
            distinct_key_count=None,
            duplicate_row_count=None,
        )

    keys = tuple(tuple(_cell(row, column) for column in columns) for row in rows)
    distinct_key_count = len(set(keys))

    return AscapCsvRowGrainProfile(
        columns=columns,
        available=True,
        distinct_key_count=distinct_key_count,
        duplicate_row_count=len(rows) - distinct_key_count,
    )


def _exact_duplicate_full_row_count(
    header: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> int:
    keys = tuple(tuple(_cell(row, column) for column in header) for row in rows)
    return len(rows) - len(set(keys))


def _common_columns(headers: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    if not headers:
        return ()

    common = set(headers[0])
    for header in headers[1:]:
        common &= set(header)

    return tuple(sorted(common))


def _cell(row: dict[str, str], column: str) -> str:
    return (row.get(column) or "").strip()


def _to_jsonable(value: object) -> Any:
    if isinstance(value, AscapCsvLayoutProfile):
        return {
            "common_columns": value.common_columns,
            "files": tuple(_to_jsonable(file_profile) for file_profile in value.files),
            "unique_header_shape_count": value.unique_header_shape_count,
        }
    if isinstance(value, AscapCsvFileProfile):
        return {
            "column_count": value.column_count,
            "columns": tuple(_to_jsonable(column) for column in value.columns),
            "date_period_masks": value.date_period_masks,
            "exact_duplicate_full_row_count": value.exact_duplicate_full_row_count,
            "filename": value.filename,
            "header": value.header,
            "numeric_filename": value.numeric_filename,
            "numeric_profiles": tuple(
                _to_jsonable(numeric_profile) for numeric_profile in value.numeric_profiles
            ),
            "row_count": value.row_count,
            "row_grain_profiles": tuple(
                _to_jsonable(row_grain_profile) for row_grain_profile in value.row_grain_profiles
            ),
        }
    if isinstance(value, AscapCsvColumnProfile):
        return {
            "blank_count": value.blank_count,
            "distinct_nonblank_count": value.distinct_nonblank_count,
            "name": value.name,
            "nonblank_count": value.nonblank_count,
            "status": value.status,
        }
    if isinstance(value, AscapCsvNumericProfile):
        return {
            "blank_count": value.blank_count,
            "column": value.column,
            "failed_count": value.failed_count,
            "negative_row_count": value.negative_row_count,
            "parsed_count": value.parsed_count,
            "positive_row_count": value.positive_row_count,
            "zero_row_count": value.zero_row_count,
        }
    if isinstance(value, AscapCsvRowGrainProfile):
        return {
            "available": value.available,
            "columns": value.columns,
            "distinct_key_count": value.distinct_key_count,
            "duplicate_row_count": value.duplicate_row_count,
        }

    raise TypeError(f"Unsupported value for JSON serialization: {type(value).__name__}")
