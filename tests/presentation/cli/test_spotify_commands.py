# ruff: noqa: F403,F405
from datetime import UTC, datetime

import pytest

from songtrace.application import EvidenceImporter, JsonRawEvidenceSource
from songtrace.presentation.cli import main as cli_main
from songtrace.providers import (
    SpotifyPlaylistDiscoveryResult,
    SpotifyPlaylistSearchCandidate,
    SpotifyPlaylistSkippedCandidate,
    SpotifyPlaylistTrackMembership,
    SpotifyTrackMetadata,
)
from tests.presentation.cli.fixtures import *


def test_spotify_playlist_search_text_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def discover(
        queries: tuple[str, ...],
        track_id: str,
        *,
        limit: int,
    ) -> SpotifyPlaylistDiscoveryResult:
        assert queries == ("Everything Is Fading", "Warrel Dane")
        assert track_id == "spotify-track-id"
        assert limit == 2
        return _multi_query_discovery_result()

    monkeypatch.setattr(
        cli_main, "discover_spotify_playlist_track_memberships_for_queries", discover
    )

    result = runner.invoke(
        app,
        [
            "spotify-playlist-search",
            "Everything Is Fading",
            "spotify-track-id",
            "--limit",
            "2",
            "--query",
            "Warrel Dane",
        ],
    )

    assert result.exit_code == 0
    assert "SongTrace Spotify Playlist Discovery" in result.stdout
    assert "Queries:" in result.stdout
    assert "- Everything Is Fading" in result.stdout
    assert "- Warrel Dane" in result.stdout
    assert "Candidate playlists: 3" in result.stdout
    assert "Skipped candidates: 1" in result.stdout
    assert "Verified placements: 1" in result.stdout
    assert "contains track yes" in result.stdout
    assert "contains track no" in result.stdout
    assert "Skipped playlists:" in result.stdout
    assert "spotify_playlist_tracks_http_error_403" in result.stdout
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_spotify_playlist_search_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_main,
        "discover_spotify_playlist_track_memberships_for_queries",
        _discovery_result_from_args,
    )

    result = runner.invoke(
        app,
        ["spotify-playlist-search", "Everything Is Fading", "spotify-track-id", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "candidate_count": 2,
        "memberships": [
            {
                "contains_track": True,
                "matched_track_ids": ["spotify-track-id"],
                "playlist_name": "Everything Is Fading Radio",
                "spotify_playlist_id": "playlist-one",
                "spotify_track_id": "spotify-track-id",
            },
            {
                "contains_track": False,
                "matched_track_ids": [],
                "playlist_name": "Dark Metal",
                "spotify_playlist_id": "playlist-two",
                "spotify_track_id": "spotify-track-id",
            },
        ],
        "query": "Everything Is Fading",
        "queries": ["Everything Is Fading"],
        "skipped_candidate_count": 0,
        "skipped_candidates": [],
        "spotify_track_id": "spotify-track-id",
        "verified_placement_count": 1,
    }


def test_spotify_playlist_search_failure_output_is_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def discover(
        _queries: tuple[str, ...],
        _track_id: str,
        *,
        limit: int,
    ) -> SpotifyPlaylistDiscoveryResult:
        raise ValueError("spotify_playlist_search_http_error_429")

    monkeypatch.setattr(
        cli_main, "discover_spotify_playlist_track_memberships_for_queries", discover
    )

    result = runner.invoke(
        app,
        ["spotify-playlist-search", "Everything Is Fading", "spotify-track-id"],
    )

    assert result.exit_code == 1
    assert "spotify_playlist_search_http_error_429" in result.stderr
    assert "SECRET_CLIENT_ID" not in result.stderr
    assert "SECRET_CLIENT_SECRET" not in result.stderr
    assert "SECRET_TOKEN" not in result.stderr
    assert "access_token" not in result.stderr


def test_export_spotify_playlist_search_placements_prints_json_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_main,
        "discover_spotify_playlist_track_memberships_for_queries",
        _discovery_result_from_args,
    )

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-search-placements",
            "Everything Is Fading",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--observed-at",
            "2026-07-21T12:05:00+00:00",
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--track-isrc",
            "GBDHC2120401",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == [
        {
            "id": "a12acb89-be69-553c-89f6-f7ee1731cf0b",
            "kind": "playlist_activity",
            "occurred_at": "2026-07-21T12:00:00+00:00",
            "observed_at": "2026-07-21T12:05:00+00:00",
            "reference": "spotify:playlist:playlist-one:track:spotify-track-id",
            "signals": ["playlist_placement"],
            "source_name": "spotify",
            "summary": (
                "Spotify current playlist membership observed track spotify-track-id "
                "in playlist Everything Is Fading Radio."
            ),
            "track_artist": "Warrel Dane",
            "track_isrc": "GBDHC2120401",
            "track_title": "Everything Is Fading",
        }
    ]


