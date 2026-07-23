# SongTrace Architecture

## Mission

> Build an evidence-to-action reasoning engine, proven first through music intelligence.

SongTrace starts with music because the proof cases are concrete, personally meaningful, and immediately useful to artists, managers, labels, marketers, and other music business teams. The architecture should still preserve a reusable reasoning core that can eventually serve analogous domains such as market analysis, telecom trend detection, operational incident intelligence, or other fragmented-data decision systems.

## Architectural layers

```text
Presentation
    ↓
Application
    ↓
Domain
```

Provider-specific and vertical-specific concerns should live outside the reasoning core.

## Core boundary

The current local import boundary is:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

Future connectors, uploads, and provider integrations should preserve that shape or evolve it deliberately. The domain reasoning model should operate on normalized evidence and derived reasoning objects, not on raw provider payloads.

## Reasoning model

The target reasoning path is:

```text
Evidence -> Observation -> Event/Conclusion -> Opportunity -> Recommendation
```

These concepts should remain as provider-neutral and vertical-neutral as practical:

- `Evidence`: sourced facts with provenance
- `Observation`: factual patterns extracted from evidence
- `Event`: meaningful state or change detected from observations
- `Conclusion`: inference supported by observations or events
- `Opportunity`: evidence-backed area for possible growth or action
- `Recommendation`: proposed action with rationale, confidence, risk, and missing evidence

Music-specific concepts such as ASCAP statements, Spotify playlists, TikTok sounds, royalties, territories, touring opportunities, or genre scenes should be translated into these generic concepts before reaching the reusable reasoning layer.

## Provider and vertical adapters

Adapters may understand provider or vertical details:

- ASCAP CSV layouts
- Spotify exports or APIs
- TikTok sound/video evidence
- distributor reports
- market trend files
- manual or screenshot observations
- future non-music data sources

Adapters should not leak provider-specific objects into the domain reasoning engine. Their job is to preserve provenance while normalizing source material into evidence and structured signals.

## Product-facing vertical layer

The music product layer can provide music-specific commands, reports, terminology, and recommended next actions. It may talk about artists, tracks, works, territories, genres, playlists, campaigns, labels, and managers.

That layer should be allowed to evolve quickly because it is the proving ground for user value. When a pattern appears broadly reusable, promote it into generic reasoning concepts deliberately and with tests.

## Development guidance

Prefer implementation-led vertical slices that answer a concrete product question, such as:

- What happened?
- What evidence supports it?
- What remains unknown?
- Where is there an opportunity gap?
- What action is reasonably supported next?

Avoid speculative abstractions that are not needed by a current proof case. Keep the reasoning core agnostic, deterministic where possible, explainable, and traceable.
