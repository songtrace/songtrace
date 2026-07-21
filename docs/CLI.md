# SongTrace CLI Reference

SongTrace provides a small command-line interface for local evidence validation and deterministic investigations.

The CLI is intentionally provider-neutral. It loads raw evidence files into `RawEvidenceRecord` objects, imports them into immutable domain `Evidence`, and optionally runs the deterministic investigation pipeline. The reasoning engine does not know whether evidence came from JSON, CSV, XLSX, or a future connector.

## Commands

### `export-spotify-playlist-placement`

Check current Spotify playlist membership and export a positive match as raw playlist-placement evidence.

```sh
uv run songtrace export-spotify-playlist-placement 37i9dQZF1DX0XUsuxWHRQd 7zHxneKcojYp1eFkGO0e2N \
  --occurred-at 2026-07-21T12:00:00+00:00 \
  --track-artist "Warrel Dane" \
  --track-title "Everything Is Fading" \
  --track-isrc "GBDHC2120401"
```

This command writes `playlist_activity` evidence with the `playlist_placement` signal only when the track is currently found in the playlist. It does not infer when the track was added, whether the playlist caused a stream spike, or whether this placement existed historically.

To write the JSON to a private local file:

```sh
uv run songtrace export-spotify-playlist-placement 37i9dQZF1DX0XUsuxWHRQd 7zHxneKcojYp1eFkGO0e2N \
  --occurred-at 2026-07-21T12:00:00+00:00 \
  --output-file .songtrace-private/everything-is-fading/spotify-playlist-placement.json
```

### `spotify-playlist-track-lookup`

Check whether a known Spotify playlist currently contains a known Spotify track.

```sh
uv run songtrace spotify-playlist-track-lookup 37i9dQZF1DX0XUsuxWHRQd 7zHxneKcojYp1eFkGO0e2N
```

This is a provider-facing validation probe. It inspects current playlist membership only. It does not create playlist-placement evidence, import evidence, infer historical placement, or attribute a stream spike to the playlist.

For machine-readable output:

```sh
uv run songtrace spotify-playlist-track-lookup 37i9dQZF1DX0XUsuxWHRQd 7zHxneKcojYp1eFkGO0e2N --output json
```

### `export-spotify-track-metadata`

Look up Spotify track metadata and export it as a JSON array compatible with the existing raw evidence import boundary.

```sh
uv run songtrace export-spotify-track-metadata 0abc123exampleTrackId \
  --occurred-at 2026-07-21T12:00:00+00:00
```

This command creates identity metadata evidence only. It does not infer engagement, playlist placement, stream growth, save growth, royalties, attribution, observations, or conclusions.

To write the JSON to a private local file:

```sh
uv run songtrace export-spotify-track-metadata 0abc123exampleTrackId \
  --occurred-at 2026-07-21T12:00:00+00:00 \
  --observed-at 2026-07-21T12:05:00+00:00 \
  --output-file .songtrace-private/everything-is-fading/spotify-track-metadata.json
```

The exported JSON can be validated with:

```sh
uv run songtrace validate-evidence .songtrace-private/everything-is-fading/spotify-track-metadata.json
```

### `spotify-track-lookup`

Look up safe Spotify track metadata by Spotify track ID. This command is a development probe for validating track identity mapping before Spotify evidence import exists.

```sh
uv run songtrace spotify-track-lookup 0abc123exampleTrackId
```

The command uses local Spotify developer credentials and the client credentials flow. It prints only safe metadata: Spotify track ID, title, artist names, album name when available, and ISRC when available. It does not print or store credentials or tokens, import evidence, run OAuth, or perform attribution.

For machine-readable output:

```sh
uv run songtrace spotify-track-lookup 0abc123exampleTrackId --output json
```

The command exits non-zero when credentials are missing, token validation fails, Spotify returns an error, the response is invalid, or the track ID is blank.

### `validate-spotify-api-access`

Validate whether local Spotify developer credentials can obtain a client-credentials access token without exposing credential or token values.

```sh
uv run songtrace validate-spotify-api-access
```

This command reads the same environment variables as `validate-spotify-environment` and makes a single request to Spotify Accounts using the client credentials flow. It reports only safe success/failure status. It does not print tokens, store tokens, call Spotify Web API data endpoints, run a browser OAuth flow, or create evidence.

For machine-readable output:

```sh
uv run songtrace validate-spotify-api-access --output json
```

The command exits non-zero when required credentials are missing or token validation fails.

### `validate-spotify-environment`

Validate whether local Spotify developer environment variables are present without exposing credential values.

