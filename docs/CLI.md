# SongTrace CLI Reference

SongTrace provides a small command-line interface for local evidence validation and deterministic investigations.

The CLI is intentionally provider-neutral. It loads raw evidence files into `RawEvidenceRecord` objects, imports them into immutable domain `Evidence`, and optionally runs the deterministic investigation pipeline. The reasoning engine does not know whether evidence came from JSON, CSV, XLSX, or a future connector.

## Commands

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

Run the current deterministic investigation pipeline for a local raw evidence file.

```sh
uv run songtrace investigate-evidence examples/simple_investigation_evidence.json
```

This command runs:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
Evidence -> ObservationExtractor -> Observation -> SimpleInvestigator -> Conclusion
```

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

The CLI currently selects the raw evidence source by file extension:

| Extension | Source |
| --- | --- |
| `.json` | `JsonRawEvidenceSource` |
| `.csv` | `CsvRawEvidenceSource` |
| `.xlsx` | `XlsxRawEvidenceSource` |

These are generic local file sources, not provider-specific connectors.

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
