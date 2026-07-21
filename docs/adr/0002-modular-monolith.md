# ADR 0002: Modular Monolith

## Status

Accepted

## Context

SongTrace is early-stage and needs architectural clarity without distributed-system complexity. The current product requires deterministic local workflows, domain modeling, evidence import boundaries, provider-specific adapters, and a CLI.

## Decision

Build SongTrace as a modular monolith with clear package boundaries instead of separate services.

Current primary modules are:

- `songtrace.domain`
- `songtrace.application`
- `songtrace.providers`
- `songtrace.presentation`

## Consequences

- Contributors can understand and run the full system locally.
- Tests can cover end-to-end behavior without network or service orchestration.
- Module boundaries can remain explicit without premature service extraction.
- If future scale or deployment requirements justify services, those decisions can be made from a clearer product foundation.
