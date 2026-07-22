# Premium Data Provider Selection

## Purpose

SongTrace needs richer evidence than public Spotify API probes can provide. The proof case for “Everything Is Fading” requires enough trustworthy data to explain how, when, where, and why a major performance spike happened.

This document supports ST-082 by focusing provider evaluation on actionable evidence acquisition. It is not a broad market map and it does not choose a permanent vendor dependency.

## Product principle

SongTrace should be the evidence-driven intelligence layer above the connected music ecosystem. It should help users bring data they already have access to and, when necessary, evaluate paid or professional sources that can fill concrete evidence gaps.

The goal is not to become another reporting dashboard. Analytics tools measure activity; SongTrace normalizes evidence, extracts observations, and produces explainable conclusions.

## What the ranking means

The `rank-music-data-providers` command exposes a deterministic catalog of provider candidates and ranks them against the current proof-case needs.

The ranking is based on evidence capabilities that matter most right now:

- source attribution
- historical playlist timeline
- stream timeline
- territory timeline
- playlist context
- social and cultural signals
- listener and save engagement
- royalty/commercial context
- track identity

It is selection guidance only. A high rank does not mean that SongTrace has a connector, subscription, API access, export rights, or confirmed coverage. Those facts must be validated before implementation.

## Current high-value candidates

The catalog currently includes:

- Chartmetric
- Soundcharts
- Songstats
- Viberate
- Music Tomorrow
- SpotOnTrack
- Spotify for Artists
- distributor or label-service reports
- ASCAP royalty statements
- YouTube Studio
- Luminate

## Why this matters for the proof case

ASCAP royalty statements can help establish the money timeline and some territory or source-class clues, but they usually cannot explain the upstream cause of a spike. Spotify Web API playlist search can find candidate playlists, but tested playlist item access returned `403` even with a scoped user token, so inaccessible playlist items must be treated as missing verification evidence.

The next useful product step is to trial or profile one source that can provide source-attribution and historical activity data for the relevant track or catalog. That source might be an artist-authorized export, distributor/label report, or paid music intelligence service.

## Near-term development direction

Before building more generic ingestion infrastructure, SongTrace should validate at least one richer real-world data source by answering:

1. Does it cover the target track or comparable catalog data?
2. Can the user legally export or access the data?
3. Does it provide historical depth around the spike period?
4. Does it include source attribution, playlist history, territory history, or social context?
5. Can exported records be normalized into provider-neutral `RawEvidenceRecord` objects?
6. Can every imported fact preserve provenance?

Only after those questions are answered should SongTrace add a provider-specific connector or importer.

## Boundaries

This work does not:

- call provider APIs
- purchase subscriptions
- parse private files
- expose private evidence
- implement connectors
- add persistence
- introduce provider-specific domain objects
- let provider data bypass the evidence import boundary

The existing architecture remains:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence -> Observation -> Conclusion
```

Any future connector must produce normalized raw evidence records and keep the reasoning engine unaware of how evidence entered the system.
