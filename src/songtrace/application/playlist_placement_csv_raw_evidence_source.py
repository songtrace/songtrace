"""Raw evidence source for local playlist placement CSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.track import TrackIdentity

_REQUIRED_FIELDS = frozenset(
    {
        "id",
        "source_name",
        "summary",
        "occurred_at",
        "reference",
    }
)


@dataclass(frozen=True, slots=True)
class PlaylistPlacementCsvRawEvidenceSource:
    """Loads provider-neutral playlist placement raw evidence from a local CSV file."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load playlist placement records from CSV rows in deterministic order."""

        try:
            with self.path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames

                if fieldnames is None:
                    raise ValueError("Playlist placement CSV must include a header row")

                missing_fields = _REQUIRED_FIELDS.difference(fieldnames)
                if missing_fields:
                    missing = ", ".join(sorted(missing_fields))
                    raise ValueError(
                        f"Playlist placement CSV is missing required field(s): {missing}"
                    )

                return tuple(
                    _parse_row(row, line_number) for line_number, row in enumerate(reader, start=2)
                )
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Playlist placement CSV file not found: {self.path}"
            ) from error


def _parse_row(row: dict[str | None, str | None], line_number: int) -> RawEvidenceRecord:
    if None in row:
        raise ValueError(f"Playlist placement CSV row {line_number} has too many columns")

    id_value = _required(row, "id", line_number)
    source_name = _required(row, "source_name", line_number)
    summary = _required(row, "summary", line_number)
    occurred_at = _required(row, "occurred_at", line_number)
    reference = _required(row, "reference", line_number)
    observed_at = _optional(row, "observed_at")
    track = _parse_optional_track(row, line_number)

    return RawEvidenceRecord(
        id=_parse_uuid(id_value, "id", line_number),
        source_name=source_name,
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary=summary,
        observed_at=_parse_optional_datetime(observed_at, "observed_at", line_number),
        occurred_at=_parse_datetime(occurred_at, "occurred_at", line_number),
        reference=reference,
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        track=track,
    )


def _required(row: dict[str | None, str | None], field_name: str, line_number: int) -> str:
    value = row.get(field_name)
    if value is None or not value.strip():
        raise ValueError(
            f"Playlist placement CSV row {line_number} is missing field '{field_name}'"
        )
    return value.strip()


def _optional(row: dict[str | None, str | None], field_name: str) -> str | None:
    value = row.get(field_name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _parse_uuid(value: str, field_name: str, line_number: int) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise ValueError(
            f"Playlist placement CSV row {line_number} field '{field_name}' must be a valid UUID"
        ) from error


def _parse_optional_track(
    row: dict[str | None, str | None], line_number: int
) -> TrackIdentity | None:
    artist = _optional(row, "track_artist")
    title = _optional(row, "track_title")
    isrc = _optional(row, "track_isrc")

    if artist is None and title is None and isrc is None:
        return None

    if artist is None:
        raise ValueError(
            f"Playlist placement CSV row {line_number} field 'track_artist' is required "
            "when track identity is supplied"
        )
    if title is None:
        raise ValueError(
            f"Playlist placement CSV row {line_number} field 'track_title' is required "
            "when track identity is supplied"
        )

    return TrackIdentity(artist=artist, title=title, isrc=isrc)


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
            f"Playlist placement CSV row {line_number} field '{field_name}' must be an ISO datetime"
        ) from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"Playlist placement CSV row {line_number} field '{field_name}' must be timezone-aware"
        )

    return parsed
