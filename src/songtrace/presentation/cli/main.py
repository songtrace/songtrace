import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

import typer
from rich.console import Console

from songtrace import __version__
from songtrace.application import (
    CsvRawEvidenceSource,
    EvidenceImportBatch,
    EvidenceImporter,
    EvidenceImportError,
    InvestigationService,
    JsonRawEvidenceSource,
    ObservationExtractor,
    PlaylistPlacementCsvRawEvidenceSource,
    RawEvidenceRecord,
    SimpleInvestigator,
    XlsxRawEvidenceSource,
)
from songtrace.domain.conclusion import Conclusion
from songtrace.domain.evidence import Evidence
from songtrace.domain.observation import Observation
from songtrace.providers import (
    AscapCsvRawEvidenceSource,
    AscapWorkSummary,
    profile_ascap_csv_layout,
    summarize_ascap_work,
)

app = typer.Typer(
    name="songtrace",
    help="Investigate why song performance changes.",
    no_args_is_help=True,
)

console = Console()
error_console = Console(stderr=True)
investigation_service = InvestigationService()


def version_callback(value: bool) -> None:
    """Print the SongTrace version and exit."""
    if value:
        console.print(f"SongTrace {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the installed SongTrace version.",
        ),
    ] = None,
) -> None:
    """SongTrace song investigation engine."""


@app.command()
def investigate(
    artist: Annotated[str, typer.Option(help="Name of the recording artist.")],
    track: Annotated[str, typer.Option(help="Title of the track.")],
) -> None:
    """Begin a song investigation."""
    investigation = investigation_service.begin(
        artist=artist,
        track=track,
    )

    console.print("[bold]SongTrace Investigation[/bold]")
    console.print()
    console.print(f"Artist: {investigation.track.artist}")
    console.print(f"Track: {investigation.track.title}")
    console.print(f"Status: {investigation.status.value}")


