from datetime import datetime
from pathlib import Path
from uuid import UUID

import typer

from songtrace.application import (
    CsvRawEvidenceSource,
    EvidenceImportBatch,
    EvidenceImporter,
    EvidenceImportError,
    JsonRawEvidenceSource,
    PlaylistPlacementCsvRawEvidenceSource,
    RawEvidenceRecord,
    XlsxRawEvidenceSource,
)
from songtrace.domain.evidence import Evidence
from songtrace.presentation.cli.errors import exit_with_import_error, exit_with_source_error
from songtrace.providers import AscapCsvRawEvidenceSource


def load_and_import_evidence(
    evidence_file: Path,
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_records = load_raw_records(evidence_file)
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        exit_with_import_error(error)
    except ValueError as error:
        exit_with_source_error(error)

    return raw_records, evidence


def load_and_import_ascap_layout_a_evidence(
    csv_file: Path,
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_records = AscapCsvRawEvidenceSource(csv_file).load()
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        exit_with_import_error(error)
    except (FileNotFoundError, ValueError) as error:
        exit_with_source_error(error)

    return raw_records, evidence


def load_and_import_playlist_placement_investigation_evidence(
    playlist_file: Path,
    evidence_files: tuple[Path, ...],
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_record_groups = [PlaylistPlacementCsvRawEvidenceSource(playlist_file).load()]
        raw_record_groups.extend(
            load_raw_records(evidence_file) for evidence_file in evidence_files
        )
        raw_records = tuple(record for group in raw_record_groups for record in group)
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        exit_with_import_error(error)
    except (FileNotFoundError, ValueError) as error:
        exit_with_source_error(error)

    return raw_records, evidence


def load_and_import_batch(
    evidence_file: Path,
    *,
    source_name: str,
    batch_id: UUID | None,
    imported_at: datetime | None,
) -> tuple[tuple[RawEvidenceRecord, ...], EvidenceImportBatch]:
    try:
        raw_records = load_raw_records(evidence_file)
        importer = EvidenceImporter(
            clock=(lambda: imported_at) if imported_at is not None else None,
            batch_id_factory=(lambda: batch_id) if batch_id is not None else None,
        )
        batch = importer.import_batch(raw_records, source_name=source_name)
    except EvidenceImportError as error:
        exit_with_import_error(error)
    except ValueError as error:
        exit_with_source_error(error)

    return raw_records, batch


def load_and_import_playlist_placement_batch(
    playlist_file: Path,
    *,
    source_name: str,
    batch_id: UUID | None,
    imported_at: datetime | None,
) -> tuple[tuple[RawEvidenceRecord, ...], EvidenceImportBatch]:
    try:
        raw_records = PlaylistPlacementCsvRawEvidenceSource(playlist_file).load()
        importer = EvidenceImporter(
            clock=(lambda: imported_at) if imported_at is not None else None,
            batch_id_factory=(lambda: batch_id) if batch_id is not None else None,
        )
        batch = importer.import_batch(raw_records, source_name=source_name)
    except EvidenceImportError as error:
        exit_with_import_error(error)
    except (FileNotFoundError, ValueError) as error:
        exit_with_source_error(error)

    return raw_records, batch


def load_raw_records(path: Path) -> tuple[RawEvidenceRecord, ...]:
    suffix = path.suffix.lower()

    if suffix == ".json":
        return JsonRawEvidenceSource(path).load()
    if suffix == ".csv":
        return CsvRawEvidenceSource(path).load()
    if suffix == ".xlsx":
        return XlsxRawEvidenceSource(path).load()

    raise typer.BadParameter(
        "unsupported evidence file extension; expected .json, .csv, or .xlsx",
        param_hint="evidence_file",
    )
