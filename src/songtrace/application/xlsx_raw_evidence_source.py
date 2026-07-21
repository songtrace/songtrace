"""Raw evidence source backed by a simple XLSX workbook."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID
from zipfile import BadZipFile, ZipFile

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.track import TrackIdentity

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
_CELL_REFERENCE_PATTERN = re.compile(r"([A-Z]+)")
_SPREADSHEET_NAMESPACE = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


@dataclass(frozen=True, slots=True)
class XlsxRawEvidenceSource:
    """Loads raw evidence records from the first worksheet in an XLSX file."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load raw evidence records from worksheet rows in deterministic order."""

        try:
            with ZipFile(self.path) as workbook:
                shared_strings = _load_shared_strings(workbook)
                rows = _load_sheet_rows(workbook, shared_strings)
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Evidence XLSX file not found: {self.path}") from error
        except (BadZipFile, KeyError, ET.ParseError) as error:
            raise ValueError(f"Evidence XLSX file is invalid: {self.path}") from error

        if not rows:
            raise ValueError("Evidence XLSX must include a header row")

        fieldnames = tuple(value.strip() for value in rows[0])
        if not any(fieldnames):
            raise ValueError("Evidence XLSX must include a header row")

        missing_fields = _REQUIRED_FIELDS.difference(fieldnames)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Evidence XLSX is missing required field(s): {missing}")

        records: list[RawEvidenceRecord] = []
        for row_number, values in enumerate(rows[1:], start=2):
            if not any(value.strip() for value in values):
                continue
            if len(values) > len(fieldnames):
                raise ValueError(f"Evidence XLSX row {row_number} has too many cells")

            row = dict(zip(fieldnames, values, strict=False))
            records.append(_parse_row(row, row_number))

        return tuple(records)


def _load_shared_strings(workbook: ZipFile) -> tuple[str, ...]:
    try:
        content = workbook.read("xl/sharedStrings.xml")
    except KeyError:
        return ()

    root = ET.fromstring(content)
    strings: list[str] = []
    for item in root.findall(f"{_SPREADSHEET_NAMESPACE}si"):
        text_parts = [text.text or "" for text in item.iter(f"{_SPREADSHEET_NAMESPACE}t")]
        strings.append("".join(text_parts))

    return tuple(strings)


def _load_sheet_rows(
    workbook: ZipFile, shared_strings: tuple[str, ...]
) -> tuple[tuple[str, ...], ...]:
    content = workbook.read("xl/worksheets/sheet1.xml")
    root = ET.fromstring(content)
    rows: list[tuple[str, ...]] = []

    for row in root.iter(f"{_SPREADSHEET_NAMESPACE}row"):
        values_by_index: dict[int, str] = {}
        for cell in row.findall(f"{_SPREADSHEET_NAMESPACE}c"):
            index = _cell_column_index(cell.attrib.get("r"))
            values_by_index[index] = _cell_value(cell, shared_strings)

        if values_by_index:
            max_index = max(values_by_index)
            rows.append(tuple(values_by_index.get(index, "") for index in range(max_index + 1)))
        else:
            rows.append(())

    return tuple(rows)


def _cell_column_index(reference: str | None) -> int:
    if reference is None:
        return 0

    match = _CELL_REFERENCE_PATTERN.match(reference)
    if match is None:
        return 0

    index = 0
    for letter in match.group(1):
        index = index * 26 + (ord(letter) - ord("A") + 1)

    return index - 1


def _cell_value(cell: ET.Element, shared_strings: tuple[str, ...]) -> str:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.iter(f"{_SPREADSHEET_NAMESPACE}t"))

    value = cell.find(f"{_SPREADSHEET_NAMESPACE}v")
    if value is None or value.text is None:
        return ""

    if cell_type == "s":
        try:
            return shared_strings[int(value.text)]
        except (IndexError, ValueError) as error:
            raise ValueError("Evidence XLSX contains an invalid shared string reference") from error

    return value.text


def _parse_row(row: dict[str, str], row_number: int) -> RawEvidenceRecord:
    id_value = _required(row, "id", row_number)
    source_name = _required(row, "source_name", row_number)
    kind = _required(row, "kind", row_number)
    summary = _required(row, "summary", row_number)
    occurred_at = _required(row, "occurred_at", row_number)
    observed_at = _optional(row, "observed_at")
    reference = _optional(row, "reference")
    signals = row.get("signals") or ""
    track = _parse_optional_track(row, row_number)

    return RawEvidenceRecord(
        id=_parse_uuid(id_value, "id", row_number),
        source_name=source_name,
        kind=_parse_evidence_kind(kind, row_number),
        summary=summary,
        observed_at=_parse_optional_datetime(observed_at, "observed_at", row_number),
        occurred_at=_parse_datetime(occurred_at, "occurred_at", row_number),
        reference=reference,
        signals=_parse_signals(signals, row_number),
        track=track,
    )


def _required(row: dict[str, str], field_name: str, row_number: int) -> str:
    value = row.get(field_name)

    if value is None or not value.strip():
        raise ValueError(f"Evidence XLSX row {row_number} is missing field '{field_name}'")

    return value


def _optional(row: dict[str, str], field_name: str) -> str | None:
    value = row.get(field_name)

    if value is None or not value.strip():
        return None

    return value


def _parse_uuid(value: str, field_name: str, row_number: int) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence XLSX row {row_number} field '{field_name}' must be a valid UUID"
        ) from error


def _parse_evidence_kind(value: str, row_number: int) -> EvidenceKind:
    try:
        return EvidenceKind(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence XLSX row {row_number} field 'kind' has invalid EvidenceKind: {value}"
        ) from error


def _parse_optional_track(row: dict[str, str], row_number: int) -> TrackIdentity | None:
    artist = _optional(row, "track_artist")
    title = _optional(row, "track_title")
    isrc = _optional(row, "track_isrc")

    if artist is None and title is None and isrc is None:
        return None

    if artist is None:
        raise ValueError(
            f"Evidence XLSX row {row_number} field 'track_artist' is required "
            "when track identity is supplied"
        )
    if title is None:
        raise ValueError(
            f"Evidence XLSX row {row_number} field 'track_title' is required "
            "when track identity is supplied"
        )

    return TrackIdentity(artist=artist, title=title, isrc=isrc)


def _parse_signals(value: str, row_number: int) -> tuple[EvidenceSignal, ...]:
    signal_values = [signal.strip() for signal in value.split(";") if signal.strip()]

    signals: list[EvidenceSignal] = []
    for signal_index, signal_value in enumerate(signal_values):
        try:
            signals.append(EvidenceSignal(signal_value))
        except ValueError as error:
            raise ValueError(
                "Evidence XLSX row "
                f"{row_number} field 'signals[{signal_index}]' has invalid EvidenceSignal: "
                f"{signal_value}"
            ) from error

    return tuple(signals)


def _parse_optional_datetime(
    value: str | None, field_name: str, row_number: int
) -> datetime | None:
    if value is None:
        return None

    return _parse_datetime(value, field_name, row_number)


def _parse_datetime(value: str, field_name: str, row_number: int) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"Evidence XLSX row {row_number} field '{field_name}' must be an ISO datetime"
        ) from error

    if parsed.tzinfo is None:
        raise ValueError(
            f"Evidence XLSX row {row_number} field '{field_name}' must be timezone-aware"
        )

    return parsed