```sh
uv run songtrace validate-spotify-environment
```

Required environment variables:

- `SONGTRACE_SPOTIFY_CLIENT_ID`
- `SONGTRACE_SPOTIFY_CLIENT_SECRET`

The command reports only safe presence/missing status. It does not print credential values, call Spotify APIs, run OAuth, exchange tokens, store secrets, or create evidence.

For machine-readable output:

```sh
uv run songtrace validate-spotify-environment --output json
```

The command exits non-zero when either required variable is missing or blank.

### `validate-evidence`

Validate that a local raw evidence file can be imported into domain `Evidence`.

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json
```

This command checks the import boundary only:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

It does not extract observations, evaluate rules, or produce conclusions.

#### JSON output

Use JSON output for scripts and repeatable local checks:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json --output json
```

The JSON payload includes:

- `batch_id`
- `source_name`
- `imported_at`
- `raw_record_count`
- `evidence_count`
- `evidence_ids`

#### Deterministic validation metadata

For stable local comparisons, pass deterministic batch metadata:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json \
  --output json \
  --batch-id 00000000-0000-0000-0000-000000000901 \
  --imported-at 2026-07-21T12:00:00+00:00
```

`--batch-id` must be a valid UUID.

`--imported-at` must be a timezone-aware ISO datetime.

#### Source name

Use `--source-name` to label the import batch with a provider-neutral source name:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json \
  --source-name local_fixture
```

The source name is import metadata. It should not introduce provider-specific behavior into the reasoning model.

### `validate-playlist-placement-csv`

Validate a local provider-neutral playlist placement CSV file through the import boundary.

```sh
uv run songtrace validate-playlist-placement-csv /absolute/path/to/playlist-placements.csv
```

This command uses:

```text
PlaylistPlacementCsvRawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

It does not extract observations, evaluate rules, produce conclusions, enrich playlist metadata, or contact external APIs.

The required CSV shape is intentionally narrow:

```csv
id,source_name,summary,occurred_at,observed_at,reference
```

`id`, `source_name`, `summary`, `occurred_at`, and `reference` are required. `observed_at` is optional. Datetimes must be timezone-aware ISO datetimes.

Playlist placement CSV files may also include optional track identity fields:

```csv
track_artist,track_title,track_isrc
```

If track identity is supplied, `track_artist` and `track_title` are required and must not be blank. `track_isrc` is optional. Validation and investigation output do not print track identity by default.

For machine-readable validation output:

```sh
uv run songtrace validate-playlist-placement-csv /absolute/path/to/playlist-placements.csv --output json
```

The command supports the same validation metadata options as `validate-evidence`:

```sh
uv run songtrace validate-playlist-placement-csv /absolute/path/to/playlist-placements.csv \
  --source-name local_playlist_fixture \
  --batch-id 00000000-0000-0000-0000-000000000901 \
  --imported-at 2026-07-21T12:00:00+00:00
```

Use this command when you have local playlist placement evidence that should normalize to `playlist_activity` with `playlist_placement`. The generic `validate-evidence` command still treats `.csv` files as generic raw evidence CSVs and does not auto-detect this specialized shape.

SongTrace also provides `PlatformActivityCsvRawEvidenceSource` for provider-neutral local stream/save growth evidence. Its required CSV fields are:

```csv
id,source_name,summary,occurred_at,observed_at,reference,signal
```

`signal` must be `stream_growth` or `save_growth`. Use `investigate-playlist-platform-csv` when combining this shape with playlist placement evidence. This source is intentionally explicit and is not auto-detected by the generic CLI CSV loader.

### `investigate-playlist-platform-csv`

Run the deterministic investigation pipeline using one local playlist placement CSV file plus one or more local platform activity CSV files.

```sh
uv run songtrace investigate-playlist-platform-csv \
  /absolute/path/to/playlist-placements.csv \
  /absolute/path/to/platform-activity.csv
```

This command uses:

```text
PlaylistPlacementCsvRawEvidenceSource -> RawEvidenceRecord
PlatformActivityCsvRawEvidenceSource -> RawEvidenceRecord
RawEvidenceRecord -> EvidenceImporter -> Evidence
Evidence -> ObservationExtractor -> Observation -> SimpleInvestigator -> Conclusion
```

Records are combined deterministically: playlist placement records first, followed by platform activity files in argument order, preserving each file's source order.

For machine-readable output:

```sh
uv run songtrace investigate-playlist-platform-csv \
  /absolute/path/to/playlist-placements.csv \
  /absolute/path/to/platform-activity.csv \
  --output json
