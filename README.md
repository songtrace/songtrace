# SongTrace

SongTrace is an evidence-driven music intelligence platform and the first vertical for a broader provider-neutral reasoning engine.

It is not a reporting dashboard. Analytics produce measurements; SongTrace turns structured evidence into explainable, traceable understanding, event intelligence, and eventually actionable recommendations.

The current implementation is intentionally small and deterministic. It focuses on a reasoning path that should remain generic enough to serve future verticals beyond music:

```text
Evidence -> Observation -> Event/Conclusion -> Opportunity -> Recommendation
```

For local evidence imports, SongTrace uses a provider-neutral boundary:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

This keeps source-specific file parsing outside the domain reasoning model. Music-specific providers such as ASCAP or Spotify should adapt their data into normalized evidence; the reasoning engine should not depend on music-vendor schemas.

## Current capabilities

SongTrace can currently:

- load provider-neutral raw evidence from JSON, CSV, and XLSX files
- validate raw records into immutable domain `Evidence`
- extract deterministic playlist engagement observations
- run deterministic investigation rules
- produce traceable conclusions with confidence
- summarize ASCAP royalty and platform-source evidence
- produce ASCAP-backed music event reports with missing evidence and next actions
- expose local validation, investigation, and evidence-summary commands through the CLI

## Quickstart

Install dependencies and run commands through `uv`.

### Run the test suite

```sh
uv run pytest
```

### Run the example investigation

```sh
uv run python examples/simple_investigation.py
```

### Validate an evidence file

Use `validate-evidence` to check only the import boundary:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json
```

This loads raw records and verifies they can become domain `Evidence`. It does not extract observations or run investigation rules.

For machine-readable validation output:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json --output json
```

For repeatable local comparisons, provide deterministic batch metadata:

```sh
uv run songtrace validate-evidence examples/simple_investigation_evidence.json \
  --output json \
  --batch-id 00000000-0000-0000-0000-000000000901 \
  --imported-at 2026-07-21T12:00:00+00:00
```

### Investigate an evidence file

Use `investigate-evidence` to run the current deterministic pipeline:

```sh
uv run songtrace investigate-evidence examples/simple_investigation_evidence.json
```

For machine-readable investigation output:

```sh
uv run songtrace investigate-evidence examples/simple_investigation_evidence.json --output json
```

## Supported local raw evidence formats

Current generic raw evidence sources support:

- JSON
- CSV
- XLSX

These are provider-neutral input formats. They are not provider-specific connectors.

## Private local data

Do not commit private exports, royalty statements, provider reports, credentials, API tokens, or real provider/customer data.

For guidance on local-only validation with private files, see:

- [Local Evidence Validation Guide](docs/LOCAL_EVIDENCE_VALIDATION.md)

If private files must temporarily live near the repository, use the ignored `.songtrace-private/` directory and always check:

```sh
git status --short
```

No private file should appear before committing.

## Architecture and strategy

Additional project documentation lives in `docs/`, including:

- [Architecture](docs/ARCHITECTURE.md)
- [CLI Reference](docs/CLI.md)
- [Evidence Semantics](docs/EVIDENCE_SEMANTICS.md)
- [Import Policy](docs/IMPORT_POLICY.md)
- [Spotify Evidence Acquisition Checklist](docs/validation/SPOTIFY_EVIDENCE_ACQUISITION.md)
- [Product Vision](docs/vision/PRODUCT_VISION.md)
- [Data Strategy](docs/vision/DATA_STRATEGY.md)
- [Intelligence Strategy](docs/vision/INTELLIGENCE_STRATEGY.md)
- [Roadmap](docs/vision/ROADMAP.md)

## Current objective

Near-term work should stay focused on implementation-led vertical slices that help users answer:

- What happened?
- What evidence supports it?
- What remains unknown?
- What opportunity or next action is reasonably supported?

Music is the proving ground because it provides immediate real-world evidence and user value. The core reasoning primitives should stay generic enough to later support analogous evidence-to-action domains such as market analysis, telecom trend detection, or operational incident intelligence.

## Current non-goals

SongTrace does not currently implement:

- provider-specific connectors
- live API integrations
- OAuth flows
- PDF parsing
- persistence or import history
- autonomous recommendations
- AI-assisted reasoning

Those should be introduced only when they solve a concrete product need and preserve provider-neutral, evidence-first architecture.