def test_export_spotify_playlist_search_placements_writes_importable_json_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "spotify-playlist-search-placements.json"
    monkeypatch.setattr(
        cli_main,
        "discover_spotify_playlist_track_memberships_for_queries",
        _discovery_result_from_args,
    )

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-search-placements",
            "Everything Is Fading",
            "spotify-track-id",
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
    assert evidence[0].reference == "spotify:playlist:playlist-one:track:spotify-track-id"


def test_export_spotify_playlist_search_placements_rejects_incomplete_track_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[str, ...], str, int]] = []

    def discover(
        queries: tuple[str, ...],
        track_id: str,
        *,
        limit: int,
    ) -> SpotifyPlaylistDiscoveryResult:
        calls.append((queries, track_id, limit))
        return _discovery_result()

    monkeypatch.setattr(
        cli_main, "discover_spotify_playlist_track_memberships_for_queries", discover
    )

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-search-placements",
            "Everything Is Fading",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--track-artist",
            "Warrel Dane",
        ],
    )

    assert result.exit_code == 2
    assert calls == []


def test_export_spotify_playlist_search_placements_allows_no_verified_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_main,
        "discover_spotify_playlist_track_memberships_for_queries",
        _empty_discovery_result_from_args,
    )

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-search-placements",
            "Everything Is Fading",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_export_spotify_playlist_placement_prints_json_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(playlist_id: str, track_id: str) -> SpotifyPlaylistTrackMembership:
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id=playlist_id,
            playlist_name="Metal Essentials",
            spotify_track_id=track_id,
            contains_track=True,
            matched_track_ids=(track_id,),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-placement",
            "playlist-id",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--observed-at",
            "2026-07-21T12:05:00+00:00",
            "--track-artist",
            "Warrel Dane",
            "--track-title",
            "Everything Is Fading",
            "--track-isrc",
            "GBDHC2120401",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == [
        {
            "id": "645f695e-798b-54bd-b84f-750600a96ceb",
            "kind": "playlist_activity",
            "occurred_at": "2026-07-21T12:00:00+00:00",
            "observed_at": "2026-07-21T12:05:00+00:00",
            "reference": "spotify:playlist:playlist-id:track:spotify-track-id",
            "signals": ["playlist_placement"],
            "source_name": "spotify",
            "summary": (
                "Spotify current playlist membership observed track spotify-track-id "
                "in playlist Metal Essentials."
            ),
            "track_artist": "Warrel Dane",
            "track_isrc": "GBDHC2120401",
            "track_title": "Everything Is Fading",
        }
    ]
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_export_spotify_playlist_placement_writes_importable_json_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "spotify-playlist-placement.json"

    def lookup(_playlist_id: str, _track_id: str) -> SpotifyPlaylistTrackMembership:
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            spotify_track_id="spotify-track-id",
            contains_track=True,
            matched_track_ids=("spotify-track-id",),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-placement",
            "playlist-id",
            "spotify-track-id",
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
    assert evidence[0].reference == "spotify:playlist:playlist-id:track:spotify-track-id"


def test_export_spotify_playlist_placement_rejects_incomplete_track_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def lookup(playlist_id: str, track_id: str) -> SpotifyPlaylistTrackMembership:
        calls.append((playlist_id, track_id))
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id=playlist_id,
            spotify_track_id=track_id,
            contains_track=True,
            matched_track_ids=(track_id,),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-placement",
            "playlist-id",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
            "--track-artist",
            "Warrel Dane",
        ],
    )

    assert result.exit_code == 2
    assert calls == []


def test_export_spotify_playlist_placement_membership_not_found_is_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(_playlist_id: str, _track_id: str) -> SpotifyPlaylistTrackMembership:
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            spotify_track_id="spotify-track-id",
            contains_track=False,
            matched_track_ids=(),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        [
            "export-spotify-playlist-placement",
            "playlist-id",
            "spotify-track-id",
            "--occurred-at",
            "2026-07-21T12:00:00+00:00",
        ],
    )

    assert result.exit_code == 1
    assert "spotify_playlist_membership_not_found" in result.stderr
    assert "SECRET_CLIENT_ID" not in result.stderr
    assert "SECRET_CLIENT_SECRET" not in result.stderr
    assert "SECRET_TOKEN" not in result.stderr
    assert "access_token" not in result.stderr


