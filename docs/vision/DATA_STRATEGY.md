# SongTrace Data Strategy

## Purpose

SongTrace depends on trustworthy evidence. This document defines the long-term data strategy for collecting, validating, classifying, and reasoning over evidence in a provider-neutral way.

SongTrace must not assume that every desirable metric is available through public APIs. Some evidence may be obtainable through public platforms, some through user imports, some through distributors, some through commercial providers, and some may be unavailable or only derivable.

The goal is to build disciplined evidence foundations before expanding conclusions and recommendations.

## Evidence Catalog

SongTrace should maintain an evidence catalog describing the information needed for artist, release, catalog, market, audience, platform, and campaign analysis.

The catalog should distinguish:

- required evidence
- optional evidence
- future evidence
- exploratory evidence
- derived evidence
- unavailable evidence
- provider-specific fields
- provider-neutral normalized fields

The existing `EvidenceKind` and `EvidenceSignal` models are early examples of provider-neutral classification. The catalog below is intentionally strategic rather than provider-specific: it describes the evidence SongTrace needs to reason well, not the exact API fields that any one source exposes.

### Evidence priority definitions

| Priority | Meaning |
| --- | --- |
| Required | Needed for credible near-term investigations and deterministic conclusions. |
| Optional | Useful for stronger conclusions, segmentation, or confidence, but not required for the first investigation flows. |
| Future | Likely important for diagnosis, decision support, or recommendations after the core investigation pipeline matures. |
| Exploratory | Potentially valuable, but availability, licensing, quality, or product value still needs validation. |

### Initial evidence catalog

| Category | Evidence | Priority | Product questions supported | Rationale |
| --- | --- | --- | --- | --- |
| Artist context | Artist identity and canonical identifiers | Required | Which artist does this evidence describe? | Stable identity is necessary to connect evidence across releases, platforms, campaigns, and providers. |
| Artist context | Artist lifecycle stage | Optional | Is this a developing, established, catalog-driven, or campaign-active artist? | Lifecycle context affects how momentum, risk, and opportunity should be interpreted. |
| Release context | Release identity and canonical identifiers | Required | Which release or track does this evidence describe? | Release identity is necessary to avoid mixing evidence from different tracks, versions, or campaigns. |
| Release context | Release date and territory availability | Required | Did performance change before or after release, rollout, or territory availability? | Timing anchors observations and prevents false conclusions from comparing incompatible windows. |
| Catalog context | Track and catalog ownership context | Future | Which catalog assets can reasonably be acted on? | Recommendations may depend on rights, ownership, and whether renewed promotion is commercially actionable. |
| Platform activity | Stream count or stream-growth evidence | Required | Did listening activity increase, decrease, or materially change? | Streaming movement is a core signal for current deterministic investigation rules. |
| Platform activity | Save count or save-growth evidence | Required | Did listeners show stronger intent or retention? | Save growth helps distinguish passive exposure from deeper listener engagement. |
| Platform activity | Skip, completion, repeat, or listener-retention evidence | Optional | Did users engage meaningfully after exposure? | Engagement quality can improve confidence but may not be available through every source. |
| Playlist activity | Playlist placement evidence | Required | Was the track placed in a playlist during the relevant window? | Playlist placement is a core exposure signal for current investigation rules. |
| Playlist activity | Playlist type, curator, size, and position | Optional | What kind of playlist exposure occurred? | Placement quality affects interpretation; editorial, algorithmic, user, and paid contexts should not be treated identically. |
| Playlist activity | Playlist add and remove timestamps | Optional | How long did the exposure last? | Duration and timing help connect exposure to observed performance changes. |
| Audience activity | Listener, follower, fan, or subscriber growth | Optional | Did audience depth grow alongside consumption? | Audience growth helps distinguish durable momentum from short-term consumption spikes. |
| Audience activity | Demographic or segment evidence | Future | Which audiences are responding? | Segmentation can support diagnosis and decision support but may carry availability and privacy constraints. |
| Market activity | Territory-level consumption and engagement | Optional | Where is momentum emerging? | Territory evidence supports market opportunity detection and campaign allocation decisions. |
| Market activity | Local market context and availability | Future | Is growth meaningful in the local context? | Territory evidence becomes stronger when compared with market size, release availability, and historical baselines. |
| Campaign activity | Campaign timing and spend | Optional | Did paid or owned activity coincide with performance changes? | Campaign context helps avoid over-attributing growth to organic or playlist activity. |
| Campaign activity | Campaign channel, targeting, and creative metadata | Future | Which campaign actions appear efficient or repeatable? | More detailed campaign evidence supports diagnosis and recommendation quality. |
| Social activity | Social engagement, content volume, and follower growth | Optional | Did off-platform attention coincide with music performance changes? | Social evidence can explain demand creation outside streaming platforms, but signals vary by platform. |
| Social activity | Short-form content usage and trend evidence | Exploratory | Is a track gaining cultural or creator-driven traction? | Short-form evidence can be powerful but may be limited by API access, attribution quality, and licensing. |
| Chart activity | Chart positions and movement | Optional | Did the track achieve externally visible momentum? | Chart evidence can validate market significance but is often lagging and methodology-dependent. |
| Commercial activity | Revenue, royalty, and sales evidence | Future | Did attention convert into commercial value? | Commercial evidence is critical for opportunity ranking but may depend on distributor, label, or rights-holder access. |
| Media and press | Press, radio, sync, and editorial coverage | Future | Did external exposure contribute to momentum? | Media context can explain performance changes outside platform-native signals. |
| Comparable context | Comparable artists, tracks, campaigns, or markets | Exploratory | What benchmarks make this performance meaningful? | Comparable-case reasoning is useful but should wait until SongTrace has enough normalized evidence and safeguards. |

