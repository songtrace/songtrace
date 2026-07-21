# Evidence Semantics

SongTrace evidence is provider-neutral. It records facts that can later support observations, conclusions, and recommendations without exposing provider-specific source objects to the domain model.

Current evidence semantics are intentionally small. New kinds or signals should be added only when real validation or product behavior justifies them.

## Evidence timestamps

`observed_at` records when SongTrace, a user, or an import process observed the evidence.

`occurred_at` records when the underlying fact happened. For evidence that summarizes a period instead of a single event, use the end of the represented period as `occurred_at` unless a more precise provider-neutral event timestamp is available.

Examples:

- a playlist placement event: use the placement date/time
- a weekly stream increase: use the end of the measured week
- a royalty statement period: use the end of the royalty/performance/distribution period represented by the evidence

Both timestamps must be timezone-aware when supplied.

## Evidence signals

Signals are structured provider-neutral labels that make evidence machine-interpretable. Evidence may have no structured signals when the fact is valid but SongTrace has not yet defined a signal for it.

Current signals:

| Signal | Compatible kind | Meaning |
| --- | --- | --- |
| `playlist_placement` | `playlist_activity` | A track, release, or catalog item was placed on a playlist. |
| `stream_growth` | `audience_activity` | Stream activity increased over a represented period. |
| `save_growth` | `audience_activity` | Save activity increased over a represented period. |
| `royalty_reported` | `royalty_activity` | Royalty activity was reported for a represented statement, usage, performance, or distribution period. |

## Royalty evidence

`royalty_activity` evidence represents provider-neutral facts derived from royalty statements, royalty exports, or similar royalty reporting sources.

The first supported royalty signal is `royalty_reported`. It means royalty activity exists in a source for a represented period. It does not imply growth, causation, payment accuracy, reconciliation status, or commercial significance.

For royalty-statement-derived evidence:

- `source_name` should describe the source category without leaking private details, such as `local_statement_upload`.
- `summary` should describe the fact without including sensitive private values.
- `occurred_at` should represent the end of the period covered by the evidence.
- `observed_at` should represent when the statement/export was imported or observed.
- `reference` should be stable enough for traceability but should not expose private account identifiers or confidential statement values.
- `signals` may include `royalty_reported` when the evidence represents reported royalty activity.

## Current limits

SongTrace can import royalty evidence today, but the deterministic investigation engine does not yet extract royalty observations or produce royalty conclusions.

A royalty evidence file can therefore validate successfully and still produce:

```text
Observations: 0
Conclusions: 0
```

That is expected until a focused ticket introduces provider-neutral royalty observations and catalog rules.
