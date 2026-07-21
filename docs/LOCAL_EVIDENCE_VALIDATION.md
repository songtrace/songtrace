# Local Evidence Validation Guide

## Purpose

SongTrace should eventually be validated against real-world exports, reports, statements, and source files. This guide explains how to do that safely during local development without committing private data or prematurely introducing provider-specific connectors.

Local evidence validation is an architecture feedback activity. Its goal is to learn whether real files can be normalized into SongTrace's current provider-neutral evidence model:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

It is not a commitment to implement a provider integration yet.

## When to use local real data

Local real-data validation is appropriate when you want to answer questions such as:

- Can real export rows be mapped into `RawEvidenceRecord` fields?
- Are existing `EvidenceKind` values sufficient for the evidence being tested?
- Are existing `EvidenceSignal` values too narrow or ambiguous?
- Is `source_name` enough to preserve basic provenance for this source?
- Are `occurred_at`, `observed_at`, and `reference` expressive enough for the file?
- Are validation errors clear enough to help a user fix malformed input?
- Does the import remain deterministic across repeated runs?
- Does private source data reveal a concrete need for new provider-neutral metadata?

If local validation reveals a gap, document the gap and create a focused ticket. Do not add broad abstractions until the gap is tied to a current product need.

## Private data rules

Do not commit private or sensitive data to the repository.

This includes:

- royalty statements
- distributor exports
- platform analytics exports
- private CSV, XLSX, PDF, or JSON files
- API credentials
- OAuth tokens
- customer, artist, writer, label, publisher, or financial data
- screenshots or logs containing private data

Use synthetic fixtures for committed automated tests. Real files may be used locally only when they are authorized for your own development environment.

## Recommended local file locations

Keep private validation files outside the repository when possible, for example:

```text
~/songtrace-private-fixtures/
~/Documents/songtrace-private-fixtures/
```

If a file must be near the working tree temporarily, use the repository-local ignored workspace:

```text
.songtrace-private/
```

This directory is ignored by git and is intended only for local private validation files. Do not place committed fixtures, generated examples, source code, credentials, or documentation there.

Even when using an ignored local workspace, verify `git status` before every commit.

Before committing, always run:

```sh
git status --short
```

No private validation file should appear in the output. If a private file appears, stop and move it outside the repository or into `.songtrace-private/` before continuing.

## Current supported local source formats

SongTrace currently has generic raw evidence sources for:

- JSON: `JsonRawEvidenceSource`
- CSV: `CsvRawEvidenceSource`
- XLSX: `XlsxRawEvidenceSource`

These sources expect provider-neutral evidence fields. They are not provider-specific importers.

### Required fields

Generic raw evidence files currently require:

- `id`
- `source_name`
- `kind`
- `summary`
- `occurred_at`
- `signals`

The `signals` field must be present in generic CSV, XLSX, and JSON records. It may be blank or empty when evidence has no currently defined structured signal. See [Evidence Semantics](EVIDENCE_SEMANTICS.md) for current signal compatibility and timestamp guidance.

### Optional fields

Generic raw evidence files may include:

- `observed_at`
- `reference`

`occurred_at` and `observed_at`, when supplied, must be timezone-aware ISO datetimes.

## Smoke-test workflow

Start by validating that a local file can cross the import boundary:

```sh
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.csv
```

The command supports the existing generic raw evidence source formats:

```sh
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.json
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.csv
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.xlsx
```

It loads raw records, imports validated domain evidence, and prints import batch metadata, raw record counts, evidence counts, and evidence IDs. It does not extract observations or run investigation rules, so it is the best first check for real-world files whose evidence may not yet map to SongTrace's current reasoning rules.

The default validation source name is `local_file` so local filenames are not exposed in output. Use `--source-name` when a provider-neutral source label is useful:

```sh
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.csv --source-name local_statement_upload
```

For scripts or repeatable local checks, request a small provider-neutral JSON validation summary:

```sh
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.csv --output json
```

