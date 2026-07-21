# ADR 0003: Framework-Independent Core

## Status

Accepted

## Context

SongTrace's core value is evidence-backed reasoning. That reasoning should not depend on a web framework, CLI framework, database, external API, or AI provider.

## Decision

Keep the domain and application layers framework-independent.

The CLI may use Typer and Rich, but presentation-layer choices must not leak into domain entities, evidence import rules, observation extraction, or investigation logic.

## Consequences

- Domain and application behavior remains easy to test directly.
- Future presentation layers can be added without rewriting the reasoning model.
- External providers and file formats must normalize into `RawEvidenceRecord` and domain `Evidence` before reasoning.
- Framework-specific code belongs in presentation or provider-facing modules, not in the core reasoning model.
