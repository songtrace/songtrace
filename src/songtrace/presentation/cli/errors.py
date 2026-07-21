from typing import NoReturn

import typer
from rich.console import Console

from songtrace.application import EvidenceImportError

error_console = Console(stderr=True)


def print_import_error(error: EvidenceImportError) -> None:
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


def print_source_error(error: Exception) -> None:
    error_console.print("[bold red]Evidence source failed.[/bold red]")
    error_console.print(f"Error: {error}")


def exit_with_import_error(error: EvidenceImportError) -> NoReturn:
    print_import_error(error)
    raise typer.Exit(1) from error


def exit_with_source_error(error: Exception) -> NoReturn:
    print_source_error(error)
    raise typer.Exit(1) from error
