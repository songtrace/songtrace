# Evidence Import Policy

## Purpose

SongTrace imports external records through a provider-neutral boundary before those records become domain `Evidence`.

The import policy keeps source loading, domain validation, and reasoning separate so future connectors can support many ingestion mechanisms without coupling the investigation engine to provider formats.

## Boundary

The current import pipeline is:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

- `RawEvidenceSource` loads raw transport records from a source such as JSON, CSV, XLSX, or a future connector.
- `RawEvidenceRecord` carries only the normalized fields needed to construct domain `Evidence`.
- `EvidenceImporter` constructs validated immutable domain `Evidence`.
- Observation extraction and investigation logic operate only after evidence has crossed this boundary.

Raw sources may parse provider or file formats, but they must not construct domain `Evidence`, create observations, run investigations, or expose provider-specific objects to the domain model.

## Atomic imports

`EvidenceImporter` uses an atomic import policy.

An import attempt either:

1. returns a complete immutable tuple of validated `Evidence`, or
2. raises an `EvidenceImportError` with an `ImportValidationReport`.

It must not return a partially imported evidence tuple when any record in the batch is invalid.

This applies to both:

- `EvidenceImporter.import_records(...)`
- `EvidenceImporter.import_batch(...)`

`import_batch(...)` follows the same atomic policy while also returning immutable batch metadata when the import succeeds.

## Validation failures

When validation fails, SongTrace should preserve provider-neutral context that helps identify the rejected record without exposing provider-specific internal objects.

The validation report may include:

- accepted record count before the rejection
- rejected record index
- rejected source name
- rejected reference
- rejected summary
- rejected record ID
- validation error message

The accepted record count is diagnostic context only. It does not mean partial domain evidence was returned or committed by the importer.

## Duplicate evidence IDs

Explicit evidence IDs are treated as idempotency keys within an import attempt.

If two raw records in the same import contain the same explicit evidence ID, the import fails atomically with validation context. Multiple records without explicit IDs may still be imported because the domain model generates unique IDs for them.

## Source responsibilities

Raw file sources should fail clearly and deterministically for malformed input. They should not silently skip invalid records or return partial results for partially valid files.

Current file sources include:

- `JsonRawEvidenceSource`
- `CsvRawEvidenceSource`
- `XlsxRawEvidenceSource`

Each source returns immutable `tuple[RawEvidenceRecord, ...]` values in deterministic input order.

## Non-goals

SongTrace does not currently support configurable partial imports.

The project should not introduce partial-import modes, retry policies, persistence, provider adapter frameworks, or source-specific orchestration until a concrete feature requires them.