def test_spotify_playlist_track_lookup_text_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(playlist_id: str, track_id: str) -> SpotifyPlaylistTrackMembership:
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id=playlist_id,
            playlist_name="Metal Essentials",
            spotify_track_id=track_id,
            contains_track=True,
            matched_track_ids=(track_id,),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        ["spotify-playlist-track-lookup", "playlist-id", "spotify-track-id"],
    )

    assert result.exit_code == 0
    assert "SongTrace Spotify Playlist Track Lookup" in result.stdout
    assert "Spotify playlist ID: playlist-id" in result.stdout
    assert "Playlist name: Metal Essentials" in result.stdout
    assert "Spotify track ID: spotify-track-id" in result.stdout
    assert "Contains track: yes" in result.stdout
    assert "Matched track IDs: 1" in result.stdout
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_spotify_playlist_track_lookup_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def lookup(_playlist_id: str, _track_id: str) -> SpotifyPlaylistTrackMembership:
        return SpotifyPlaylistTrackMembership(
            spotify_playlist_id="playlist-id",
            playlist_name="Metal Essentials",
            spotify_track_id="spotify-track-id",
            contains_track=False,
            matched_track_ids=(),
        )

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        ["spotify-playlist-track-lookup", "playlist-id", "spotify-track-id", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "contains_track": False,
        "matched_track_ids": [],
        "playlist_name": "Metal Essentials",
        "spotify_playlist_id": "playlist-id",
        "spotify_track_id": "spotify-track-id",
    }
    assert "SECRET" not in result.stdout
    assert "access_token" not in result.stdout


def test_spotify_playlist_track_lookup_failure_output_is_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def lookup(_playlist_id: str, _track_id: str) -> SpotifyPlaylistTrackMembership:
        raise ValueError("spotify_playlist_http_error_404")

    monkeypatch.setattr(cli_main, "lookup_spotify_playlist_track_membership", lookup)

    result = runner.invoke(
        app,
        ["spotify-playlist-track-lookup", "playlist-id", "spotify-track-id"],
    )

    assert result.exit_code == 1
    assert "spotify_playlist_http_error_404" in result.stderr
    assert "SECRET_CLIENT_ID" not in result.stderr
    assert "SECRET_CLIENT_SECRET" not in result.stderr
    assert "SECRET_TOKEN" not in result.stderr
    assert "access_token" not in result.stderr


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


def _discovery_result_from_args(
    _queries: tuple[str, ...],
    _track_id: str,
    *,
    limit: int,
) -> SpotifyPlaylistDiscoveryResult:
    return _discovery_result()


def _empty_discovery_result_from_args(
    _queries: tuple[str, ...],
    _track_id: str,
    *,
    limit: int,
) -> SpotifyPlaylistDiscoveryResult:
    return SpotifyPlaylistDiscoveryResult(
        query="Everything Is Fading",
        spotify_track_id="spotify-track-id",
        candidates=(),
        memberships=(),
    )


def _multi_query_discovery_result() -> SpotifyPlaylistDiscoveryResult:
    return SpotifyPlaylistDiscoveryResult(
        query="Everything Is Fading | Warrel Dane",
        queries=("Everything Is Fading", "Warrel Dane"),
        spotify_track_id="spotify-track-id",
        candidates=(
            *_discovery_result().candidates,
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id="inaccessible-playlist",
                playlist_name="Inaccessible Playlist",
            ),
        ),
        memberships=_discovery_result().memberships,
        skipped_candidates=(
            SpotifyPlaylistSkippedCandidate(
                spotify_playlist_id="inaccessible-playlist",
                playlist_name="Inaccessible Playlist",
                reason="spotify_playlist_tracks_http_error_403",
            ),
        ),
    )


def _discovery_result() -> SpotifyPlaylistDiscoveryResult:
    return SpotifyPlaylistDiscoveryResult(
        query="Everything Is Fading",
        spotify_track_id="spotify-track-id",
        candidates=(
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id="playlist-one",
                playlist_name="Everything Is Fading Radio",
            ),
            SpotifyPlaylistSearchCandidate(
                spotify_playlist_id="playlist-two",
                playlist_name="Dark Metal",
            ),
        ),
        memberships=(
            SpotifyPlaylistTrackMembership(
                spotify_playlist_id="playlist-one",
                playlist_name="Everything Is Fading Radio",
                spotify_track_id="spotify-track-id",
                contains_track=True,
                matched_track_ids=("spotify-track-id",),
            ),
            SpotifyPlaylistTrackMembership(
                spotify_playlist_id="playlist-two",
                playlist_name="Dark Metal",
                spotify_track_id="spotify-track-id",
                contains_track=False,
                matched_track_ids=(),
            ),
        ),
    )
