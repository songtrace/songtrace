"""ASCAP CSV raw evidence source for the profiled International Incoming statement format."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal

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


@dataclass(frozen=True, slots=True)
class AscapInternationalIncomingCsvRawEvidenceSource:
    """Loads provider-neutral raw evidence records from ASCAP International Incoming CSV files."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load International Incoming ASCAP rows as deterministic royalty evidence records."""

        try:
            with self.path.open(newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames

                if fieldnames is None:
                    raise ValueError("ASCAP CSV must include a header row")

                _validate_international_incoming_header(tuple(fieldnames))

                return tuple(
                    _record_from_row(row, path=self.path, line_number=line_number)
                    for line_number, row in enumerate(reader, start=2)
                )
        except FileNotFoundError as error:
            raise FileNotFoundError(f"ASCAP CSV file not found: {self.path}") from error


def _validate_international_incoming_header(fieldnames: tuple[str, ...]) -> None:
    missing_fields = _INTERNATIONAL_INCOMING_REQUIRED_FIELDS.difference(fieldnames)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"ASCAP international incoming CSV is missing required field(s): {missing}"
        )


def _record_from_row(
    row: dict[str | None, str | None],
    *,
    path: Path,
    line_number: int,
) -> RawEvidenceRecord:
    if None in row:
        raise ValueError(f"ASCAP CSV row {line_number} has too many columns")

    distribution_date = _required(row, "Distribution Date", line_number)
    occurred_at = _distribution_date(distribution_date, line_number)
    reference = _safe_reference(path, line_number)

    return RawEvidenceRecord(
        id=_deterministic_id(reference),
        source_name="ascap",
        kind=EvidenceKind.ROYALTY_ACTIVITY,
        summary="ASCAP international incoming royalty activity was reported for a statement row.",
        occurred_at=occurred_at,
        reference=reference,
        signals=(EvidenceSignal.ROYALTY_REPORTED,),
    )


def _required(row: dict[str | None, str | None], field_name: str, line_number: int) -> str:
    value = row.get(field_name)
    if value is None or not value.strip():
        raise ValueError(f"ASCAP CSV row {line_number} is missing field '{field_name}'")
    return value.strip()


def _distribution_date(value: str, line_number: int) -> datetime:
    try:
        parsed = datetime.strptime(value, "%m-%d-%Y").replace(tzinfo=UTC)
    except ValueError as error:
        raise ValueError(
            f"ASCAP CSV row {line_number} field 'Distribution Date' must use MM-DD-YYYY"
        ) from error

    return parsed.replace(hour=23, minute=59, second=59)


def _safe_reference(path: Path, line_number: int) -> str:
    file_digest = sha256(path.name.encode("utf-8")).hexdigest()[:12]
    return f"ascap-csv:international-incoming:file:{file_digest}:row:{line_number}"


def _deterministic_id(reference: str) -> UUID:
    return uuid5(NAMESPACE_URL, reference)
