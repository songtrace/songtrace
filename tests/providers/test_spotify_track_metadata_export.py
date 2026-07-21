"""Tests for exporting Spotify metadata through the raw evidence boundary."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from songtrace.application import EvidenceImporter, JsonRawEvidenceSource
from songtrace.domain.evidence import EvidenceKind
from songtrace.providers import SpotifyTrackMetadata
from songtrace.providers.spotify_track_metadata_export import (
    spotify_track_metadata_raw_record_to_json,
    spotify_track_metadata_raw_records_to_json_text,
    spotify_track_metadata_to_raw_record,
)


def test_spotify_track_metadata_to_raw_record_maps_track_identity_with_isrc() -> None:
    occurred_at = datetime(2026, 7, 21, 12, tzinfo=UTC)
    observed_at = datetime(2026, 7, 21, 12, 5, tzinfo=UTC)

    record = spotify_track_metadata_to_raw_record(
        SpotifyTrackMetadata(
            spotify_track_id="7zHxneKcojYp1eFkGO0e2N",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            album_name="Praises To The War Machine (2021 Extended Edition)",
            isrc="GBDHC2120401",
        ),
        occurred_at=occurred_at,
        observed_at=observed_at,
    )

    assert record.source_name == "spotify"
    assert record.kind is EvidenceKind.OTHER
    assert (
        record.summary == "Spotify track metadata identified Everything Is Fading by Warrel Dane."
    )
    assert record.occurred_at == occurred_at
    assert record.observed_at == observed_at
    assert record.reference == "spotify:track:7zHxneKcojYp1eFkGO0e2N"
    assert record.signals == ()
    assert record.track is not None
    assert record.track.artist == "Warrel Dane"
    assert record.track.title == "Everything Is Fading"
    assert record.track.isrc == "GBDHC2120401"


def test_spotify_track_metadata_to_raw_record_allows_missing_isrc() -> None:
    record = spotify_track_metadata_to_raw_record(
        SpotifyTrackMetadata(
            spotify_track_id="spotify-track-id",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
    )

    assert record.track is not None
    assert record.track.isrc is None


def test_spotify_track_metadata_to_raw_record_uses_deterministic_id() -> None:
    metadata = SpotifyTrackMetadata(
        spotify_track_id="spotify-track-id",
        title="Everything Is Fading",
        artist_names=("Warrel Dane",),
    )
    occurred_at = datetime(2026, 7, 21, 12, tzinfo=UTC)

    first = spotify_track_metadata_to_raw_record(metadata, occurred_at=occurred_at)
    second = spotify_track_metadata_to_raw_record(metadata, occurred_at=occurred_at)

    assert first.id == second.id


def test_spotify_track_metadata_to_raw_record_rejects_naive_timestamps() -> None:
    metadata = SpotifyTrackMetadata(
        spotify_track_id="spotify-track-id",
        title="Everything Is Fading",
        artist_names=("Warrel Dane",),
    )

    with pytest.raises(ValueError, match="occurred_at_must_be_timezone_aware"):
        spotify_track_metadata_to_raw_record(
            metadata,
            occurred_at=datetime(2026, 7, 21, 12),
        )

    with pytest.raises(ValueError, match="observed_at_must_be_timezone_aware"):
        spotify_track_metadata_to_raw_record(
            metadata,
            occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            observed_at=datetime(2026, 7, 21, 12, 5),
        )


def test_spotify_track_metadata_json_is_importable(tmp_path: Path) -> None:
    path = tmp_path / "spotify-track-metadata.json"
    record = spotify_track_metadata_to_raw_record(
        SpotifyTrackMetadata(
            spotify_track_id="7zHxneKcojYp1eFkGO0e2N",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            isrc="GBDHC2120401",
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
    )
    path.write_text(spotify_track_metadata_raw_records_to_json_text((record,)), encoding="utf-8")

    raw_records = JsonRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: datetime(2026, 7, 21, 13, tzinfo=UTC)).import_records(
        raw_records
    )

    assert len(evidence) == 1
    assert evidence[0].kind is EvidenceKind.OTHER
    assert evidence[0].reference == "spotify:track:7zHxneKcojYp1eFkGO0e2N"
    assert evidence[0].track is not None
    assert evidence[0].track.isrc == "GBDHC2120401"


def test_spotify_track_metadata_raw_record_to_json_omits_missing_optional_fields() -> None:
    record = spotify_track_metadata_to_raw_record(
        SpotifyTrackMetadata(
            spotify_track_id="spotify-track-id",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
    )

    payload = spotify_track_metadata_raw_record_to_json(record)

    assert "observed_at" not in payload
    assert "track_isrc" not in payload
    assert json.dumps(payload, sort_keys=True)
