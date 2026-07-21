"""Raw evidence source backed by a CSV file."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import UUID

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal

_REQUIRED_FIELDS = frozenset(
    {
        "id",
        "source_name",
        "kind",
        "summary",
        "occurred_at",
        "signals",
    }
)


@dataclass(frozen=True, slots=True)
class CsvRawEvidenceSource:
    """Loads raw evidence records from a CSV file."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load raw evidence records from CSV rows in deterministic order."""

        try:
            with self.path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames

                if fieldnames is None:
                    raise ValueError("Evidence CSV must include a header row")

                missing_fields = _REQUIRED_FIELDS.difference(fieldnames)
                if missing_fields:
                    missing = ", ".join(sorted(missing_fields))
                    raise ValueError(f"Evidence CSV is missing required field(s): {missing}")

                return tuple(
                    _parse_row(cast(dict[str | None, str | None], row), index)
                    for index, row in enumerate(reader, start=2)
                )
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Evidence CSV file not found: {self.path}") from error


def _parse_row(row: dict[str | None, str | None], line_number: int) -> RawEvidenceRecord:
    if None in row:
        raise ValueError(f"Evidence CSV row {line_number} has too many columns")

    id_value = _required(row, "id", line_number)
    source_name = _required(row, "source_name", line_number)
    kind = _required(row, "kind", line_number)
    summary = _required(row, "summary", line_number)
    occurred_at = _required(row, "occurred_at", line_number)
    observed_at = _optional(row, "observed_at")
    reference = _optional(row, "reference")
    signals = row.get("signals") or ""

    return RawEvidenceRecord(
        id=_parse_uuid(id_value, "id", line_number),
        source_name=source_name,
        kind=_parse_evidence_kind(kind, line_number),
        summary=summary,
        observed_at=_parse_optional_datetime(observed_at, "observed_at", line_number),
        occurred_at=_parse_datetime(occurred_at, "occurred_at", line_number),
        reference=reference,
        signals=_parse_signals(signals, line_number),
    )


def _required(row: dict[str | None, str | None], field_name: str, line_number: int) -> str:
    value = row.get(field_name)

    if value is None or not value.strip():
        raise ValueError(f"Evidence CSV row {line_number} is missing field '{field_name}'")

    return value


def _optional(row: dict[str | None, str | None], field_name: str) -> str | None:
    value = row.get(field_name)

    if value is None or not value.strip():
        return None

    return value


def _parse_uuid(value: str, field_name: str, line_number: int) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence CSV row {line_number} field '{field_name}' must be a valid UUID"
        ) from error


def _parse_evidence_kind(value: str, line_number: int) -> EvidenceKind:
    try:
        return EvidenceKind(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence CSV row {line_number} field 'kind' has invalid EvidenceKind: {value}"
        ) from error


def _parse_signals(value: str, line_number: int) -> tuple[EvidenceSignal, ...]:
    signal_values = [signal.strip() for signal in value.split(";") if signal.strip()]

    signals: list[EvidenceSignal] = []

    for signal_index, signal_value in enumerate(signal_values):
        try:
            signals.append(EvidenceSignal(signal_value))
        except ValueError as error:
            raise ValueError(
                "Evidence CSV row "
                f"{line_number} field 'signals[{signal_index}]' has invalid EvidenceSignal: "
                f"{signal_value}"
            ) from error

    return tuple(signals)


def _parse_optional_datetime(
    value: str | None, field_name: str, line_number: int
) -> datetime | None:
    if value is None:
        return None

    return _parse_datetime(value, field_name, line_number)


def _parse_datetime(value: str, field_name: str, line_number: int) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence CSV row {line_number} field '{field_name}' must be an ISO datetime"
        ) from error

    if parsed.tzinfo is None:
        raise ValueError(
            f"Evidence CSV row {line_number} field '{field_name}' must be timezone-aware"
        )

    return parsed
