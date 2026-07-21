"""Tests for loading platform activity raw evidence from CSV files."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application import EvidenceImporter, ObservationExtractor
from songtrace.application.platform_activity_csv_raw_evidence_source import (
    PlatformActivityCsvRawEvidenceSource,
)
from songtrace.application.playlist_placement_csv_raw_evidence_source import (
    PlaylistPlacementCsvRawEvidenceSource,
)
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.observation import ObservationKind

_COLUMNS = (
    "id",
    "source_name",
    "summary",
    "occurred_at",
    "observed_at",
    "reference",
    "signal",
)


def test_loads_stream_growth_rows_as_raw_evidence_records(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(), _row(id="00000000-0000-0000-0000-000000000502")])
    source: RawEvidenceSource = PlatformActivityCsvRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 2
    assert records[0].id == UUID("00000000-0000-0000-0000-000000000501")
    assert records[0].source_name == "spotify"
    assert records[0].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert records[0].summary == "Streams increased after playlist activity."
    assert records[0].signals == (EvidenceSignal.STREAM_GROWTH,)
    assert records[0].occurred_at == datetime(2026, 1, 18, 12, 0, tzinfo=UTC)
    assert records[0].observed_at is None
    assert records[0].reference == "spotify-analytics:streams-week-2026-01-18"


def test_loads_save_growth_signal(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(
        path,
        [
            _row(
                summary="Saves increased after playlist activity.",
                reference="spotify-analytics:saves-week-2026-01-18",
                signal="save_growth",
            )
        ],
    )

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert records[0].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert records[0].signals == (EvidenceSignal.SAVE_GROWTH,)


def test_preserves_record_order(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(
        path,
        [
            _row(id="00000000-0000-0000-0000-000000000501"),
            _row(id="00000000-0000-0000-0000-000000000502"),
            _row(id="00000000-0000-0000-0000-000000000503"),
        ],
    )

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert tuple(record.id for record in records) == (
        UUID("00000000-0000-0000-0000-000000000501"),
        UUID("00000000-0000-0000-0000-000000000502"),
        UUID("00000000-0000-0000-0000-000000000503"),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row()])

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_parses_optional_observed_at(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(observed_at="2026-01-19T12:00:00+00:00")])

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert records[0].observed_at == datetime(2026, 1, 19, 12, 0, tzinfo=UTC)


def test_current_csv_shape_remains_valid_without_track_identity(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row()])

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert records[0].track is None


def test_parses_optional_track_identity(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    columns = (*_COLUMNS, "track_artist", "track_title", "track_isrc")
    _write_table(
        path,
        columns,
        [
            _row(
                track_artist="Warrel Dane",
                track_title="Everything Is Fading",
                track_isrc="USABC0800001",
            )
        ],
    )

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert records[0].track is not None
    assert records[0].track.artist == "Warrel Dane"
    assert records[0].track.title == "Everything Is Fading"
    assert records[0].track.isrc == "USABC0800001"


def test_missing_track_artist_fails_when_track_identity_is_supplied(
    tmp_path: Path,
) -> None:
    path = tmp_path / "platform-activity.csv"
    columns = (*_COLUMNS, "track_artist", "track_title", "track_isrc")
    _write_table(path, columns, [_row(track_artist="", track_title="Everything Is Fading")])

    with pytest.raises(ValueError, match="field 'track_artist' is required"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_blank_track_isrc_is_ignored_as_absent(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    columns = (*_COLUMNS, "track_artist", "track_title", "track_isrc")
    _write_table(
        path,
        columns,
        [_row(track_artist="Warrel Dane", track_title="Everything Is Fading", track_isrc="")],
    )

    records = PlatformActivityCsvRawEvidenceSource(path).load()

    assert records[0].track is not None
    assert records[0].track.isrc is None


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Platform activity CSV file not found"):
        PlatformActivityCsvRawEvidenceSource(tmp_path / "missing.csv").load()


def test_missing_header_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="must include a header row"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_missing_required_column_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    columns = tuple(column for column in _COLUMNS if column != "signal")
    row = _row()
    del row["signal"]
    _write_table(path, columns, [row])

    with pytest.raises(ValueError, match="signal"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_missing_required_row_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(reference="")])

    with pytest.raises(ValueError, match="missing field 'reference'"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_too_many_columns_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    path.write_text(
        ",".join(_COLUMNS) + "\n" + ",".join(_row().values()) + ",extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too many columns"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_invalid_uuid_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(id="not-a-uuid")])

    with pytest.raises(ValueError, match="must be a valid UUID"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_invalid_signal_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(signal="not_a_signal")])

    with pytest.raises(ValueError, match="invalid EvidenceSignal"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_unsupported_signal_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(signal="playlist_placement")])

    with pytest.raises(ValueError, match="must be one of"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_invalid_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(occurred_at="not-a-datetime")])

    with pytest.raises(ValueError, match="must be an ISO datetime"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_naive_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(occurred_at="2026-01-18T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_naive_observed_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(observed_at="2026-01-19T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row(), _row(id="not-a-uuid")])

    with pytest.raises(ValueError, match="must be a valid UUID"):
        PlatformActivityCsvRawEvidenceSource(path).load()


def test_loaded_records_are_compatible_with_evidence_importer(tmp_path: Path) -> None:
    path = tmp_path / "platform-activity.csv"
    _write_csv(path, [_row()])
    fallback_observed_at = datetime(2026, 1, 19, 12, 0, tzinfo=UTC)

    records = PlatformActivityCsvRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: fallback_observed_at).import_records(records)

    assert len(evidence) == 1
    assert evidence[0].id == records[0].id
    assert evidence[0].kind is EvidenceKind.AUDIENCE_ACTIVITY
    assert evidence[0].signals == (EvidenceSignal.STREAM_GROWTH,)
    assert evidence[0].observed_at == fallback_observed_at


def test_imported_platform_activity_evidence_preserves_track_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "platform-activity.csv"
    columns = (*_COLUMNS, "track_artist", "track_title", "track_isrc")
    _write_table(
        path,
        columns,
        [
            _row(
                track_artist="Warrel Dane",
                track_title="Everything Is Fading",
                track_isrc="USABC0800001",
            )
        ],
    )

    records = PlatformActivityCsvRawEvidenceSource(path).load()
    evidence = EvidenceImporter(
        clock=lambda: datetime(2026, 1, 19, 12, 0, tzinfo=UTC)
    ).import_records(records)

    assert evidence[0].track is not None
    assert evidence[0].track.artist == "Warrel Dane"
    assert evidence[0].track.title == "Everything Is Fading"
    assert evidence[0].track.isrc == "USABC0800001"


def test_platform_activity_records_can_support_existing_playlist_observations(
    tmp_path: Path,
) -> None:
    playlist_path = tmp_path / "playlist-placements.csv"
    platform_path = tmp_path / "platform-activity.csv"
    _write_table(
        playlist_path,
        ("id", "source_name", "summary", "occurred_at", "observed_at", "reference"),
        [
            {
                "id": "00000000-0000-0000-0000-000000000301",
                "source_name": "spotify",
                "summary": "Everything Is Fading was added to a playlist.",
                "occurred_at": "2026-01-15T12:00:00+00:00",
                "observed_at": "",
                "reference": "spotify-playlist:example-playlist",
            }
        ],
    )
    _write_csv(
        platform_path,
        [
            _row(id="00000000-0000-0000-0000-000000000501"),
            _row(
                id="00000000-0000-0000-0000-000000000502",
                summary="Saves increased after playlist activity.",
                reference="spotify-analytics:saves-week-2026-01-18",
                signal="save_growth",
            ),
        ],
    )
    observed_at = datetime(2026, 1, 20, 12, 0, tzinfo=UTC)

    raw_records = (
        *PlaylistPlacementCsvRawEvidenceSource(playlist_path).load(),
        *PlatformActivityCsvRawEvidenceSource(platform_path).load(),
    )
    evidence = EvidenceImporter(clock=lambda: observed_at).import_records(raw_records)
    observations = ObservationExtractor(clock=lambda: observed_at).extract(evidence)

    assert tuple(observation.kind for observation in observations) == (
        ObservationKind.PLAYLIST_STREAM_GROWTH,
        ObservationKind.PLAYLIST_SAVE_GROWTH,
    )
    assert observations[0].supporting_evidence_ids == (evidence[0].id, evidence[1].id)
    assert observations[1].supporting_evidence_ids == (evidence[0].id, evidence[2].id)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    _write_table(path, _COLUMNS, rows)


def _write_table(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows([row[column] for column in columns] for row in rows)


def _row(
    *,
    id: str = "00000000-0000-0000-0000-000000000501",
    source_name: str = "spotify",
    summary: str = "Streams increased after playlist activity.",
    occurred_at: str = "2026-01-18T12:00:00+00:00",
    observed_at: str = "",
    reference: str = "spotify-analytics:streams-week-2026-01-18",
    signal: str = "stream_growth",
    track_artist: str = "",
    track_title: str = "",
    track_isrc: str = "",
) -> dict[str, str]:
    return {
        "id": id,
        "source_name": source_name,
        "summary": summary,
        "occurred_at": occurred_at,
        "observed_at": observed_at,
        "reference": reference,
        "signal": signal,
        "track_artist": track_artist,
        "track_title": track_title,
        "track_isrc": track_isrc,
    }
