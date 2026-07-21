# ADR 0001: Python as Primary Language

## Status

Accepted

## Context

SongTrace needs to support deterministic evidence processing, local file ingestion, CLI workflows, and future data-provider integrations. The project benefits from a language with strong standard-library support for JSON, CSV, datetime handling, typing, testing, and data-processing workflows.

## Decision

Use Python as the primary implementation language for the SongTrace core and CLI.

## Consequences

- Domain and application code can remain small, readable, and contributor-friendly.
- The project can use Python typing, `dataclasses`, `pytest`, `ruff`, and `pyright` for quality control.
- Local evidence processing can rely heavily on the standard library.
- Performance-sensitive work can be revisited later only if real workloads justify it.
