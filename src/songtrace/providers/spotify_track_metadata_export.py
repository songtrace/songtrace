"""Export Spotify track metadata through the raw evidence boundary."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID, uuid5

from songtrace.application import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind
from songtrace.domain.track import TrackIdentity
from songtrace.providers.spotify_track_lookup import SpotifyTrackMetadata

_SPOTIFY_TRACK_METADATA_NAMESPACE = UUID("00000000-0000-0000-0000-000000000066")


def spotify_track_metadata_to_raw_record(
    metadata: SpotifyTrackMetadata,
    *,
    occurred_at: datetime,
    observed_at: datetime | None = None,
) -> RawEvidenceRecord:
    """Convert safe Spotify track metadata into one provider-neutral raw evidence record."""

    _require_timezone_aware(occurred_at, "occurred_at")
    if observed_at is not None:
        _require_timezone_aware(observed_at, "observed_at")

    primary_artist = metadata.artist_names[0]
    reference = f"spotify:track:{metadata.spotify_track_id}"
    return RawEvidenceRecord(
        id=uuid5(_SPOTIFY_TRACK_METADATA_NAMESPACE, reference),
        source_name="spotify",
        kind=EvidenceKind.OTHER,
        summary=(f"Spotify track metadata identified {metadata.title} by {primary_artist}."),
        occurred_at=occurred_at,
        observed_at=observed_at,
        reference=reference,
        signals=(),
        track=TrackIdentity(
            artist=primary_artist,
            title=metadata.title,
            isrc=metadata.isrc,
        ),
    )


def spotify_track_metadata_raw_record_to_json(record: RawEvidenceRecord) -> dict[str, object]:
    """Serialize a Spotify metadata raw record using JsonRawEvidenceSource fields."""

    payload: dict[str, object] = {
        "id": str(record.id),
        "kind": record.kind.value,
        "summary": record.summary,
        "occurred_at": _required_datetime(record.occurred_at, "occurred_at").isoformat(),
        "source_name": record.source_name,
        "signals": [signal.value for signal in record.signals],
    }
    if record.observed_at is not None:
        payload["observed_at"] = record.observed_at.isoformat()
    if record.reference is not None:
        payload["reference"] = record.reference
    if record.track is not None:
        payload["track_artist"] = record.track.artist
        payload["track_title"] = record.track.title
        if record.track.isrc is not None:
            payload["track_isrc"] = record.track.isrc
    return payload


def spotify_track_metadata_raw_records_to_json_text(records: tuple[RawEvidenceRecord, ...]) -> str:
    """Serialize Spotify metadata raw records as deterministic JSON text."""

    payload = [spotify_track_metadata_raw_record_to_json(record) for record in records]
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _require_timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name}_must_be_timezone_aware"
        raise ValueError(msg)


def _required_datetime(value: datetime | None, field_name: str) -> datetime:
    if value is None:
        msg = f"{field_name}_required"
        raise ValueError(msg)
    return value
