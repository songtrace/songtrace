# ST-042 ASCAP CSV Layout Profile

## Purpose

This report captures repo-safe findings from profiling private local ASCAP CSV royalty statement files across multiple periods/layouts.

The private source files are intentionally not committed. This document does not include row values, royalty amounts, work titles, party names, writer names, account identifiers, customer data, screenshots, or sensitive statement details.

## Source files profiled

Three private CSV files were profiled from the ignored `.songtrace-private/` workspace:

| File label | Filename provenance | Rows | Columns | Notes |
| --- | --- | ---: | ---: | --- |
| Current renamed sample | Renamed locally | 525 | 41 | Same header shape as one numeric downloaded file. |
| Numeric downloaded sample A | Original ASCAP-style numeric filename | 499 | 41 | Same header shape as the renamed current sample. |
| Numeric downloaded sample B | Original ASCAP-style numeric filename | 122 | 26 | Different header shape. |

The original downloaded numeric filenames appear potentially meaningful as statement/download identifiers. Future connector design should preserve original filename provenance without exposing it directly in summaries or domain objects.

## Header stability

Two distinct ASCAP CSV header shapes were observed across three files.

- Header shape A: 41 columns, present in 2 of 3 files.
- Header shape B: 26 columns, present in 1 of 3 files.
- The renamed current sample and one original numeric downloaded sample share the same 41-column shape.
- The second original numeric downloaded sample uses a different 26-column shape.

This means an eventual ASCAP CSV connector should not assume a single stable ASCAP CSV schema.

## Common columns

Sixteen columns were present in all profiled files:

- `Adjustment Indicator`
- `Legal Earner Party ID`
- `Legal Earner Party Name`
- `Licensor`
- `Party ID`
- `Party Name`
- `Performance End Date`
- `Performance Start Date`
- `Program Name`
- `Role Type`
- `Statement Recipient ID`
- `Statement Recipient Name`
- `Territory`
- `Type Of Right`
- `Work ID`
- `Work Title`

Several common columns contain sensitive values or may be empty depending on the layout. Common presence does not mean each column is safe or useful for committed fixtures.

## Layout A: 41-column statement shape

The 41-column files appear to be usage/source line-item statements with statement-level, work-level, source-level, rights-level, and measure fields.

### Stable characteristics observed

- Rows: 499 and 525 in the two samples.
- Work metadata was populated:
  - `Work ID`
  - `Work Title`
- Usage/source dimensions were populated:
  - `Performance Source/Broadcast Medium`
  - `Music User Genre`
  - `Music User`
  - `Performance Type (Usage)`
- Measures were populated:
  - `Number of Plays`
  - `Credits`
  - `Dollars`
- Premium measures were present but constant zero in the profiled files:
  - `Premium Credits`
  - `Premium Dollars`
- Many optional descriptive fields were empty in all rows:
  - `Network Service`
  - `Performance Start Date`
  - `Performance End Date`
  - `Series or Film/Attraction`
  - `Program Name`
  - `Performing Artist`
  - `Composer Name`
  - `Original Distribution Date`

### Period fields

Layout A did not populate exact performance date fields in the profiled samples.

Observed period fields:

- `DistributionYear`: nonblank, shape `9999`
- `Distribution Quarter`: nonblank, shape `9`
- `Performance Quarter`: nonblank, shape `9A9999`

For this layout, `occurred_at` for normalized evidence likely needs to derive from quarter/year fields rather than exact performance start/end dates.

### Row grain

For both Layout A samples:

- `Work ID` alone was not unique.
- `Work ID + Music User` was unique for every row.
- Full rows had no exact duplicates.

This suggests the observed row grain is close to work-by-music-user line items, but a connector should not hardcode that assumption without more samples.

## Layout B: 26-column statement shape

The 26-column file appears to be a different ASCAP export layout, likely with different source/reporting semantics.

### Stable characteristics observed in the sample

- Rows: 122.
- `Distribution Date` is present instead of `DistributionYear` and `Distribution Quarter`.
- `Country Name` is present instead of the Layout A source fields.
- `Revenue Class Code` and `Revenue Class Description` are present instead of `Performance Source/Broadcast Medium`, `Music User Genre`, and `Music User`.
- `$ Amount` is present instead of `Credits` and `Dollars`.
- `Performance Start Date` and `Performance End Date` are mostly populated.
- Some `Work ID` values are blank while `Work Title` is populated.

### Date fields

Layout B has date-like fields with redacted shape `99-99-9999`:

- `Distribution Date`
- `Performance Start Date`
- `Performance End Date`

The initial parser attempted ISO and slash-separated date formats, so these values were not parsed during the first pass. A future connector should support dash-separated numeric dates and determine whether they are month-day-year or day-month-year based on ASCAP documentation or additional evidence.

### Row grain

For the Layout B sample:

- `Work ID` alone was not unique.
- Some `Work ID` values were blank.
- Full rows had no exact duplicates.
- Layout A row-grain candidate keys involving `Music User` are unavailable.

This layout needs separate normalization rules from Layout A.

## Useful provider-neutral information

Across the observed files, ASCAP CSV statements can potentially support provider-neutral evidence about:

- royalty activity reported for a statement/import period
- royalty activity reported for a work
- royalty activity reported by territory/country
- royalty activity reported by source, usage, or revenue class
- usage/play activity reported where play counts are available
- monetary royalty activity reported where amount fields are available
- catalog/work coverage in a statement
- period-over-period changes when multiple comparable statements are normalized

These should become normalized `Evidence` only after an ASCAP-specific source adapter converts provider rows into provider-neutral records.

## Provenance implications

An ASCAP CSV connector should preserve traceability without exposing ASCAP-specific objects to the domain model.

Useful provenance inputs include:

- original filename
- row number
- header shape/version detected by the connector
- statement/distribution period fields
- source layout family
- stable provider references where available

Sensitive fields such as account IDs, party names, work titles, and royalty amounts should not be placed into generic summaries or committed fixtures. If they are needed for local matching or traceability, they should remain private and be represented through safe references or metadata at the import boundary.

## Normalization implications

A future ASCAP CSV connector should likely:

1. Detect supported layout shape by header set.
2. Preserve deterministic row order.
3. Normalize Layout A and Layout B separately.
4. Derive `occurred_at` from the best available period/date field:
   - Layout A: quarter/year fields when exact dates are empty.
   - Layout B: distribution or performance dates after format semantics are confirmed.
5. Emit provider-neutral `RawEvidenceRecord` objects only.
6. Avoid constructing domain `Evidence` directly.
7. Avoid exposing ASCAP row objects to the domain model.
8. Include row-level references that are deterministic but safe.

## Recommended next implementation ticket

The next justified implementation ticket is:

```text
ST-043: Add private-safe ASCAP CSV layout profiler helper
```

Rationale:

- We now know ASCAP has at least two CSV layouts.
- Profiling private files by ad hoc local scripts is useful but not repeatable.
- A small application or developer-facing helper can produce safe schema profiles without committing private data or implementing an ASCAP connector.

That ticket should still avoid provider normalization, PDF parsing, reconciliation, OAuth, persistence, and domain changes.

After that, a separate ticket can add a narrowly scoped `AscapCsvRawEvidenceSource` for one supported layout using synthetic fixtures.

## Non-goals confirmed

This profiling did not introduce:

- committed private ASCAP files
- row-level private values in repository documentation
- ASCAP connector implementation
- PDF parsing
- CSV/PDF reconciliation
- provider-specific domain objects
- source-specific reasoning rules
