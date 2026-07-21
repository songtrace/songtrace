# ruff: noqa: F403,F405
from datetime import UTC, datetime

import pytest

from songtrace.application import EvidenceImporter, JsonRawEvidenceSource
from songtrace.presentation.cli import main as cli_main
from songtrace.providers import SpotifyTrackMetadata
from tests.presentation.cli.fixtures import *


def test_export_spotify_track_metadata_prints_json_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(spotify_track_id: str) -> SpotifyTrackMetadata:
        return SpotifyTrackMetadata(
            spotify_track_id=spotify_track_id,
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            album_name="Praises To The War Machine (2021 Extended Edition)",
            isrc="GBDHC2120401",
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-track-metadata",
            "7zHxneKcojYp1eFkGO0e2N",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--observed-at",
            "2026-07-21T12:05:00+00:00",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == [
        {
            "id": "2fb34f30-98de-5282-8e20-68a858c8d3d4",
            "kind": "other",
            "occurred_at": "2026-07-21T12:00:00+00:00",
            "observed_at": "2026-07-21T12:05:00+00:00",
            "reference": "spotify:track:7zHxneKcojYp1eFkGO0e2N",
            "signals": [],
            "source_name": "spotify",
            "summary": "Spotify track metadata identified Everything Is Fading by Warrel Dane.",
            "track_artist": "Warrel Dane",
            "track_isrc": "GBDHC2120401",
            "track_title": "Everything Is Fading",
        }
    ]
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_export_spotify_track_metadata_writes_importable_json_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "spotify-track-metadata.json"

    def lookup(_spotify_track_id: str) -> SpotifyTrackMetadata:
        return SpotifyTrackMetadata(
            spotify_track_id="7zHxneKcojYp1eFkGO0e2N",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            isrc="GBDHC2120401",
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-track-metadata",
            "7zHxneKcojYp1eFkGO0e2N",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    raw_records = JsonRawEvidenceSource(output_file).load()
    evidence = EvidenceImporter(clock=lambda: datetime(2026, 7, 21, 13, tzinfo=UTC)).import_records(
        raw_records
    )
    assert len(evidence) == 1
    assert evidence[0].reference == "spotify:track:7zHxneKcojYp1eFkGO0e2N"
    assert evidence[0].track is not None
    assert evidence[0].track.isrc == "GBDHC2120401"


def test_export_spotify_track_metadata_rejects_naive_occurred_at() -> None:
    result = runner.invoke(
        app,
        [
            "export-spotify-track-metadata",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00",
        ],
    )

    assert result.exit_code == 2
    assert "occurred_at must be timezone-aware" in result.stderr


def test_export_spotify_track_metadata_rejects_naive_observed_at() -> None:
    result = runner.invoke(
        app,
        [
            "export-spotify-track-metadata",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--observed-at",
            "2026-07-21T12:05:00",
        ],
    )

    assert result.exit_code == 2
    assert "observed_at must be timezone-aware" in result.stderr


def test_export_spotify_track_metadata_lookup_failure_is_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(_spotify_track_id: str) -> SpotifyTrackMetadata:
        raise ValueError("spotify_track_http_error_404")

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-track-metadata",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
        ],
    )

    assert result.exit_code == 1
    assert "spotify_track_http_error_404" in result.stderr
    assert "SECRET_CLIENT_ID" not in result.stderr
    assert "SECRET_CLIENT_SECRET" not in result.stderr
    assert "SECRET_TOKEN" not in result.stderr
    assert "access_token" not in result.stderr


def test_spotify_track_lookup_text_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(spotify_track_id: str) -> SpotifyTrackMetadata:
        return SpotifyTrackMetadata(
            spotify_track_id=spotify_track_id,
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            album_name="Praises to the War Machine",
            isrc="USABC0800001",
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(app, ["spotify-track-lookup", "spotify-track-id"])

    assert result.exit_code == 0
    assert "SongTrace Spotify Track Lookup" in result.stdout
    assert "Spotify track ID: spotify-track-id" in result.stdout
    assert "Title: Everything Is Fading" in result.stdout
    assert "Artists: Warrel Dane" in result.stdout
    assert "Album: Praises to the War Machine" in result.stdout
    assert "ISRC: USABC0800001" in result.stdout
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_spotify_track_lookup_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(_spotify_track_id: str) -> SpotifyTrackMetadata:
        return SpotifyTrackMetadata(
            spotify_track_id="spotify-track-id",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            album_name="Praises to the War Machine",
            isrc="USABC0800001",
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(
        app,
        ["spotify-track-lookup", "spotify-track-id", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "album_name": "Praises to the War Machine",
        "artist_names": ["Warrel Dane"],
        "isrc": "USABC0800001",
        "spotify_track_id": "spotify-track-id",
        "title": "Everything Is Fading",
    }
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_spotify_track_lookup_json_output_allows_missing_isrc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(_spotify_track_id: str) -> SpotifyTrackMetadata:
        return SpotifyTrackMetadata(
            spotify_track_id="spotify-track-id",
            title="Everything Is Fading",
            artist_names=("Warrel Dane",),
            album_name=None,
            isrc=None,
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(
        app,
        ["spotify-track-lookup", "spotify-track-id", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["album_name"] is None
    assert payload["isrc"] is None


def test_spotify_track_lookup_blank_track_id_fails_before_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def lookup(spotify_track_id: str) -> SpotifyTrackMetadata:
        calls.append(spotify_track_id)
        raise ValueError("spotify_track_id_required")

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(app, ["spotify-track-lookup", " "])

    assert result.exit_code == 1
    assert "spotify_track_id_required" in result.stderr
    assert calls == [" "]


def test_spotify_track_lookup_failure_output_is_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(_spotify_track_id: str) -> SpotifyTrackMetadata:
        raise ValueError("spotify_track_http_error_404")

    monkeypatch.setattr(cli_main, "lookup_spotify_track_metadata", lookup)

    result = runner.invoke(app, ["spotify-track-lookup", "spotify-track-id"])

    assert result.exit_code == 1
    assert "spotify_track_http_error_404" in result.stderr
    assert "SECRET_CLIENT_ID" not in result.stderr
    assert "SECRET_CLIENT_SECRET" not in result.stderr
    assert "SECRET_TOKEN" not in result.stderr
    assert "access_token" not in result.stderr
