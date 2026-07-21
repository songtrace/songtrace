"""Export Spotify current playlist membership through the raw evidence boundary."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID, uuid5

from songtrace.application import RawEvidenceRecord
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.track import TrackIdentity
from songtrace.providers.spotify_playlist_membership import SpotifyPlaylistTrackMembership

_SPOTIFY_PLAYLIST_PLACEMENT_NAMESPACE = UUID("00000000-0000-0000-0000-000000000068")


def spotify_playlist_membership_to_raw_record(
    membership: SpotifyPlaylistTrackMembership,
    *,
    occurred_at: datetime,
    observed_at: datetime | None = None,
    track: TrackIdentity | None = None,
) -> RawEvidenceRecord:
    """Convert positive current Spotify playlist membership into raw placement evidence."""

    if not membership.contains_track:
        msg = "spotify_playlist_membership_not_found"
        raise ValueError(msg)
    _require_timezone_aware(occurred_at, "occurred_at")
    if observed_at is not None:
        _require_timezone_aware(observed_at, "observed_at")

    reference = (
        f"spotify:playlist:{membership.spotify_playlist_id}:track:{membership.spotify_track_id}"
    )
    playlist_label = membership.playlist_name or membership.spotify_playlist_id
    return RawEvidenceRecord(
        id=uuid5(_SPOTIFY_PLAYLIST_PLACEMENT_NAMESPACE, reference),
        source_name="spotify",
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary=(
            "Spotify current playlist membership observed track "
            f"{membership.spotify_track_id} in playlist {playlist_label}."
        ),
        occurred_at=occurred_at,
        observed_at=observed_at,
        reference=reference,
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        track=track,
    )


def spotify_playlist_placement_raw_record_to_json(record: RawEvidenceRecord) -> dict[str, object]:
    """Serialize a Spotify playlist placement raw record for JsonRawEvidenceSource."""

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


def spotify_playlist_placement_raw_records_to_json_text(
    records: tuple[RawEvidenceRecord, ...],
) -> str:
    """Serialize Spotify playlist placement records as deterministic JSON text."""

    payload = [spotify_playlist_placement_raw_record_to_json(record) for record in records]
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