```

Use this command for local attribution experiments where you have known playlist placement evidence and platform stream/save growth evidence.

To focus a multi-track local file set on one explicit track identity, provide an exact track filter:

```sh
uv run songtrace investigate-playlist-platform-csv \
  /absolute/path/to/playlist-placements.csv \
  /absolute/path/to/platform-activity.csv \
  --track-artist "Warrel Dane" \
  --track-title "Everything Is Fading" \
  --track-isrc "USABC0800001"
```

If any track filter option is supplied, `--track-artist` and `--track-title` are required. `--track-isrc` is optional, but when supplied it participates in exact matching. Evidence without track identity is excluded when a track filter is active. Successful text and JSON output remain privacy-safe and do not print track identity by default.

It does not enrich playlist metadata, search Spotify, perform historical playlist lookup, contact APIs, infer missing placements, or generate recommendations.

### `investigate-playlist-placement-csv`

Run the deterministic investigation pipeline using one local playlist placement CSV file plus one or more supplemental generic raw evidence files.

```sh
uv run songtrace investigate-playlist-placement-csv \
  /absolute/path/to/playlist-placements.csv \
  /absolute/path/to/audience-evidence.json
```

This command uses:

```text
PlaylistPlacementCsvRawEvidenceSource -> RawEvidenceRecord
Generic RawEvidenceSource -> RawEvidenceRecord
RawEvidenceRecord -> EvidenceImporter -> Evidence
Evidence -> ObservationExtractor -> Observation -> SimpleInvestigator -> Conclusion
```

Records are combined deterministically: playlist placement records first, followed by supplemental evidence files in argument order, preserving each file's source order.

For machine-readable output:

```sh
uv run songtrace investigate-playlist-placement-csv \
  /absolute/path/to/playlist-placements.csv \
  /absolute/path/to/audience-evidence.json \
  --output json
```

Use this command to test whether known local playlist placement evidence can explain stream/save evidence through the existing rule catalog when supplemental evidence is already in generic JSON, CSV, or XLSX raw evidence shape. For local platform activity CSV files, prefer `investigate-playlist-platform-csv`.

It does not enrich playlist metadata, search Spotify, perform historical playlist lookup, contact APIs, infer missing placements, or generate recommendations.

### `investigate-ascap-csv-layout-a`

Run the current deterministic investigation pipeline for a private local ASCAP CSV file using the profiled 41-column layout A.

```sh
uv run songtrace investigate-ascap-csv-layout-a .songtrace-private/ascap/42278445.csv
```

For machine-readable output:

```sh
uv run songtrace investigate-ascap-csv-layout-a .songtrace-private/ascap/42278445.csv --output json
```

This command uses:

```text
AscapCsvRawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
Evidence -> ObservationExtractor -> Observation -> SimpleInvestigator -> Conclusion
```

It currently produces royalty reported observations but no royalty conclusions. It supports layout A only. Unsupported ASCAP layouts fail clearly.

This command is intentionally narrow. It is not a general ASCAP connector and does not support layout B, PDFs, reconciliation, APIs, OAuth, persistence, or provider authentication.

### `profile-ascap-csv-layout`

Profile one or more private local ASCAP CSV statement files without exposing row values or sensitive statement details.

```sh
uv run songtrace profile-ascap-csv-layout .songtrace-private/ascap/42278445.csv
```

The command emits deterministic JSON with safe aggregate layout information, including:

- filenames
- row and column counts
- header shapes
- column blank/nonblank counts
- distinct nonblank counts
- date and period shape masks
- numeric parse counts without totals or values
- row-grain candidate counts
- safe statement-type classification when inferable from filename or header shape, such as `domestic` or `international_incoming`

It does not emit royalty amounts, work titles, party names, account IDs, writer names, customer data, screenshots, or row-level values.

This is a local validation helper for understanding ASCAP CSV layouts. It is not an ASCAP connector and does not produce `RawEvidenceRecord` or domain `Evidence`.

### `summarize-ascap-work`

Summarize private ASCAP CSV rows for a specific work across supported local ASCAP CSV layouts without exposing row-level values.

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>"
```

You can also match by a case-insensitive title query:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-title "Everything Is Fading"
```

For machine-readable output:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>" --output json
```

By default, the command emits aggregate counts only, including scanned files, matched files, matched rows, statement-type counts, distinct distribution periods/dates, distinct territories/countries, and distinct revenue classes. It does not print work titles, work IDs, account IDs, party names, writer names, royalty amounts, filenames, or row values.