@app.command("investigate-evidence")
def investigate_evidence(
    evidence_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a JSON, CSV, or XLSX raw evidence file.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Run the deterministic investigation pipeline for a raw evidence file."""

    output_format = _parse_output_format(output)
    _raw_records, evidence = _load_and_import_evidence(evidence_file)
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            _print_text_result(evidence, observations, result.conclusions)
        case "json":
            _print_json_result(evidence, observations, result.conclusions)


@app.command("investigate-playlist-placement-csv")
def investigate_playlist_placement_csv(
    playlist_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a provider-neutral playlist placement CSV file.",
        ),
    ],
    evidence_files: Annotated[
        list[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="One or more supplemental JSON, CSV, or XLSX raw evidence files.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Investigate playlist placement evidence with supplemental raw evidence."""

    if not evidence_files:
        raise typer.BadParameter(
            "at least one supplemental evidence file is required",
            param_hint="evidence_files",
        )

    output_format = _parse_output_format(output)
    _raw_records, evidence = _load_and_import_playlist_placement_investigation_evidence(
        playlist_file,
        tuple(evidence_files),
    )
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            _print_text_result(evidence, observations, result.conclusions)
        case "json":
            _print_json_result(evidence, observations, result.conclusions)


@app.command("investigate-ascap-csv-layout-a")
def investigate_ascap_csv_layout_a(
    csv_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to an ASCAP CSV file using the profiled 41-column layout A.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Run the deterministic investigation pipeline for an ASCAP layout A CSV file."""

    output_format = _parse_output_format(output)
    _raw_records, evidence = _load_and_import_ascap_layout_a_evidence(csv_file)
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            _print_text_result(evidence, observations, result.conclusions)
        case "json":
            _print_json_result(evidence, observations, result.conclusions)


@app.command("profile-ascap-csv-layout")
def profile_ascap_csv_layout_command(
    csv_files: Annotated[
        list[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="One or more private local ASCAP CSV files to profile safely.",
        ),
    ],
) -> None:
    """Profile private ASCAP CSV layouts without exposing row values."""

    try:
        profile = profile_ascap_csv_layout(tuple(csv_files))
    except (FileNotFoundError, ValueError) as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    print(profile.to_json())


@app.command("summarize-ascap-work")
def summarize_ascap_work_command(
    paths: Annotated[
        list[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            help="One or more ASCAP CSV files or directories containing ASCAP CSV files.",
        ),
    ],
    work_id: Annotated[
        str | None,
        typer.Option(
            "--work-id",
            help=(
                "Exact ASCAP work ID to summarize. The value is used for matching but not printed."
            ),
        ),
    ] = None,
    work_title: Annotated[
        str | None,
        typer.Option(
            "--work-title",
            help=(
                "Case-insensitive work title query. The value is used for matching but not printed."
            ),
        ),
    ] = None,
    include_breakdowns: Annotated[
        bool,
        typer.Option(
            "--include-breakdowns",
            help="Include opt-in aggregate breakdown labels and counts.",
        ),
    ] = False,
    include_attribution_gaps: Annotated[
        bool,
        typer.Option(
            "--include-attribution-gaps",
            help="Include source-attribution status and missing upstream evidence categories.",
        ),
    ] = False,
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Summarize private ASCAP CSV rows for one work without exposing row values."""

    output_format = _parse_output_format(output)
    try:
        summary = summarize_ascap_work(
            tuple(paths),
            work_id=work_id,
            work_title_query=work_title,
        )
    except (FileNotFoundError, ValueError) as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    match output_format:
        case "text":
            _print_ascap_work_summary_text_result(
                summary,
                include_breakdowns=include_breakdowns,
                include_attribution_gaps=include_attribution_gaps,
            )
        case "json":
            print(
                summary.to_json(
                    include_breakdowns=include_breakdowns,
                    include_attribution_gaps=include_attribution_gaps,
                )
            )


@app.command("validate-evidence")
def validate_evidence(
    evidence_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a JSON, CSV, or XLSX raw evidence file.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
    source_name: Annotated[
        str,
        typer.Option(
            "--source-name",
            help="Provider-neutral source name for import batch metadata.",
        ),
    ] = "local_file",
    batch_id: Annotated[
        str | None,
        typer.Option(
            "--batch-id",
            help="Optional deterministic import batch UUID.",
        ),
    ] = None,
    imported_at: Annotated[
        str | None,
        typer.Option(
            "--imported-at",
            help="Optional deterministic timezone-aware ISO import timestamp.",
        ),
    ] = None,
) -> None:
    """Validate that a raw evidence file can be imported into domain evidence."""

    output_format = _parse_output_format(output)
    parsed_batch_id = _parse_optional_batch_id(batch_id)
    parsed_imported_at = _parse_optional_imported_at(imported_at)
    raw_records, batch = _load_and_import_batch(
        evidence_file,
        source_name=source_name,
        batch_id=parsed_batch_id,
        imported_at=parsed_imported_at,
    )

    match output_format:
        case "text":
            _print_validation_text_result(raw_records, batch)
        case "json":
            _print_validation_json_result(raw_records, batch)


@app.command("validate-playlist-placement-csv")
def validate_playlist_placement_csv(
    playlist_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a provider-neutral playlist placement CSV file.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
    source_name: Annotated[
        str,
        typer.Option(
            "--source-name",
            help="Provider-neutral source name for import batch metadata.",
        ),
    ] = "local_playlist_placement_file",
    batch_id: Annotated[
        str | None,
        typer.Option(
            "--batch-id",
            help="Optional deterministic import batch UUID.",
        ),
    ] = None,
    imported_at: Annotated[
        str | None,
        typer.Option(
            "--imported-at",
            help="Optional deterministic timezone-aware ISO import timestamp.",
        ),
    ] = None,
) -> None:
    """Validate a local playlist placement CSV through the import boundary."""

    output_format = _parse_output_format(output)
    parsed_batch_id = _parse_optional_batch_id(batch_id)
    parsed_imported_at = _parse_optional_imported_at(imported_at)
    raw_records, batch = _load_and_import_playlist_placement_batch(
        playlist_file,
        source_name=source_name,
        batch_id=parsed_batch_id,
        imported_at=parsed_imported_at,
    )

    match output_format:
        case "text":
            _print_validation_text_result(raw_records, batch)
        case "json":
            _print_validation_json_result(raw_records, batch)


def _load_and_import_evidence(
    evidence_file: Path,
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_records = _load_raw_records(evidence_file)
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        _print_import_error(error)
        raise typer.Exit(1) from error
    except ValueError as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    return raw_records, evidence


def _load_and_import_ascap_layout_a_evidence(
    csv_file: Path,
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_records = AscapCsvRawEvidenceSource(csv_file).load()
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        _print_import_error(error)
        raise typer.Exit(1) from error
    except (FileNotFoundError, ValueError) as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    return raw_records, evidence


def _load_and_import_playlist_placement_investigation_evidence(
    playlist_file: Path,
    evidence_files: tuple[Path, ...],
) -> tuple[tuple[RawEvidenceRecord, ...], tuple[Evidence, ...]]:
    try:
        raw_record_groups = [PlaylistPlacementCsvRawEvidenceSource(playlist_file).load()]
        raw_record_groups.extend(
            _load_raw_records(evidence_file) for evidence_file in evidence_files
        )
        raw_records = tuple(record for group in raw_record_groups for record in group)
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        _print_import_error(error)
        raise typer.Exit(1) from error
    except (FileNotFoundError, ValueError) as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    return raw_records, evidence


def _load_and_import_batch(
    evidence_file: Path,
    *,
    source_name: str,
    batch_id: UUID | None,
    imported_at: datetime | None,
) -> tuple[tuple[RawEvidenceRecord, ...], EvidenceImportBatch]:
    try:
        raw_records = _load_raw_records(evidence_file)
        importer = EvidenceImporter(
            clock=(lambda: imported_at) if imported_at is not None else None,
            batch_id_factory=(lambda: batch_id) if batch_id is not None else None,
        )
        batch = importer.import_batch(raw_records, source_name=source_name)
    except EvidenceImportError as error:
        _print_import_error(error)
        raise typer.Exit(1) from error
    except ValueError as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    return raw_records, batch


def _load_and_import_playlist_placement_batch(
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
        _print_import_error(error)
        raise typer.Exit(1) from error
    except (FileNotFoundError, ValueError) as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    return raw_records, batch


def _parse_optional_batch_id(value: str | None) -> UUID | None:
    if value is None:
        return None

    try:
        return UUID(value)
    except ValueError as error:
        raise typer.BadParameter(
            "batch ID must be a valid UUID",
            param_hint="--batch-id",
        ) from error


def _parse_optional_imported_at(value: str | None) -> datetime | None:
    if value is None:
        return None

    try:
        imported_at = datetime.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter(
            "imported_at must be an ISO datetime",
            param_hint="--imported-at",
        ) from error

    if imported_at.tzinfo is None or imported_at.utcoffset() is None:
        raise typer.BadParameter(
            "imported_at must be timezone-aware",
            param_hint="--imported-at",
        )

    return imported_at


def _parse_output_format(output: str) -> Literal["text", "json"]:
    output_format = output.lower()
    if output_format == "text":
        return "text"
    if output_format == "json":
        return "json"

    raise typer.BadParameter(
        "unsupported output format; expected text or json",
        param_hint="--output",
    )


def _print_text_result(
    evidence: tuple[Evidence, ...],
    observations: tuple[Observation, ...],
    conclusions: tuple[Conclusion, ...],
) -> None:
    console.print("[bold]SongTrace Evidence Investigation[/bold]")
    console.print()
    console.print(f"Evidence: {len(evidence)}")
    console.print(f"Observations: {len(observations)}")
    console.print(f"Conclusions: {len(conclusions)}")

    if conclusions:
        console.print()
        console.print("[bold]Conclusions[/bold]")
        for conclusion in conclusions:
            console.print(f"- {conclusion.statement}")


def _print_json_result(
    evidence: tuple[Evidence, ...],
    observations: tuple[Observation, ...],
    conclusions: tuple[Conclusion, ...],
) -> None:
    payload = {
        "evidence_count": len(evidence),
        "observation_count": len(observations),
        "conclusion_count": len(conclusions),
        "evidence_ids": [str(item.id) for item in evidence],
        "observation_ids": [str(observation.id) for observation in observations],
        "conclusions": [
            {
                "id": str(conclusion.id),
                "statement": conclusion.statement,
                "confidence_level": conclusion.confidence.level.value,
                "supporting_observation_ids": [
                    str(observation_id) for observation_id in conclusion.supporting_observation_ids
                ],
            }
            for conclusion in conclusions
        ],
    }
    print(json.dumps(payload, sort_keys=True))


def _print_ascap_work_summary_text_result(
    summary: AscapWorkSummary, *, include_breakdowns: bool, include_attribution_gaps: bool
) -> None:
    console.print("[bold]SongTrace ASCAP Work Summary[/bold]")
    console.print()
    console.print(f"Scanned files: {summary.scanned_file_count}")
    console.print(f"Matched files: {summary.matched_file_count}")
    console.print(f"Matched rows: {summary.matched_row_count}")
    console.print(f"Distribution periods/dates: {summary.distribution_period_count}")
    console.print(f"Territories/countries: {summary.territory_count}")
    console.print(f"Revenue classes: {summary.revenue_class_count}")
    console.print("Statement types:")
    if summary.statement_type_counts:
        for statement_type, count in summary.statement_type_counts:
            console.print(f"- {statement_type}: {count}")
    else:
        console.print("- none: 0")

    if include_breakdowns:
        _print_ascap_breakdown("Distribution periods/dates", summary.distribution_period_counts)
        _print_ascap_breakdown("Territories/countries", summary.territory_counts)
        _print_ascap_breakdown("Revenue classes", summary.revenue_class_counts)

    if include_attribution_gaps:
        _print_ascap_attribution_gaps(summary)


def _print_ascap_attribution_gaps(summary: AscapWorkSummary) -> None:
    console.print()
    console.print("[bold]Source attribution[/bold]")
    console.print(f"Status: {summary.source_attribution_status}")
    console.print("Missing upstream evidence:")
    for evidence_type in summary.missing_upstream_evidence:
        console.print(f"- {evidence_type}")


def _print_ascap_breakdown(label: str, counts: tuple[tuple[str, int], ...]) -> None:
    console.print()
    console.print(f"[bold]{label}[/bold]")
    if counts:
        for value, count in counts:
            console.print(f"- {value}: {count}")
    else:
        console.print("- none: 0")


def _print_validation_text_result(
    raw_records: tuple[RawEvidenceRecord, ...],
    batch: EvidenceImportBatch,
) -> None:
    console.print("[bold]SongTrace Evidence Validation[/bold]")
    console.print()
    console.print(f"Batch ID: {batch.metadata.id}")
    console.print(f"Source name: {batch.metadata.source_name}")
    console.print(f"Imported at: {batch.metadata.imported_at.isoformat()}")
    console.print(f"Raw records: {len(raw_records)}")
    console.print(f"Evidence: {len(batch.evidence)}")
    console.print("Evidence IDs:")
    for item in batch.evidence:
        console.print(f"- {item.id}")


def _print_validation_json_result(
    raw_records: tuple[RawEvidenceRecord, ...],
    batch: EvidenceImportBatch,
) -> None:
    payload = {
        "batch_id": str(batch.metadata.id),
        "source_name": batch.metadata.source_name,
        "imported_at": batch.metadata.imported_at.isoformat(),
        "raw_record_count": len(raw_records),
        "evidence_count": len(batch.evidence),
        "evidence_ids": [str(item.id) for item in batch.evidence],
    }
    print(json.dumps(payload, sort_keys=True))


def _print_import_error(error: EvidenceImportError) -> None:
    report = error.report

    error_console.print("[bold red]Evidence import failed.[/bold red]")
    error_console.print(f"Rejected record index: {report.rejected_record_index}")
    error_console.print(f"Accepted record count: {report.accepted_record_count}")
    if report.rejected_source_name is not None:
        error_console.print(f"Source: {report.rejected_source_name}")
    if report.rejected_reference is not None:
        error_console.print(f"Reference: {report.rejected_reference}")
    if report.rejected_record_id is not None:
        error_console.print(f"Record ID: {report.rejected_record_id}")
    error_console.print(f"Error: {report.error_message}")


def _print_source_error(error: Exception) -> None:
    error_console.print("[bold red]Evidence source failed.[/bold red]")
    error_console.print(f"Error: {error}")


def _load_raw_records(path: Path) -> tuple[RawEvidenceRecord, ...]:
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
