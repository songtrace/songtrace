"""Raw evidence source backed by a JSON file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import UUID

from songtrace.application.raw_evidence_record import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.track import TrackIdentity


@dataclass(frozen=True, slots=True)
class JsonRawEvidenceSource:
    """Loads raw evidence records from a JSON file."""

    path: Path

    def load(self) -> tuple[RawEvidenceRecord, ...]:
        """Load raw evidence records from a JSON array in deterministic order."""

        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Evidence JSON file not found: {self.path}") from error

        try:
            payload: object = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"Evidence JSON is invalid: {error.msg}") from error

        if not isinstance(payload, list):
            raise ValueError("Evidence JSON top-level value must be an array")

        items = cast(list[object], payload)

        return tuple(_parse_record(item, index) for index, item in enumerate(items))


def _parse_record(item: object, index: int) -> RawEvidenceRecord:
    if not isinstance(item, dict):
        raise ValueError(f"Evidence JSON item at index {index} must be an object")

    record = cast(dict[str, object], item)
    id_value = _required(record, "id", index)
    source_name = _required(record, "source_name", index)
    kind = _required(record, "kind", index)
    summary = _required(record, "summary", index)
    occurred_at = _required(record, "occurred_at", index)
    observed_at = record.get("observed_at")
    signals = _required(record, "signals", index)

    return RawEvidenceRecord(
        id=_parse_uuid(id_value, "id", index),
        source_name=_parse_string(source_name, "source_name", index),
        kind=_parse_evidence_kind(kind, index),
        summary=_parse_string(summary, "summary", index),
        observed_at=_parse_optional_datetime(observed_at, "observed_at", index),
        occurred_at=_parse_datetime(occurred_at, "occurred_at", index),
        reference=_parse_optional_string(record.get("reference"), "reference", index),
        signals=_parse_signals(signals, index),
        track=_parse_optional_track(record, index),
    )


def _required(record: dict[str, object], field_name: str, index: int) -> object:
    if field_name not in record:
        raise ValueError(f"Evidence JSON item at index {index} is missing field '{field_name}'")

    return record[field_name]


def _parse_uuid(value: object, field_name: str, index: int) -> UUID:
    text = _parse_string(value, field_name, index)

    try:
        return UUID(text)
    except ValueError as error:
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must be a valid UUID"
        ) from error


def _parse_string(value: object, field_name: str, index: int) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must be a string"
        )

    return value


def _parse_optional_string(value: object, field_name: str, index: int) -> str | None:
    if value is None:
        return None

    return _parse_string(value, field_name, index)


def _parse_optional_track(record: dict[str, object], index: int) -> TrackIdentity | None:
    artist = record.get("track_artist")
    title = record.get("track_title")
    isrc = record.get("track_isrc")

    if artist is None and title is None and isrc is None:
        return None

    return TrackIdentity(
        artist=_parse_required_track_string(artist, "track_artist", index),
        title=_parse_required_track_string(title, "track_title", index),
        isrc=_parse_optional_track_string(isrc, "track_isrc", index),
    )


def _parse_required_track_string(value: object, field_name: str, index: int) -> str:
    text = _parse_string(value, field_name, index)
    if not text.strip():
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must not be blank"
        )
    return text


def _parse_optional_track_string(value: object, field_name: str, index: int) -> str | None:
    if value is None:
        return None

    text = _parse_string(value, field_name, index)
    if not text.strip():
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must not be blank"
        )
    return text


def _parse_evidence_kind(value: object, index: int) -> EvidenceKind:
    text = _parse_string(value, "kind", index)

    try:
        return EvidenceKind(text)
    except ValueError as error:
        raise ValueError(
            f"Evidence JSON item at index {index} field 'kind' has invalid EvidenceKind: {text}"
        ) from error


def _parse_signals(value: object, index: int) -> tuple[EvidenceSignal, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Evidence JSON item at index {index} field 'signals' must be an array")

    signal_values = cast(list[object], value)
    signals: list[EvidenceSignal] = []

    for signal_index, signal_value in enumerate(signal_values):
        text = _parse_string(signal_value, f"signals[{signal_index}]", index)

        try:
            signals.append(EvidenceSignal(text))
        except ValueError as error:
            raise ValueError(
                "Evidence JSON item at index "
                f"{index} field 'signals[{signal_index}]' has invalid EvidenceSignal: {text}"
            ) from error

    return tuple(signals)


def _parse_optional_datetime(value: object, field_name: str, index: int) -> datetime | None:
    if value is None:
        return None

    return _parse_datetime(value, field_name, index)


def _parse_datetime(value: object, field_name: str, index: int) -> datetime:
    text = _parse_string(value, field_name, index)

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must be an ISO datetime"
        ) from error

    if parsed.tzinfo is None:
        raise ValueError(
            f"Evidence JSON item at index {index} field '{field_name}' must be timezone-aware"
        )

    return parsed
