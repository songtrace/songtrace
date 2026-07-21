from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from songtrace.application import EvidenceImporter, ObservationExtractor
from songtrace.application.raw_evidence_source import RawEvidenceSource
from songtrace.domain.evidence import EvidenceKind, EvidenceSignal
from songtrace.domain.observation import ObservationKind
from songtrace.providers import AscapCsvRawEvidenceSource

_LAYOUT_A_COLUMNS = (
    "DistributionYear",
    "Distribution Quarter",
    "Statement Recipient ID",
    "Statement Recipient Name",
    "Party ID",
    "Party Name",
    "Legal Earner Party ID",
    "Legal Earner Party Name",
    "Performance Source/Broadcast Medium",
    "Music User Genre",
    "Music User",
    "Network Service",
    "Performance Start Date",
    "Performance End Date",
    "Survey Type",
    "Day Part Code",
    "Series or Film/Attraction",
    "Program Name",
    "Work ID",
    "Work Title",
    "CA%",
    "Classification Code",
    "Number of Plays",
    "Performance Type (Usage)",
    "Duration",
    "Performing Artist",
    "Composer Name",
    "EE Share",
    "Credits",
    "Dollars",
    "Premium Credits",
    "Premium Dollars",
    "Adjustment Indicator",
    "Adjustment Reason Code",
    "Original Distribution Date",
    "Role Type",
    "Type Of Right",
    "Territory",
    "Licensor",
    "Program Code",
    "Performance Quarter",
)
_LAYOUT_B_COLUMNS = (
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


def test_loads_layout_a_rows_as_raw_evidence_records(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row(), _layout_a_row(work_id="WORK_2")])
    source: RawEvidenceSource = AscapCsvRawEvidenceSource(path)

    records = source.load()

    assert len(records) == 2
    assert records[0].source_name == "ascap"
    assert records[0].kind is EvidenceKind.ROYALTY_ACTIVITY
    assert records[0].summary == "ASCAP royalty activity was reported for a statement row."
    assert records[0].signals == (EvidenceSignal.ROYALTY_REPORTED,)
    assert records[0].occurred_at == datetime(2026, 6, 30, 23, 59, 59, tzinfo=UTC)
    assert records[0].observed_at is None
    assert records[0].reference is not None
    assert records[0].reference.startswith("ascap-csv:layout-a:file:")
    assert records[0].reference.endswith(":row:2")
    assert "42278445" not in records[0].reference


def test_preserves_row_order(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(
        path,
        _LAYOUT_A_COLUMNS,
        [
            _layout_a_row(work_id="WORK_1"),
            _layout_a_row(work_id="WORK_2"),
            _layout_a_row(work_id="WORK_3"),
        ],
    )

    records = AscapCsvRawEvidenceSource(path).load()

    assert tuple(record.reference for record in records) == (
        _reference_for_row(records[0].reference, 2),
        _reference_for_row(records[0].reference, 3),
        _reference_for_row(records[0].reference, 4),
    )


def test_returns_immutable_tuple(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row()])

    records = AscapCsvRawEvidenceSource(path).load()

    assert isinstance(records, tuple)


def test_generates_deterministic_record_ids(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row()])

    first = AscapCsvRawEvidenceSource(path).load()
    second = AscapCsvRawEvidenceSource(path).load()

    assert first[0].id == second[0].id
    assert isinstance(first[0].id, UUID)


def test_rejects_layout_b_as_unsupported_for_this_source(tmp_path: Path) -> None:
    path = tmp_path / "43013186.csv"
    _write_csv(path, _LAYOUT_B_COLUMNS, [_layout_b_row()])

    with pytest.raises(ValueError, match="layout A is missing required field"):
        AscapCsvRawEvidenceSource(path).load()


def test_rejects_missing_layout_a_column(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    columns = tuple(column for column in _LAYOUT_A_COLUMNS if column != "Dollars")
    row = _layout_a_row()
    del row["Dollars"]
    _write_csv(path, columns, [row])

    with pytest.raises(ValueError, match="Dollars"):
        AscapCsvRawEvidenceSource(path).load()


def test_rejects_missing_required_row_value(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row(distribution_year="")])

    with pytest.raises(ValueError, match="missing field 'DistributionYear'"):
        AscapCsvRawEvidenceSource(path).load()


def test_rejects_invalid_distribution_year(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row(distribution_year="not-a-year")])

    with pytest.raises(ValueError, match=r"DistributionYear.*year"):
        AscapCsvRawEvidenceSource(path).load()


