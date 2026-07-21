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
