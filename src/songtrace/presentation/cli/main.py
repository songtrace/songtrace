from pathlib import Path
from typing import Annotated

import typer

from songtrace import __version__
from songtrace.application import InvestigationService, ObservationExtractor, SimpleInvestigator
from songtrace.domain.evidence import Evidence
from songtrace.domain.track import TrackIdentity
from songtrace.presentation.cli.errors import print_source_error
from songtrace.presentation.cli.loading import (
    load_and_import_ascap_layout_a_evidence,
    load_and_import_batch,
    load_and_import_evidence,
    load_and_import_playlist_placement_batch,
    load_and_import_playlist_placement_investigation_evidence,
    load_and_import_playlist_platform_csv_investigation_evidence,
)
from songtrace.presentation.cli.options import (
    parse_optional_batch_id,
    parse_optional_imported_at,
    parse_output_format,
)
from songtrace.presentation.cli.output import (
    console,
    print_ascap_work_summary_text_result,
    print_investigation_json_result,
    print_investigation_text_result,
    print_spotify_api_access_json_status,
    print_spotify_api_access_text_status,
    print_spotify_environment_json_status,
    print_spotify_environment_text_status,
    print_spotify_track_metadata_json_result,
    print_spotify_track_metadata_text_result,
    print_validation_json_result,
    print_validation_text_result,
)
from songtrace.providers import (
    lookup_spotify_track_metadata,
    profile_ascap_csv_layout,
    summarize_ascap_work,
    validate_spotify_api_access,
    validate_spotify_environment,
)

app = typer.Typer(
    name="songtrace",
    help="Investigate why song performance changes.",
    no_args_is_help=True,
)

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


