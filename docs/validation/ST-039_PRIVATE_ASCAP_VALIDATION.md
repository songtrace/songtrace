# ST-039 Private ASCAP Validation Findings

## Purpose

This note captures repo-safe findings from validating the current SongTrace import boundary against a private local ASCAP CSV statement sample.

The private source file is intentionally not committed. This document does not include row values, royalty amounts, account identifiers, party names, work titles, writer names, statement recipient data, or screenshots.

## Source tested

- Source type: ASCAP CSV royalty statement
- Local-only file location: `.songtrace-private/`
- Rows observed: 525
- Columns observed: 41
- PDF sample: not present in the local workspace during this validation

## Current direct import result

Running the existing generic CLI directly against the private ASCAP CSV failed before import:

```text
Evidence source failed.
Error: Evidence CSV is missing required field(s): id, kind, occurred_at, signals, source_name, summary
```

This is expected and healthy behavior. The ASCAP CSV is provider-shaped statement data, while `CsvRawEvidenceSource` expects provider-neutral raw evidence rows shaped for SongTrace:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

The generic CSV source should not learn ASCAP-specific column semantics.

## Architecture findings

### What works today

- The import boundary correctly rejects a provider-shaped CSV instead of silently guessing how to map private royalty data.
- `EvidenceKind.ROYALTY_ACTIVITY` already exists as a provider-neutral category for royalty-related evidence.
- Domain `Evidence` permits an empty `signals` tuple, which is appropriate for evidence that is valid but does not yet have a defined structured signal.
- Validation errors are concise and do not leak row contents.
- `.songtrace-private/` remains the right local workspace for private samples that must stay out of git.

### Concrete compatibility issue found

CSV and XLSX raw evidence sources rejected blank `signals` values even though domain `Evidence` and JSON raw evidence records allow empty signal tuples.

That inconsistency matters for royalty-statement-derived evidence because SongTrace currently has a royalty evidence kind but no royalty-specific `EvidenceSignal` values.

ST-039 fixes the generic CSV/XLSX behavior so blank `signals` fields load as `()` instead of being rejected.

### What does not fit yet

The ASCAP CSV contains statement-level and usage-level provider data that cannot be directly represented by the current generic raw evidence shape without a normalization step.

Provider-neutral modeling questions remain open:

- What royalty facts should become evidence?
- Which dates represent the evidence event: performance period, distribution period, original distribution date, or import date?
- What reference format should identify a royalty-statement-derived fact without exposing private statement data?
- Which fields are provenance metadata versus evidence summary content?
- Which royalty signals, if any, should be added as provider-neutral `EvidenceSignal` values?
- How should CSV and future PDF representations of the same statement be reconciled?

## Recommended next ticket

Do not implement an ASCAP connector yet.

The next justified implementation ticket was:

```text
ST-040: Define provider-neutral royalty evidence signals and timestamp semantics
```

That ticket should remain independent of ASCAP-specific parsing and should use synthetic fixtures.

## Non-goals confirmed

This validation did not introduce:

- committed private ASCAP files
- ASCAP-specific source code
- PDF parsing
- provider connector abstractions
- OAuth, API, persistence, or reconciliation behavior
