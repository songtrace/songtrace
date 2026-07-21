import json

from rich.console import Console

from songtrace.application import EvidenceImportBatch, RawEvidenceRecord
from songtrace.domain.conclusion import Conclusion
from songtrace.domain.evidence import Evidence
from songtrace.domain.observation import Observation
from songtrace.providers import AscapWorkSummary, SpotifyEnvironmentStatus

console = Console()


def print_investigation_text_result(
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


def print_investigation_json_result(
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


def print_ascap_work_summary_text_result(
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


def print_spotify_environment_text_status(status: SpotifyEnvironmentStatus) -> None:
    console.print("[bold]SongTrace Spotify Environment[/bold]")
    console.print()
    console.print(f"Client ID: {_presence_label(status.client_id_present)}")
    console.print(f"Client secret: {_presence_label(status.client_secret_present)}")
    console.print(f"Configured: {'yes' if status.is_configured else 'no'}")
    if status.missing_variables:
        console.print("Missing variables:")
        for variable_name in status.missing_variables:
            console.print(f"- {variable_name}")


def print_spotify_environment_json_status(status: SpotifyEnvironmentStatus) -> None:
    payload = {
        "client_id_present": status.client_id_present,
        "client_secret_present": status.client_secret_present,
        "configured": status.is_configured,
        "missing_variables": list(status.missing_variables),
    }
    print(json.dumps(payload, sort_keys=True))


def _presence_label(is_present: bool) -> str:
    return "present" if is_present else "missing"


def print_validation_text_result(
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


def print_validation_json_result(
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
