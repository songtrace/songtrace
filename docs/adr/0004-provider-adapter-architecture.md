# ADR 0004: Provider Adapter Architecture

## Status

Accepted

## Context

SongTrace should participate in a connected music ecosystem. Users may bring data from artist tools, distributor exports, PRO statements, commercial intelligence services, internal label systems, spreadsheets, APIs, reports, and future providers.

The reasoning engine must remain provider-neutral.

## Decision

Provider-specific or file-format-specific code should live outside the domain model and normalize records into SongTrace's import boundary:

```text
Raw source -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

Provider adapters and concrete raw evidence sources may know provider schemas. Domain entities and investigation rules should not.

## Consequences

- New sources can be introduced without redesigning the reasoning engine.
- Provider-specific payloads are not exposed directly to domain logic.
- Evidence provenance and confidence can evolve in provider-neutral terms.
- SongTrace can become the intelligence layer above existing providers rather than a replacement analytics provider.