When comparing validation output across runs, supply deterministic batch metadata:

```sh
uv run songtrace validate-evidence /absolute/path/to/local/private/evidence.csv \
  --output json \
  --batch-id 00000000-0000-0000-0000-000000000901 \
  --imported-at 2026-07-21T12:00:00+00:00
```

`--imported-at` must be a timezone-aware ISO datetime.

After the file imports successfully, run the current deterministic investigation pipeline:

```sh
uv run songtrace investigate-evidence /absolute/path/to/local/private/evidence.csv
```

For investigation scripts, request JSON output:

```sh
uv run songtrace investigate-evidence /absolute/path/to/local/private/evidence.csv --output json
```

The investigation JSON output includes counts, evidence IDs, observation IDs, and conclusion traceability fields. CLI JSON output is intended for local validation automation, not as a full report export format.

For expected validation failures, the command exits non-zero and prints a concise provider-neutral text error instead of a Python traceback. Import validation errors include the rejected record index, accepted record count before rejection, available source/reference/record ID context, and the validation message.

For deeper debugging, use the existing source that matches the file shape you want to validate:

```python
from datetime import UTC, datetime
from pathlib import Path

from songtrace.application import (
    CsvRawEvidenceSource,
    EvidenceImporter,
    JsonRawEvidenceSource,
    ObservationExtractor,
    SimpleInvestigator,
    XlsxRawEvidenceSource,
)

path = Path("/absolute/path/to/local/private/evidence.csv")
source = CsvRawEvidenceSource(path)

# Alternatives:
# source = JsonRawEvidenceSource(Path("/absolute/path/to/local/private/evidence.json"))
# source = XlsxRawEvidenceSource(Path("/absolute/path/to/local/private/evidence.xlsx"))

records = source.load()
evidence = EvidenceImporter(clock=lambda: datetime.now(UTC)).import_records(records)
observations = ObservationExtractor(clock=lambda: datetime.now(UTC)).extract(evidence)
result = SimpleInvestigator().investigate(observations)

print(f"records: {len(records)}")
print(f"evidence: {len(evidence)}")
print(f"observations: {len(observations)}")
print(f"conclusions: {len(result.conclusions)}")
```

Both workflows verify the current deterministic pipeline without adding a provider connector.

## Interpreting failures

A local validation failure can mean different things:

| Failure type | Likely meaning | Preferred response |
| --- | --- | --- |
| File parse failure | The file does not match the generic JSON, CSV, or XLSX shape. | Use a temporary local transformation outside the repo, or create a future connector ticket if the format is important. |
| Invalid enum value | The evidence does not fit current `EvidenceKind` or `EvidenceSignal` values. | Document the missing provider-neutral classification. |
| Missing timestamp | The source may require different event-period modeling. | Document the date semantics before changing the model. |
| Missing provenance | `source_name` and `reference` may not be enough. | Create a focused provenance metadata ticket if justified. |
| No observations | The evidence imported successfully but current observation extraction rules do not use it yet. | Consider whether a new deterministic observation is justified. |
| No conclusions | The evidence produced observations but no catalog rule matched. | Consider whether a new `InvestigationRule` is justified. |

Do not treat every local validation failure as an implementation bug. Some failures are useful evidence that the product model needs a future, focused extension.

## ASCAP-style royalty statements

ASCAP CSV and PDF royalty statements are useful examples of future private validation files. They should remain local and private.

They may eventually help validate whether SongTrace can:

- import ASCAP CSV royalty statements
- import ASCAP PDF royalty statements
- normalize both into provider-neutral evidence
- reconcile both representations of the same statement
- preserve provenance for every imported fact
- record confidence where appropriate
- verify deterministic imports through automated tests

Do not implement ASCAP-specific parsing, royalty-statement reconciliation, or PDF ingestion until a dedicated ticket is created.

For current provider-neutral royalty evidence semantics, see [Evidence Semantics](EVIDENCE_SEMANTICS.md).

