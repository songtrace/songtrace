"""ASCAP CSV raw evidence source for the profiled layout A statement format."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal

_LAYOUT_A_REQUIRED_FIELDS = frozenset(
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


@dataclass(frozen=True, slots=True)
class AscapCsvRawEvidenceSource:
    """Loads provider-neutral raw evidence records from ASCAP CSV layout A files."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load layout A ASCAP rows as deterministic royalty evidence records."""

        try:
            with self.path.open(newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames

                if fieldnames is None:
                    raise ValueError("ASCAP CSV must include a header row")

                _validate_layout_a_header(tuple(fieldnames))

                return tuple(
                    _record_from_row(row, path=self.path, line_number=line_number)
                    for line_number, row in enumerate(reader, start=2)
                )
        except FileNotFoundError as error:
            raise FileNotFoundError(f"ASCAP CSV file not found: {self.path}") from error


def _validate_layout_a_header(fieldnames: tuple[str, ...]) -> None:
    missing_fields = _LAYOUT_A_REQUIRED_FIELDS.difference(fieldnames)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"ASCAP CSV layout A is missing required field(s): {missing}")


def _record_from_row(
    row: dict[str | None, str | None],
    *,
    path: Path,
    line_number: int,
) -> RawEvidenceRecord:
    if None in row:
        raise ValueError(f"ASCAP CSV row {line_number} has too many columns")

    year = _required(row, "DistributionYear", line_number)
    quarter = _required(row, "Distribution Quarter", line_number)
    occurred_at = _quarter_end(year, quarter, line_number)
    reference = _safe_reference(path, line_number)

    return RawEvidenceRecord(
        id=_deterministic_id(reference),
        source_name="ascap",
        kind=EvidenceKind.ROYALTY_ACTIVITY,
        summary="ASCAP royalty activity was reported for a statement row.",
        occurred_at=occurred_at,
        reference=reference,
        signals=(EvidenceSignal.ROYALTY_REPORTED,),
    )


def _required(row: dict[str | None, str | None], field_name: str, line_number: int) -> str:
    value = row.get(field_name)
    if value is None or not value.strip():
        raise ValueError(f"ASCAP CSV row {line_number} is missing field '{field_name}'")
    return value.strip()


def _quarter_end(year_value: str, quarter_value: str, line_number: int) -> datetime:
    try:
        year = int(year_value)
    except ValueError as error:
        raise ValueError(
            f"ASCAP CSV row {line_number} field 'DistributionYear' must be a year"
        ) from error

    try:
        quarter = int(quarter_value)
    except ValueError as error:
        raise ValueError(
            f"ASCAP CSV row {line_number} field 'Distribution Quarter' must be 1, 2, 3, or 4"
        ) from error

    match quarter:
        case 1:
            return datetime(year, 3, 31, 23, 59, 59, tzinfo=UTC)
        case 2:
            return datetime(year, 6, 30, 23, 59, 59, tzinfo=UTC)
        case 3:
            return datetime(year, 9, 30, 23, 59, 59, tzinfo=UTC)
        case 4:
            return datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)
        case _:
            raise ValueError(
                f"ASCAP CSV row {line_number} field 'Distribution Quarter' must be 1, 2, 3, or 4"
            )


def _safe_reference(path: Path, line_number: int) -> str:
    file_digest = sha256(path.name.encode("utf-8")).hexdigest()[:12]
    return f"ascap-csv:layout-a:file:{file_digest}:row:{line_number}"


def _deterministic_id(reference: str) -> UUID:
    return uuid5(NAMESPACE_URL, reference)
