from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from songtrace import __version__
from songtrace.application import (
    CsvRawEvidenceSource,
    EvidenceImporter,
    EvidenceImportError,
    InvestigationService,
    JsonRawEvidenceSource,
    ObservationExtractor,
    RawEvidenceRecord,
    SimpleInvestigator,
    XlsxRawEvidenceSource,
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
) -> None:
    """Run the deterministic investigation pipeline for a raw evidence file."""

    try:
        raw_records = _load_raw_records(evidence_file)
        evidence = EvidenceImporter().import_records(raw_records)
    except EvidenceImportError as error:
        _print_import_error(error)
        raise typer.Exit(1) from error
    except ValueError as error:
        _print_source_error(error)
        raise typer.Exit(1) from error

    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    console.print("[bold]SongTrace Evidence Investigation[/bold]")
    console.print()
    console.print(f"Evidence: {len(evidence)}")
    console.print(f"Observations: {len(observations)}")
    console.print(f"Conclusions: {len(result.conclusions)}")

    if result.conclusions:
        console.print()
        console.print("[bold]Conclusions[/bold]")
        for conclusion in result.conclusions:
            console.print(f"- {conclusion.statement}")


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


def _print_source_error(error: ValueError) -> None:
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