@app.command("spotify-track-lookup")
def spotify_track_lookup_command(
    spotify_track_id: Annotated[
        str,
        typer.Argument(help="Spotify track ID to look up."),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Lookup safe Spotify track metadata without importing evidence."""

    output_format = parse_output_format(output)
    try:
        metadata = lookup_spotify_track_metadata(spotify_track_id)
    except ValueError as error:
        print_source_error(error)
        raise typer.Exit(1) from error

    match output_format:
        case "text":
            print_spotify_track_metadata_text_result(metadata)
        case "json":
            print_spotify_track_metadata_json_result(metadata)


@app.command("validate-spotify-api-access")
def validate_spotify_api_access_command(
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Validate Spotify API access without exposing credentials or tokens."""

    output_format = parse_output_format(output)
    status = validate_spotify_api_access()

    match output_format:
        case "text":
            print_spotify_api_access_text_status(status)
        case "json":
            print_spotify_api_access_json_status(status)

    if not status.access_granted:
        raise typer.Exit(1)


@app.command("validate-spotify-environment")
def validate_spotify_environment_command(
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
) -> None:
    """Validate local Spotify developer environment variables without exposing values."""

    output_format = parse_output_format(output)
    status = validate_spotify_environment()

    match output_format:
        case "text":
            print_spotify_environment_text_status(status)
        case "json":
            print_spotify_environment_json_status(status)

    if not status.is_configured:
        raise typer.Exit(1)


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

    output_format = parse_output_format(output)
    _raw_records, evidence = load_and_import_evidence(evidence_file)
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            print_investigation_text_result(evidence, observations, result.conclusions)
        case "json":
            print_investigation_json_result(evidence, observations, result.conclusions)


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

    output_format = parse_output_format(output)
    _raw_records, evidence = load_and_import_playlist_placement_investigation_evidence(
        playlist_file,
        tuple(evidence_files),
    )
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            print_investigation_text_result(evidence, observations, result.conclusions)
        case "json":
            print_investigation_json_result(evidence, observations, result.conclusions)


@app.command("investigate-playlist-platform-csv")
def investigate_playlist_platform_csv(
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
    platform_files: Annotated[
        list[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="One or more provider-neutral platform activity CSV files.",
        ),
    ],
    output: Annotated[
        str,
        typer.Option(
            "--output",
            help="Output format: text or json.",
        ),
    ] = "text",
    track_artist: Annotated[
        str | None,
        typer.Option(
            "--track-artist",
            help="Optional exact track artist filter.",
        ),
    ] = None,
    track_title: Annotated[
        str | None,
        typer.Option(
            "--track-title",
            help="Optional exact track title filter.",
        ),
    ] = None,
    track_isrc: Annotated[
        str | None,
        typer.Option(
            "--track-isrc",
            help="Optional exact track ISRC filter.",
        ),
    ] = None,
) -> None:
    """Investigate playlist placement evidence with platform activity CSV evidence."""

    if not platform_files:
        raise typer.BadParameter(
            "at least one platform activity CSV file is required",
            param_hint="platform_files",
        )

    output_format = parse_output_format(output)
    track_filter = _parse_track_filter(track_artist, track_title, track_isrc)
    _raw_records, evidence = load_and_import_playlist_platform_csv_investigation_evidence(
        playlist_file,
        tuple(platform_files),
    )
    if track_filter is not None:
        evidence = _filter_evidence_by_track(evidence, track_filter)
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            print_investigation_text_result(evidence, observations, result.conclusions)
        case "json":
            print_investigation_json_result(evidence, observations, result.conclusions)


def _parse_track_filter(
    artist: str | None,
    title: str | None,
    isrc: str | None,
) -> TrackIdentity | None:
    artist = _normalize_optional_text(artist)
    title = _normalize_optional_text(title)
    isrc = _normalize_optional_text(isrc)

    if artist is None and title is None and isrc is None:
        return None

    if artist is None or title is None:
        raise typer.BadParameter(
            "track filtering requires both --track-artist and --track-title",
            param_hint="--track-artist/--track-title",
        )

    return TrackIdentity(artist=artist, title=title, isrc=isrc)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    return value.strip()


def _filter_evidence_by_track(
    evidence: tuple[Evidence, ...],
    track: TrackIdentity,
) -> tuple[Evidence, ...]:
    return tuple(item for item in evidence if item.track == track)


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

    output_format = parse_output_format(output)
    _raw_records, evidence = load_and_import_ascap_layout_a_evidence(csv_file)
    observations = ObservationExtractor().extract(evidence)
    result = SimpleInvestigator().investigate(observations)

    match output_format:
        case "text":
            print_investigation_text_result(evidence, observations, result.conclusions)
        case "json":
            print_investigation_json_result(evidence, observations, result.conclusions)


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
        print_source_error(error)
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

    output_format = parse_output_format(output)
    try:
        summary = summarize_ascap_work(
            tuple(paths),
            work_id=work_id,
            work_title_query=work_title,
        )
    except (FileNotFoundError, ValueError) as error:
        print_source_error(error)
        raise typer.Exit(1) from error

    match output_format:
        case "text":
            print_ascap_work_summary_text_result(
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

    output_format = parse_output_format(output)
    parsed_batch_id = parse_optional_batch_id(batch_id)
    parsed_imported_at = parse_optional_imported_at(imported_at)
    raw_records, batch = load_and_import_batch(
        evidence_file,
        source_name=source_name,
        batch_id=parsed_batch_id,
        imported_at=parsed_imported_at,
    )

    match output_format:
        case "text":
            print_validation_text_result(raw_records, batch)
        case "json":
            print_validation_json_result(raw_records, batch)


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

    output_format = parse_output_format(output)
    parsed_batch_id = parse_optional_batch_id(batch_id)
    parsed_imported_at = parse_optional_imported_at(imported_at)
    raw_records, batch = load_and_import_playlist_placement_batch(
        playlist_file,
        source_name=source_name,
        batch_id=parsed_batch_id,
        imported_at=parsed_imported_at,
    )

    match output_format:
        case "text":
            print_validation_text_result(raw_records, batch)
        case "json":
            print_validation_json_result(raw_records, batch)
