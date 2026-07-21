from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application import EvidenceImporter, ObservationExtractor
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.observation import ObservationKind
from songtrace.providers import (
    AscapCsvRawEvidenceSource,
    AscapInternationalIncomingCsvRawEvidenceSource,
)

_INTERNATIONAL_INCOMING_COLUMNS = (
    "File Type",
    "Statement Recipient Name",
    "Statement Recipient ID",
    "Party Name",
    "Party ID",
    "Distribution Date",
    "Country Name",
    "Performance Start Date",
    "Performance End Date",
    "Work Title",
    "Work ID",
    "Revenue Class Code",
    "Revenue Class Description",
    "$ Amount",
    "Role Type",
    "Type Of Right",
    "Territory",
)
_DOMESTIC_COLUMNS = (
    "DistributionYear",
    "Distribution Quarter",
    "Statement Recipient ID",
    "Statement Recipient Name",
    "Party ID",
    "Party Name",
    "Performance Source/Broadcast Medium",
    "Music User Genre",
    "Music User",
    "Work ID",
    "Work Title",
    "Number of Plays",
    "Performance Type (Usage)",
    "Credits",
    "Dollars",
    "Performance Quarter",
)


def test_loads_international_incoming_rows_as_raw_evidence_records(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(
        path,
        _INTERNATIONAL_INCOMING_COLUMNS,
        [_international_incoming_row(), _international_incoming_row(work_id="WORK_2")],
    )
    source: RawEvidenceSource = AscapInternationalIncomingCsvRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 2
    assert records[0].source_name == "ascap"
    assert records[0].kind is EvidenceKind.ROYALTY_ACTIVITY
    assert (
        records[0].summary
        == "ASCAP international incoming royalty activity was reported for a statement row."
    )
    assert records[0].signals == (EvidenceSignal.ROYALTY_REPORTED,)
    assert records[0].occurred_at == datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC)
    assert records[0].observed_at is None
    assert records[0].reference is not None
    assert records[0].reference.startswith("ascap-csv:international-incoming:file:")
    assert records[0].reference.endswith(":row:2")
    assert "43013186" not in records[0].reference


