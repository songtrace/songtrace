"""Tests for exporting Spotify playlist placement through the raw evidence boundary."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from songtrace.application import EvidenceImporter, JsonRawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.track import TrackIdentity
from songtrace.providers import SpotifyPlaylistTrackMembership
from songtrace.providers.spotify_playlist_placement_export import (
    spotify_playlist_membership_to_raw_record,
    spotify_playlist_placement_raw_record_to_json,
    spotify_playlist_placement_raw_records_to_json_text,
)


def test_spotify_playlist_membership_to_raw_record_maps_positive_membership() -> None:
    occurred_at = datetime(2026, 7, 21, 12, tzinfo=UTC)
    observed_at = datetime(2026, 7, 21, 12, 5, tzinfo=UTC)

    record = spotify_playlist_membership_to_raw_record(
        SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            playlist_name="Metal Essentials",
            spotify_track_id="spotify-track-id",
            contains_track=True,
            matched_track_ids=("spotify-track-id",),
        ),
        occurred_at=occurred_at,
        observed_at=observed_at,
    )

    assert record.source_name == "spotify"
    assert record.kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert record.signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert record.occurred_at == occurred_at
    assert record.observed_at == observed_at
    assert record.reference == "spotify:playlist:playlist-id:track:spotify-track-id"
    assert record.summary == (
        "Spotify current playlist membership observed track spotify-track-id "
        "in playlist Metal Essentials."
    )


def test_spotify_playlist_membership_to_raw_record_rejects_negative_membership() -> None:
    with pytest.raises(ValueError, match="spotify_playlist_membership_not_found"):
        spotify_playlist_membership_to_raw_record(
            SpotifyPlaylistTrackMembership(
                spotify_playlist_id="playlist-id",
                spotify_track_id="spotify-track-id",
                contains_track=False,
                matched_track_ids=(),
            ),
            occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        )


def test_spotify_playlist_membership_to_raw_record_maps_track_identity() -> None:
    track = TrackIdentity(
        artist="Warrel Dane",
        title="Everything Is Fading",
        isrc="GBDHC2120401",
    )

    record = spotify_playlist_membership_to_raw_record(
        SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            spotify_track_id="spotify-track-id",
            contains_track=True,
            matched_track_ids=("spotify-track-id",),
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        track=track,
    )

    assert record.track == track


def test_spotify_playlist_membership_to_raw_record_uses_deterministic_id() -> None:
    membership = SpotifyPlaylistTrackMembership(
        spotify_playlist_id="playlist-id",
        spotify_track_id="spotify-track-id",
        contains_track=True,
        matched_track_ids=("spotify-track-id",),
    )
    occurred_at = datetime(2026, 7, 21, 12, tzinfo=UTC)

    first = spotify_playlist_membership_to_raw_record(membership, occurred_at=occurred_at)
    second = spotify_playlist_membership_to_raw_record(membership, occurred_at=occurred_at)

    assert first.id == second.id


def test_spotify_playlist_membership_to_raw_record_rejects_naive_timestamps() -> None:
    membership = SpotifyPlaylistTrackMembership(
        spotify_playlist_id="playlist-id",
        spotify_track_id="spotify-track-id",
        contains_track=True,
        matched_track_ids=("spotify-track-id",),
    )

    with pytest.raises(ValueError, match="occurred_at_must_be_timezone_aware"):
        spotify_playlist_membership_to_raw_record(
            membership,
            occurred_at=datetime(2026, 7, 21, 12),
        )

    with pytest.raises(ValueError, match="observed_at_must_be_timezone_aware"):
        spotify_playlist_membership_to_raw_record(
            membership,
            occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            observed_at=datetime(2026, 7, 21, 12, 5),
        )


def test_spotify_playlist_placement_json_is_importable(tmp_path: Path) -> None:
    path = tmp_path / "spotify-playlist-placement.json"
    record = spotify_playlist_membership_to_raw_record(
        SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            spotify_track_id="spotify-track-id",
            contains_track=True,
            matched_track_ids=("spotify-track-id",),
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        track=TrackIdentity(
            artist="Warrel Dane",
            title="Everything Is Fading",
            isrc="GBDHC2120401",
        ),
    )
    path.write_text(
        spotify_playlist_placement_raw_records_to_json_text((record,)),
        encoding="utf-8",
    )

    raw_records = JsonRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: datetime(2026, 7, 21, 13, tzinfo=UTC)).import_records(
        raw_records
    )

    assert len(evidence) == 1
    assert evidence[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert evidence[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert evidence[0].reference == "spotify:playlist:playlist-id:track:spotify-track-id"
    assert evidence[0].track is not None
    assert evidence[0].track.isrc == "GBDHC2120401"


def test_spotify_playlist_placement_raw_record_to_json_omits_missing_optional_fields() -> None:
    record = spotify_playlist_membership_to_raw_record(
        SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            spotify_track_id="spotify-track-id",
            contains_track=True,
            matched_track_ids=("spotify-track-id",),
        ),
        occurred_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
    )

    payload = spotify_playlist_placement_raw_record_to_json(record)

    assert "observed_at" not in payload
    assert "track_artist" not in payload
    assert json.dumps(payload, sort_keys=True)