### Catalog principles

- Required evidence should stay narrow enough to support credible deterministic investigations.
- Optional evidence should strengthen confidence without becoming a hidden prerequisite.
- Future evidence should be documented now but implemented only when needed by current product behavior.
- Exploratory evidence should not drive conclusions until availability, licensing, quality, and interpretation risks are understood.
- Every catalog item should eventually map to provider-neutral evidence, observations, conclusions, or confidence inputs.

## Provider-Neutral Architecture

SongTrace should preserve a provider-neutral import boundary:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

Raw sources may have provider-specific formats, but the reasoning engine should consume validated domain evidence. Provider-specific schemas should not leak into observation extraction, rule evaluation, conclusions, or recommendations.

This keeps the reasoning engine independent from any single vendor or data source.

## Evidence Lifecycle

A typical evidence lifecycle is:

1. A raw source loads external data.
2. The data is converted into `RawEvidenceRecord` transport objects.
3. `EvidenceImporter` validates and constructs domain `Evidence`.
4. `ObservationExtractor` identifies factual patterns from evidence.
5. Investigation rules produce conclusions from observations.
6. Future recommendation systems may propose actions from conclusions.

Each stage should preserve ordering, provenance, and traceability.

## Provenance

Provenance answers: "Where did this evidence come from?"

At minimum, evidence should identify its source. Over time, SongTrace should support richer provenance metadata such as:

- provider name
- import batch
- original record reference
- retrieval time
- data license or access tier
- account or workspace context
- source reliability notes

Provenance is essential for trust, debugging, audits, and resolving conflicting evidence.

## Freshness

Freshness answers: "How current is this evidence?"

SongTrace should distinguish:

- when something occurred
- when SongTrace observed or imported it
- how often the source updates
- whether the evidence may be stale

The current distinction between `occurred_at` and `observed_at` is an important foundation. Raw records may omit `observed_at`; the importer can apply an import-time fallback while preserving the event's `occurred_at` value.

## Confidence

Confidence should reflect the strength and reliability of conclusions, not just the amount of data available.

Data-related inputs to confidence may eventually include:

- source reliability
- source freshness
- historical depth
- consistency across providers
- known platform limitations
- sample size
- missing counter-evidence
- conflicts between sources

The current `Confidence` model intentionally stays simple: a level and rationale. That is appropriate while the reasoning system remains small.

## Structured Metadata

SongTrace should prefer structured metadata over prose parsing.

Examples include:

- `EvidenceKind`
- `EvidenceSignal`
- `ObservationKind`
- source identifiers
- timestamps
- references

Summaries are useful for human explanation, but product logic should rely on structured fields whenever possible.

## Obtainable, Derived, and Unavailable Evidence

A mature data strategy should classify desired evidence into three groups.

### Obtainable evidence

Evidence that can be acquired directly from a public API, user upload, distributor export, commercial provider, or internal source.

Examples may include playlist placements, streaming counts, save counts, geography, chart positions, campaign spend, and social activity.

### Derived evidence

Evidence that can be calculated from other evidence.

Examples may include growth rates, conversion ratios, anomaly scores, campaign efficiency, catalog reactivation signals, and territory acceleration.

Derived evidence should remain traceable to its source evidence.

### Unavailable evidence

Evidence that cannot currently be acquired reliably or legally.

SongTrace should explicitly document unavailable evidence so the product does not imply certainty where the data does not exist.

## Future Provider Integrations

Future provider integrations should be evaluated on:

- coverage
- freshness
- historical depth
- reliability
- licensing terms
- cost
- rate limits
- exportability
- privacy expectations
- commercial viability

Potential sources include:

- Spotify
- Apple Music
- YouTube
- TikTok
- distributor exports
- radio data
- touring data
- social platforms
- playlist data providers
- Chartmetric
- Soundcharts
- Viberate
- Songstats
- Luminate

Provider adoption should be driven by evidence value, not vendor enthusiasm alone.

## Data Strategy Outcome

SongTrace should be able to answer:

- What evidence does the product need?
- Where can that evidence come from?
- How trustworthy is it?
- How fresh is it?
- What does it cost?
- What can be derived?
- What remains unavailable?
- Which conclusions are unsupported with the current evidence?