def test_rejects_invalid_distribution_quarter(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row(distribution_quarter="5")])

    with pytest.raises(ValueError, match=r"Distribution Quarter.*1, 2, 3, or 4"):
        AscapCsvRawEvidenceSource(path).load()


def test_file_not_found_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ASCAP CSV file not found"):
        AscapCsvRawEvidenceSource(tmp_path / "missing.csv").load()


def test_loaded_records_are_compatible_with_import_and_observation_pipeline(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(path, _LAYOUT_A_COLUMNS, [_layout_a_row()])
    observed_at = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)

    records = AscapCsvRawEvidenceSource(path).load()
    evidence = EvidenceImporter(clock=lambda: observed_at).import_records(records)
    observations = ObservationExtractor(clock=lambda: observed_at).extract(evidence)

    assert len(evidence) == 1
    assert evidence[0].source.name == "ascap"
    assert evidence[0].kind is EvidenceKind.ROYALTY_ACTIVITY
    assert evidence[0].observed_at == observed_at
    assert evidence[0].occurred_at == datetime(2026, 6, 30, 23, 59, 59, tzinfo=UTC)
    assert [observation.kind for observation in observations] == [ObservationKind.ROYALTY_REPORTED]
    assert observations[0].supporting_evidence_ids == (evidence[0].id,)


def test_no_partial_result_when_later_row_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "42278445.csv"
    _write_csv(
        path,
        _LAYOUT_A_COLUMNS,
        [_layout_a_row(), _layout_a_row(distribution_quarter="invalid")],
    )

    with pytest.raises(ValueError, match="Distribution Quarter"):
        AscapCsvRawEvidenceSource(path).load()


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.write_text(
        ",".join(columns)
        + "\n"
        + "\n".join(",".join(row[column] for column in columns) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def _layout_a_row(
    *,
    distribution_year: str = "2026",
    distribution_quarter: str = "2",
    work_id: str = "WORK_1",
) -> dict[str, str]:
    return {
        "DistributionYear": distribution_year,
        "Distribution Quarter": distribution_quarter,
        "Statement Recipient ID": "RECIPIENT_ID",
        "Statement Recipient Name": "RECIPIENT",
        "Party ID": "PARTY_ID",
        "Party Name": "PARTY",
        "Legal Earner Party ID": "",
        "Legal Earner Party Name": "",
        "Performance Source/Broadcast Medium": "Streaming",
        "Music User Genre": "Digital",
        "Music User": "MUSIC_USER",
        "Network Service": "",
        "Performance Start Date": "",
        "Performance End Date": "",
        "Survey Type": "Survey",
        "Day Part Code": "",
        "Series or Film/Attraction": "",
        "Program Name": "",
        "Work ID": work_id,
        "Work Title": "WORK_TITLE",
        "CA%": "100",
        "Classification Code": "",
        "Number of Plays": "10",
        "Performance Type (Usage)": "Performance",
        "Duration": "0:00",
        "Performing Artist": "",
        "Composer Name": "",
        "EE Share": "1.0",
        "Credits": "1.23",
        "Dollars": "4.56",
        "Premium Credits": "0",
        "Premium Dollars": "0",
        "Adjustment Indicator": "",
        "Adjustment Reason Code": "",
        "Original Distribution Date": "",
        "Role Type": "Writer",
        "Type Of Right": "Performance",
        "Territory": "US",
        "Licensor": "LICENSOR",
        "Program Code": "",
        "Performance Quarter": "2Q2026",
    }


def _layout_b_row() -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "RECIPIENT",
        "Statement Recipient ID": "RECIPIENT_ID",
        "Party Name": "PARTY",
        "Party ID": "PARTY_ID",
        "Distribution Date": "01-31-2026",
        "Country Name": "US",
        "Performance Start Date": "01-01-2026",
        "Performance End Date": "01-31-2026",
        "Work Title": "WORK_TITLE",
        "Work ID": "WORK_1",
        "Revenue Class Code": "CODE",
        "Revenue Class Description": "DESCRIPTION",
        "$ Amount": "4.56",
        "Role Type": "Writer",
        "Type Of Right": "Performance",
        "Territory": "US",
    }


def _reference_for_row(reference: str | None, row_number: int) -> str:
    assert reference is not None
    return f"{reference.rsplit(':', maxsplit=1)[0]}:{row_number}"
