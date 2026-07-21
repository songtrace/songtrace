"""Tests for loading playlist placement raw evidence from CSV files."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application import EvidenceImporter, ObservationExtractor
from songtrace.application.playlist_placement_csv_raw_evidence_source import (
    PlaylistPlacementCsvRawEvidenceSource,
)
from songtrace.application.raw_evidence_record import RawEvidenceRecord
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
)


def test_loads_playlist_placement_rows_as_raw_evidence_records(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(), _row(id="00000000-0000-0000-0000-000000000302")])
    source: RawEvidenceSource = PlaylistPlacementCsvRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 2
    assert records[0].id == UUID("00000000-0000-0000-0000-000000000301")
    assert records[0].source_name == "spotify"
    assert records[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert records[0].summary == "Everything Is Fading was added to a playlist."
    assert records[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert records[0].occurred_at == datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    assert records[0].observed_at is None
    assert records[0].reference == "spotify-playlist:example-playlist"


def test_preserves_record_order(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(
        path,
        [
            _row(id="00000000-0000-0000-0000-000000000301"),
            _row(id="00000000-0000-0000-0000-000000000302"),
            _row(id="00000000-0000-0000-0000-000000000303"),
        ],
    )

    records = PlaylistPlacementCsvRawEvidenceSource(path).load()

    assert tuple(record.id for record in records) == (
        UUID("00000000-0000-0000-0000-000000000301"),
        UUID("00000000-0000-0000-0000-000000000302"),
        UUID("00000000-0000-0000-0000-000000000303"),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row()])

    records = PlaylistPlacementCsvRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_parses_optional_observed_at(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(observed_at="2026-01-16T12:00:00+00:00")])

    records = PlaylistPlacementCsvRawEvidenceSource(path).load()

    assert records[0].observed_at == datetime(2026, 1, 16, 12, 0, tzinfo=UTC)


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Playlist placement CSV file not found"):
        PlaylistPlacementCsvRawEvidenceSource(tmp_path / "missing.csv").load()


def test_missing_header_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="must include a header row"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_missing_required_column_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    columns = tuple(column for column in _COLUMNS if column != "summary")
    row = _row()
    del row["summary"]
    _write_table(path, columns, [row])

    with pytest.raises(ValueError, match="summary"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_missing_required_row_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(reference="")])

    with pytest.raises(ValueError, match="missing field 'reference'"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_too_many_columns_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    path.write_text(
        ",".join(_COLUMNS) + "\n" + ",".join(_row().values()) + ",extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too many columns"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_invalid_uuid_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(id="not-a-uuid")])

    with pytest.raises(ValueError, match="must be a valid UUID"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_invalid_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(occurred_at="not-a-datetime")])

    with pytest.raises(ValueError, match="must be an ISO datetime"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_naive_occurred_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(occurred_at="2026-01-15T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_naive_observed_at_fails(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(observed_at="2026-01-16T12:00:00")])

    with pytest.raises(ValueError, match="must be timezone-aware"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row(), _row(id="not-a-uuid")])

    with pytest.raises(ValueError, match="must be a valid UUID"):
        PlaylistPlacementCsvRawEvidenceSource(path).load()


def test_loaded_records_are_compatible_with_evidence_importer(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row()])
    fallback_observed_at = datetime(2026, 1, 16, 12, 0, tzinfo=UTC)

    records = PlaylistPlacementCsvRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: fallback_observed_at).import_records(records)

    assert len(evidence) == 1
    assert evidence[0].id == records[0].id
    assert evidence[0].kind is EvidenceKind.PLAYLIST_ACTIVITY
    assert evidence[0].signals == (EvidenceSignal.PLAYLIST_PLACEMENT,)
    assert evidence[0].observed_at == fallback_observed_at


def test_playlist_records_can_support_existing_observations(tmp_path: Path) -> None:
    path = tmp_path / "playlist-placements.csv"
    _write_csv(path, [_row()])
    observed_at = datetime(2026, 1, 20, 12, 0, tzinfo=UTC)

    playlist_record = PlaylistPlacementCsvRawEvidenceSource(path).load()[0]
    stream_record = RawEvidenceRecord(
        id=UUID("00000000-0000-0000-0000-000000000401"),
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased after playlist activity.",
        occurred_at=datetime(2026, 1, 18, 12, 0, tzinfo=UTC),
        reference="spotify-analytics:streams-week-2026-01-18",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )
    save_record = RawEvidenceRecord(
        id=UUID("00000000-0000-0000-0000-000000000402"),
        source_name="spotify",
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Saves increased after playlist activity.",
        occurred_at=datetime(2026, 1, 18, 12, 0, tzinfo=UTC),
        reference="spotify-analytics:saves-week-2026-01-18",
        signals=(EvidenceSignal.SAVE_GROWTH,),
    )

    evidence = EvidenceImporter(clock=lambda: observed_at).import_records(
        (playlist_record, stream_record, save_record)
    )
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
    id: str = "00000000-0000-0000-0000-000000000301",
    source_name: str = "spotify",
    summary: str = "Everything Is Fading was added to a playlist.",
    occurred_at: str = "2026-01-15T12:00:00+00:00",
    observed_at: str = "",
    reference: str = "spotify-playlist:example-playlist",
) -> dict[str, str]:
    return {
        "id": id,
        "source_name": source_name,
        "summary": summary,
        "occurred_at": occurred_at,
        "observed_at": observed_at,
        "reference": reference,
    }