## Private-safe ASCAP CSV layout profiling

ASCAP CSV royalty statements can use more than one provider-specific layout. Before implementing an ASCAP connector, use the private-safe profiler to compare local files without committing private data:

```sh
uv run songtrace profile-ascap-csv-layout .songtrace-private/ascap/42278445.csv
```

The profiler emits JSON containing aggregate schema information only. It can classify ASCAP statement type when that is safely inferable from filename or header shape, such as `domestic` or `international_incoming`. It does not normalize rows, produce `RawEvidenceRecord`, create domain `Evidence`, or run investigations.

The statement-type profile is intended to show whether Domestic and International Incoming statements require different future normalization behavior. It is not a domain model and should not be used by the reasoning engine.

Do not paste profiler output into documentation until you have verified it contains no private row values, royalty amounts, account identifiers, work titles, party names, writer names, customer data, or screenshots.

## ASCAP CSV sources

SongTrace includes a narrow `AscapCsvRawEvidenceSource` for the profiled 41-column ASCAP Domestic/layout A shape. It converts supported ASCAP rows into provider-neutral `RawEvidenceRecord` objects using `royalty_activity` and `royalty_reported`.

SongTrace also includes `AscapInternationalIncomingCsvRawEvidenceSource` for the profiled International Incoming/layout B shape. It uses the same provider-neutral royalty evidence semantics while preserving a distinct safe reference prefix for traceability.

To run the current deterministic pipeline against a private layout A CSV file:

```sh
uv run songtrace investigate-ascap-csv-layout-a .songtrace-private/ascap/42278445.csv
```

These sources are intentionally not a general ASCAP connector. They do not support PDF statements, reconciliation, APIs, OAuth, or persistence.

## ASCAP work-level summaries

Use `summarize-ascap-work` to safely inspect aggregate ASCAP activity for a specific work across supported private local CSV statements:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>"
```

The command can also match by a case-insensitive work title query for local exploratory use:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-title "Everything Is Fading"
```

The output is intentionally aggregate-only. By default, it reports counts for scanned files, matched files, matched rows, statement types, distribution periods/dates, territories/countries, and revenue classes. It does not print the work ID, work title, filenames, account identifiers, party names, writer names, royalty amounts, or row values.

Use `--include-breakdowns` only for local exploratory analysis when aggregate labels are useful:

```sh
uv run songtrace summarize-ascap-work .songtrace-private/ascap --work-id "<private-work-id>" --include-breakdowns
```

Breakdowns may include distribution periods/dates, territories/countries, revenue classes, and statement types. They still do not include row-level values, royalty amounts, account IDs, party names, writer names, work IDs, work titles, filenames, or source row numbers.

This command helps identify what evidence exists for a real work before expanding the domain model. It does not create `RawEvidenceRecord`, domain `Evidence`, observations, conclusions, or recommendations.

## API-backed sources are later

Local file validation should happen before live API integrations.

API-backed sources introduce additional concerns that are separate from the evidence model:

- OAuth and delegated authorization
- API keys and secret storage
- pagination
- rate limits
- retries
- network failures
- provider terms
- schema drift
- fixture recording
- data retention and privacy policies

Those concerns should be designed only after the evidence model and import boundary have been validated against local files. The reasoning engine must remain unaware of whether evidence came from a local CSV, an OAuth API, a PDF report, or a future webhook.

## What to document after a local validation run

When a private local validation reveals something useful, capture only safe, non-sensitive notes:

- source type tested, such as `ASCAP CSV statement` or `distributor XLSX export`
- whether it could be mapped to existing `RawEvidenceRecord` fields
- missing provider-neutral fields or enum values
- unclear timestamp semantics
- provenance or confidence gaps
- deterministic ordering concerns
- recommended next focused ticket

Do not include private row values, royalty amounts, account identifiers, names, statements, credentials, or screenshots.

## Validation notes

Repo-safe validation findings may be stored under `docs/validation/` when they document architecture lessons without exposing private data.