def test_preserves_row_order(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(
        path,
        _INTERNATIONAL_INCOMING_COLUMNS,
        [
            _international_incoming_row(work_id="WORK_1"),
            _international_incoming_row(work_id="WORK_2"),
            _international_incoming_row(work_id="WORK_3"),
        ],
    )

    records = AscapInternationalIncomingCsvRawEvidenceSource(path).load()

    assert tuple(record.reference for record in records) == (
        _reference_for_row(records[0].reference, 2),
        _reference_for_row(records[0].reference, 3),
        _reference_for_row(records[0].reference, 4),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(path, _INTERNATIONAL_INCOMING_COLUMNS, [_international_incoming_row()])

    records = AscapInternationalIncomingCsvRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_generates_deterministic_record_ids_and_references(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(path, _INTERNATIONAL_INCOMING_COLUMNS, [_international_incoming_row()])

    first = AscapInternationalIncomingCsvRawEvidenceSource(path).load()
    second = AscapInternationalIncomingCsvRawEvidenceSource(path).load()

    assert first[0].id == second[0].id
    assert first[0].reference == second[0].reference
    assert isinstance(first[0].id, UUID)


def test_rejects_domestic_layout_as_unsupported_for_this_source(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _DOMESTIC_COLUMNS, [_domestic_row()])

    with pytest.raises(ValueError, match="international incoming CSV is missing required field"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_rejects_missing_required_header_field(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    columns = tuple(column for column in _INTERNATIONAL_INCOMING_COLUMNS if column != "$ Amount")
    row = _international_incoming_row()
    del row["$ Amount"]
    _write_csv(path, columns, [row])

    with pytest.raises(ValueError, match=r"\$ Amount"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_rejects_missing_required_row_value(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(
        path,
        _INTERNATIONAL_INCOMING_COLUMNS,
        [_international_incoming_row(distribution_date="")],
    )

    with pytest.raises(ValueError, match="missing field 'Distribution Date'"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_rejects_invalid_distribution_date(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(
        path,
        _INTERNATIONAL_INCOMING_COLUMNS,
        [_international_incoming_row(distribution_date="2026-01-31")],
    )

    with pytest.raises(ValueError, match=r"Distribution Date.*MM-DD-YYYY"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_rejects_rows_with_too_many_columns(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    path.write_text(
        ",".join(_INTERNATIONAL_INCOMING_COLUMNS)
        + "\n"
        + ",".join(
            _international_incoming_row()[column] for column in _INTERNATIONAL_INCOMING_COLUMNS
        )
        + ",unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too many columns"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ASCAP CSV file not found"):
        AscapInternationalIncomingCsvRawEvidenceSource(tmp_path / "missing.csv").load()


def test_loaded_records_are_compatible_with_import_and_observation_pipeline(
    tmp_path: Path,
) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(path, _INTERNATIONAL_INCOMING_COLUMNS, [_international_incoming_row()])
    observed_at = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)

    records = AscapInternationalIncomingCsvRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: observed_at).import_records(records)
    observations = ObservationExtractor(clock=lambda: observed_at).extract(evidence)

    assert len(evidence) == 1
    assert evidence[0].source.name == "ascap"
    assert evidence[0].kind is EvidenceKind.ROYALTY_ACTIVITY
    assert evidence[0].observed_at == observed_at
    assert evidence[0].occurred_at == datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC)
    assert [observation.kind for observation in observations] == [ObservationKind.ROYALTY_REPORTED]
    assert observations[0].supporting_evidence_ids == (evidence[0].id,)


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(
        path,
        _INTERNATIONAL_INCOMING_COLUMNS,
        [_international_incoming_row(), _international_incoming_row(distribution_date="invalid")],
    )

    with pytest.raises(ValueError, match="Distribution Date"):
        AscapInternationalIncomingCsvRawEvidenceSource(path).load()


def test_domestic_source_still_rejects_international_incoming_layout(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(path, _INTERNATIONAL_INCOMING_COLUMNS, [_international_incoming_row()])

    with pytest.raises(ValueError, match="layout A is missing required field"):
        AscapCsvRawEvidenceSource(path).load()


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows([row[column] for column in columns] for row in rows)


def _international_incoming_row(
    *,
    distribution_date: str = "01-31-2026",
    work_id: str = "WORK_1",
) -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "RECIPIENT",
        "Statement Recipient ID": "RECIPIENT_ID",
        "Party Name": "PARTY",
        "Party ID": "PARTY_ID",
        "Distribution Date": distribution_date,
        "Country Name": "US",
        "Performance Start Date": "01-01-2026",
        "Performance End Date": "01-31-2026",
        "Work Title": "WORK_TITLE",
        "Work ID": work_id,
        "Revenue Class Code": "CODE",
        "Revenue Class Description": "DESCRIPTION",
        "$ Amount": "4.56",
        "Role Type": "Writer",
        "Type Of Right": "Performance",
        "Territory": "US",
    }


def _domestic_row() -> dict[str, str]:
    return {
        "DistributionYear": "2026",
        "Distribution Quarter": "2",
        "Statement Recipient ID": "RECIPIENT_ID",
        "Statement Recipient Name": "RECIPIENT",
        "Party ID": "PARTY_ID",
        "Party Name": "PARTY",
        "Performance Source/Broadcast Medium": "Streaming",
        "Music User Genre": "Digital",
        "Music User": "MUSIC_USER",
        "Work ID": "WORK_1",
        "Work Title": "WORK_TITLE",
        "Number of Plays": "10",
        "Performance Type (Usage)": "Performance",
        "Credits": "1.23",
        "Dollars": "4.56",
        "Performance Quarter": "2Q2026",
    }


def _reference_for_row(reference: str | None, row_number: int) -> str:
    assert reference is not None
    return f"{reference.rsplit(':', maxsplit=1)[0]}:{row_number}"