For local-only exploratory analysis, opt in to aggregate breakdown labels and counts:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>" --include-breakdowns
```

Breakdowns may include distribution periods/dates, territories/countries, revenue classes, and statement types. They still do not include row-level values, royalty amounts, account IDs, party names, writer names, work IDs, work titles, filenames, or source row numbers.

To see what upstream evidence is still needed before SongTrace can identify an exact source of engagement, opt in to attribution gaps:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>" --include-attribution-gaps
```

Attribution gaps are deterministic guidance only. ASCAP royalty statements are downstream evidence; by themselves they cannot identify a specific playlist, social post, video, campaign, algorithmic source, or distributor usage source.

This is a private local analysis helper. It does not normalize rows into `RawEvidenceRecord`, create domain `Evidence`, run investigations, parse PDFs, reconcile statements, or generate conclusions.

### `investigate-evidence`

Run the current deterministic investigation pipeline for one or more local raw evidence files.

```sh
uv run songtrace investigate-evidence examples/simple_investigation_evidence.json
```

Multiple files are combined deterministically in argument order, preserving each file's internal record order:

```sh
uv run songtrace investigate-evidence \
  .songtrace-private/everything-is-fading/spotify-track-metadata.json \
  .songtrace-private/everything-is-fading/spotify-playlist-placement.json \
  .songtrace-private/everything-is-fading/platform-activity.json
```

This command runs:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
Evidence -> ObservationExtractor -> Observation -> SimpleInvestigator -> Conclusion
```

If any file fails to load or import, the command fails without producing partial investigation output.

#### Exact track filtering

Use exact track filtering when investigating mixed evidence files that may contain records for multiple tracks:

```sh
uv run songtrace investigate-evidence \
  .songtrace-private/everything-is-fading/spotify-track-metadata.json \
  .songtrace-private/everything-is-fading/spotify-playlist-placement.json \
  .songtrace-private/everything-is-fading/platform-activity.json \
  --track-artist "Warrel Dane" \
  --track-title "Everything Is Fading" \
  --track-isrc "GBDHC2120401"
```

If any track filter option is supplied, both `--track-artist` and `--track-title` are required. `--track-isrc` is optional, but when supplied it must also match exactly. Evidence without track identity is excluded while a track filter is active.

Track filtering is deterministic and local. It does not perform fuzzy matching, provider lookups, or automatic track identity resolution.

#### JSON output

Use JSON output for machine-readable investigation summaries:

```sh
uv run songtrace investigate-evidence examples/simple_investigation_evidence.json --output json
```

The JSON payload includes:

- evidence, observation, and conclusion counts
- evidence IDs
- observation IDs
- conclusion statements
- conclusion confidence levels
- supporting observation IDs

## Supported local evidence formats

The generic `validate-evidence` and `investigate-evidence` commands select the raw evidence source by file extension:

| Extension | Source |
| --- | --- |
| `.json` | `JsonRawEvidenceSource` |
| `.csv` | `CsvRawEvidenceSource` |
| `.xlsx` | `XlsxRawEvidenceSource` |

These are generic local file sources, not provider-specific connectors.

Specialized local source commands, such as `validate-playlist-placement-csv`, are invoked explicitly. Generic `.csv` commands do not infer specialized CSV shapes from filenames or headers.

Unsupported extensions fail clearly before import.

## Output formats

Both evidence commands support:

| Format | Usage |
| --- | --- |
| `text` | Human-readable local output. This is the default. |
| `json` | Machine-readable summaries for scripts and deterministic comparisons. |

Unsupported output formats are rejected.

## Error behavior

The CLI does not silently skip invalid records.

If source loading fails, the CLI reports an evidence source failure.

If import validation fails, the CLI reports:

- rejected record index
- accepted record count before the failure
- source, reference, and record ID when available
- the validation error message

Evidence imports remain atomic: a command either imports the full file successfully or fails without returning partial imported evidence.

## Private local data

Do not commit private exports, royalty statements, provider reports, credentials, API tokens, or real provider/customer data.

For local-only validation, prefer private files outside the repository. If private files must temporarily live near the repo, use the ignored `.songtrace-private/` directory and verify that no private files appear in:

```sh
git status --short
```

See [Local Evidence Validation](LOCAL_EVIDENCE_VALIDATION.md) for more guidance.

## Current non-goals

The CLI does not currently provide:

- provider-specific connectors
- live API integrations
- OAuth flows
- PDF parsing
- persistence or import history
- autonomous recommendations
- AI-assisted reasoning

Those capabilities should be introduced only when they solve a concrete product need while preserving provider-neutral, evidence-first architecture.
