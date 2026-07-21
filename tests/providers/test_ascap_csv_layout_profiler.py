from __future__ import annotations

import json
from pathlib import Path

import pytest

from songtrace.providers import profile_ascap_csv_layout

_LAYOUT_A_COLUMNS = (
    "DistributionYear",
    "Distribution Quarter",
    "Statement Recipient ID",
    "Statement Recipient Name",
    "Party ID",
    "Party Name",
    "Performance Source/Broadcast Medium",
    "Music User Genre",
    "Music User",
    "Performance Start Date",
    "Performance End Date",
    "Work ID",
    "Work Title",
    "Number of Plays",
    "Performance Type (Usage)",
    "Credits",
    "Dollars",
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


def test_profiles_multiple_ascap_csv_layouts_without_row_values(tmp_path: Path) -> None:
    first = tmp_path / "42278445.csv"
    second = tmp_path / "renamed-statement.csv"
    _write_csv(first, _LAYOUT_A_COLUMNS, [_layout_a_row(), _layout_a_row(work_id="SECRET_WORK_2")])
    _write_csv(second, _LAYOUT_B_COLUMNS, [_layout_b_row()])

    profile = profile_ascap_csv_layout((first, second))
    payload = json.loads(profile.to_json())

    assert payload["unique_header_shape_count"] == 2
    assert payload["files"][0]["filename"] == "42278445.csv"
    assert payload["files"][0]["numeric_filename"] is True
    assert payload["files"][0]["row_count"] == 2
    assert payload["files"][1]["column_count"] == len(_LAYOUT_B_COLUMNS)
    assert "Work ID" in payload["common_columns"]

    output = profile.to_json()
    assert "SECRET_WORK_TITLE" not in output
    assert "SECRET_PARTY" not in output
    assert "123.45" not in output


def test_profiles_column_statuses_and_distinct_counts(tmp_path: Path) -> None:
    path = tmp_path / "layout-a.csv"
    _write_csv(
        path,
        _LAYOUT_A_COLUMNS,
        [
            _layout_a_row(work_id="SECRET_WORK_1", dollars="10.00"),
            _layout_a_row(work_id="SECRET_WORK_2", dollars="20.00"),
        ],
    )

    payload = json.loads(profile_ascap_csv_layout((path,)).to_json())
    columns = {column["name"]: column for column in payload["files"][0]["columns"]}

    assert columns["DistributionYear"]["status"] == "constant_nonblank"
    assert columns["Performance Start Date"]["status"] == "empty_all_rows"
    assert columns["Work ID"]["status"] == "variable"
    assert columns["Work ID"]["distinct_nonblank_count"] == 2


def test_profiles_date_shape_masks_without_values(tmp_path: Path) -> None:
    path = tmp_path / "layout-b.csv"
    _write_csv(path, _LAYOUT_B_COLUMNS, [_layout_b_row()])

    payload = json.loads(profile_ascap_csv_layout((path,)).to_json())
    masks = payload["files"][0]["date_period_masks"]

    assert masks["Distribution Date"] == {"99-99-9999": 1}
    assert "01-31-2026" not in json.dumps(payload, sort_keys=True)


def test_profiles_numeric_parse_counts_without_amount_values(tmp_path: Path) -> None:
    path = tmp_path / "layout-b.csv"
    _write_csv(path, _LAYOUT_B_COLUMNS, [_layout_b_row(amount="123.45")])

    payload = json.loads(profile_ascap_csv_layout((path,)).to_json())
    numeric_profiles = {
        numeric_profile["column"]: numeric_profile
        for numeric_profile in payload["files"][0]["numeric_profiles"]
    }

    assert numeric_profiles["$ Amount"]["parsed_count"] == 1
    assert numeric_profiles["$ Amount"]["positive_row_count"] == 1
    assert "123.45" not in json.dumps(payload, sort_keys=True)


def test_profiles_row_grain_candidates(tmp_path: Path) -> None:
    path = tmp_path / "layout-a.csv"
    _write_csv(
        path,
        _LAYOUT_A_COLUMNS,
        [
            _layout_a_row(work_id="SECRET_WORK_1", music_user="SECRET_USER_1"),
            _layout_a_row(work_id="SECRET_WORK_1", music_user="SECRET_USER_2"),
        ],
    )

    payload = json.loads(profile_ascap_csv_layout((path,)).to_json())
    row_grain_profiles = {
        tuple(row_grain_profile["columns"]): row_grain_profile
        for row_grain_profile in payload["files"][0]["row_grain_profiles"]
    }

    assert row_grain_profiles[("Work ID",)]["distinct_key_count"] == 1
    assert row_grain_profiles[("Work ID",)]["duplicate_row_count"] == 1
    assert row_grain_profiles[("Work ID", "Music User")]["distinct_key_count"] == 2


def test_rejects_empty_path_collection() -> None:
    with pytest.raises(ValueError, match="at least one ASCAP CSV path is required"):
        profile_ascap_csv_layout(())


def test_missing_file_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ASCAP CSV file not found"):
        profile_ascap_csv_layout((tmp_path / "missing.csv",))


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
    work_id: str = "SECRET_WORK_1",
    music_user: str = "SECRET_USER_1",
    dollars: str = "123.45",
) -> dict[str, str]:
    return {
        "DistributionYear": "2026",
        "Distribution Quarter": "2",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Party ID": "SECRET_PARTY_ID",
        "Party Name": "SECRET_PARTY",
        "Performance Source/Broadcast Medium": "Streaming",
        "Music User Genre": "Digital",
        "Music User": music_user,
        "Performance Start Date": "",
        "Performance End Date": "",
        "Work ID": work_id,
        "Work Title": "SECRET_WORK_TITLE",
        "Number of Plays": "10",
        "Performance Type (Usage)": "Performance",
        "Credits": "1.23",
        "Dollars": dollars,
        "Performance Quarter": "2Q2026",
    }


def _layout_b_row(*, amount: str = "123.45") -> dict[str, str]:
    return {
        "File Type": "Royalty",
        "Statement Recipient Name": "SECRET_RECIPIENT",
        "Statement Recipient ID": "SECRET_RECIPIENT_ID",
        "Party Name": "SECRET_PARTY",
        "Party ID": "SECRET_PARTY_ID",
        "Distribution Date": "01-31-2026",
        "Country Name": "Neverland",
        "Performance Start Date": "01-01-2026",
        "Performance End Date": "01-31-2026",
        "Work Title": "SECRET_WORK_TITLE",
        "Work ID": "SECRET_WORK_1",
        "Revenue Class Code": "SECRET_CODE",
        "Revenue Class Description": "SECRET_DESCRIPTION",
        "$ Amount": amount,
        "Role Type": "Writer",
        "Type Of Right": "Performance",
        "Territory": "SECRET_TERRITORY",
    }
