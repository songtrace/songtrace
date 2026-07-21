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

## Data-Source Matrix

The data-source matrix maps provider-neutral evidence needs to likely source categories. It is not a vendor commitment. Its purpose is to make data assumptions explicit before SongTrace depends on them for observations, conclusions, confidence, or future recommendations.

### Source category definitions

| Source category | Description |
| --- | --- |
| Public APIs | Platform APIs or public endpoints with documented access, rate limits, and terms. |
| User imports | Files or manual uploads supplied by artists, managers, labels, publishers, or other authorized users. |
| Distributor exports | Reports exported from distributors, label services, royalty platforms, or accounting systems. |
| Commercial data providers | Licensed third-party platforms that aggregate music, playlist, social, chart, audience, or market data. |
| Social and short-form platforms | Native platform data from social, creator, video, and short-form services. |
| Playlist and editorial data | Playlist placement, curator, editorial, algorithmic, and playlist-metadata sources. |
| Radio, touring, sync, and press sources | Specialized sources for non-streaming exposure, live activity, licensing, publicity, and media coverage. |

### Initial data-source matrix

| Evidence category | Likely source categories | Availability | Expected freshness | Historical depth | Licensing concerns | Data quality notes |
| --- | --- | --- | --- | --- | --- | --- |
| Artist identity and canonical identifiers | Public APIs, user imports, commercial data providers | Generally obtainable | Medium to high | Medium to deep | Terms may restrict redistribution of platform identifiers or metadata. | Identity resolution can be difficult across aliases, collaborations, remasters, and inconsistent provider IDs. |
| Release identity, track identity, and release dates | Public APIs, user imports, distributor exports, commercial data providers | Generally obtainable | Medium to high | Medium to deep | Metadata rights and redistribution rules may vary by source. | Versioning, regional release dates, alternate mixes, and duplicate records require careful normalization. |
| Stream count and stream-growth evidence | User imports, distributor exports, commercial data providers, limited public APIs | Partly obtainable | Medium to high | Variable | Detailed streaming analytics are often account-bound, licensed, or commercially gated. | Counts may differ by provider methodology, reporting lag, fraud filtering, or territory coverage. |
| Save count and save-growth evidence | User imports, platform analytics exports, commercial data providers where available | Partly obtainable | Medium | Variable | Save-level analytics may be account-bound or unavailable through public APIs. | Save semantics differ by platform and may be unavailable historically. |
| Playlist placement evidence | Playlist and editorial data, commercial data providers, public APIs, user imports | Obtainable with caveats | Medium to high | Variable | Playlist metadata and historical placement access may require commercial licensing. | Placement timing, playlist type, track position, and curator identity may be incomplete or inconsistent. |
| Playlist type, size, position, and curator context | Playlist and editorial data, commercial data providers, limited public APIs | Partly obtainable | Medium | Variable | Commercial playlist databases may restrict reuse or export. | Playlist followers are imperfect proxies for reach; editorial, algorithmic, user, and paid contexts must be distinguished. |
| Listener, follower, fan, or subscriber growth | User imports, platform analytics exports, public APIs, commercial data providers | Partly obtainable | Medium | Variable | Audience metrics may be account-bound or limited by privacy and platform terms. | Definitions vary: follower, listener, subscriber, fan, and engaged listener are not interchangeable. |
| Territory-level consumption and engagement | User imports, distributor exports, commercial data providers | Partly obtainable | Medium | Medium | Granular geography may be restricted by platform, account access, privacy, or licensing. | Territory naming, minimum thresholds, and suppressed small-sample data can affect comparability. |
| Campaign timing, spend, and channel evidence | User imports, advertising exports, marketing platforms, campaign management tools | Obtainable from customer-owned data | High when exported directly | Variable | Requires authorized access to campaign accounts and may include sensitive business information. | Campaign names, attribution windows, targeting definitions, and creative metadata are often inconsistent. |
| Social engagement and follower growth | Social and short-form platforms, public APIs, user imports, commercial data providers | Partly obtainable | High for recent data | Often shallow or inconsistent | APIs and terms change frequently; some metrics may be restricted or unavailable. | Engagement metrics are platform-specific and susceptible to spikes, bot activity, and changing algorithms. |
| Short-form content usage and trend evidence | Social and short-form platforms, commercial data providers, user imports | Uncertain or commercially gated | High for recent data | Often limited | Access, licensing, attribution, and rights constraints may be material. | Attribution from creator activity to music consumption can be noisy and incomplete. |
| Chart positions and movement | Public chart publishers, commercial data providers, industry reports | Obtainable with caveats | Medium | Medium to deep | Methodology and reuse rights vary by chart owner or provider. | Charts are lagging indicators and may combine multiple activity types using opaque methodology. |
| Revenue, royalty, and sales evidence | Distributor exports, royalty systems, accounting exports, user imports | Obtainable from authorized users | Low to medium | Medium to deep | Highly sensitive commercial data; access and retention policies must be explicit. | Reporting lag, currency, territory splits, deductions, and rights shares complicate interpretation. |
| Press, radio, sync, and editorial coverage | Radio monitors, press databases, sync systems, user imports, commercial data providers | Partly obtainable | Low to medium | Variable | Many sources require paid licenses or manual verification. | Coverage quantity is not the same as impact; source quality and audience relevance matter. |
| Comparable artist, track, campaign, or market context | Commercial data providers, public APIs, internal historical records | Exploratory | Variable | Variable | Comparable datasets may be licensed, incomplete, or commercially restricted. | Comparability requires careful normalization and safeguards against misleading benchmarks. |

### Matrix principles

- A source category being listed does not mean the evidence is available, licensed, complete, or affordable.
- User-owned imports and distributor exports are likely the strongest near-term path for account-specific metrics.
- Public APIs are useful but should not be assumed to expose every metric needed for reasoning.
- Commercial providers may accelerate coverage, but SongTrace should evaluate them using evidence value, licensing clarity, freshness, historical depth, and provider-neutral fit.
- Data-source uncertainty should be documented as missing or weak evidence rather than hidden behind confident conclusions.

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

- provider or source name
- source category
- import batch identifier
- original record reference
- retrieval or import time
- source account or workspace context
- data license, access tier, or usage restriction
- source reliability notes
- transformation notes when raw provider fields are normalized

Provenance is essential for trust, debugging, audits, and resolving conflicting evidence.

### Minimum provenance policy

Near-term evidence should preserve enough provenance for a user or contributor to trace a conclusion back to the records that supported it:

```text
Conclusion -> Observation IDs -> Evidence IDs -> Source name and reference
```

The current `Evidence.source` and `Evidence.reference` fields are a suitable foundation for the first import sources. They should not be treated as a complete long-term provenance model, but they are enough to preserve traceability while the product remains small.

Before adding provider integrations that produce account-specific, licensed, or commercially sensitive evidence, SongTrace should be able to represent:

- the provider or source category that supplied the evidence
- the import batch that introduced the evidence
- the original source reference or row identifier
- when the evidence was imported or observed
- any material usage restriction that affects display, retention, or redistribution

### Provenance principles

- Provenance should be provider-neutral; it should describe where evidence came from without embedding provider-specific schemas in the reasoning engine.
- Provider-specific payloads should be normalized before becoming domain `Evidence`.
- Evidence summaries are not provenance. They may explain the evidence to humans, but traceability should rely on structured identifiers and references.
- A conclusion should never require a user to trust an unsupported statement when the supporting evidence can be referenced directly.

## Freshness

Freshness answers: "How current is this evidence?"

SongTrace should distinguish:

- when something occurred
- when SongTrace observed or imported it
- how often the source updates
- whether the evidence may be stale
- whether the evidence is a snapshot, an event, or a rolling aggregate

The current distinction between `occurred_at` and `observed_at` is an important foundation. Raw records may omit `observed_at`; the importer can apply an import-time fallback while preserving the event's `occurred_at` value.

### Freshness policy

Freshness should be interpreted relative to the kind of evidence and the product question being answered.

| Evidence type | Freshness concern | Strategy |
| --- | --- | --- |
| Event evidence | The event timestamp may be older than the import timestamp. | Preserve `occurred_at` as the event time and `observed_at` as the time SongTrace learned about it. |
| Snapshot evidence | The value may represent a point-in-time state that becomes stale. | Preserve observation/import time and avoid presenting old snapshots as current. |
| Rolling aggregate evidence | The aggregation window may not match other sources. | Document or encode the window before comparing it with other evidence. |
| Historical evidence | Older records may be complete but less useful for near-term action. | Use historical depth to support baselines while distinguishing it from current freshness. |

Future conclusions and recommendations should reduce confidence or explicitly report uncertainty when evidence is stale, missing a timestamp, or measured over incompatible windows.

## Source Reliability

Source reliability describes how much trust SongTrace should place in the origin and handling of evidence before it contributes to observations, conclusions, or confidence.

Reliability is not the same as conclusion confidence. A reliable source can still support a weak conclusion if the evidence is incomplete, stale, or contradicted. An unreliable source can still be useful if it is clearly labeled and corroborated by stronger evidence.

### Reliability considerations

SongTrace should evaluate source reliability using factors such as:

- whether the source is authoritative for the metric
- whether the user has authorized access to the data
- whether the source documents its methodology
- whether timestamps and aggregation windows are clear
- whether historical revisions or delayed reporting are common
- whether the data can be corroborated by independent sources
- whether licensing terms permit the intended use
- whether the source has known coverage gaps or sampling limitations

Near-term work should document these factors rather than prematurely implementing reliability scoring.

## Source Conflicts

Source conflicts occur when two or more evidence records cannot all be interpreted as simultaneously accurate for the same question, time window, entity, or metric.

Examples include:

- two providers reporting materially different stream counts for the same platform and date range
- a playlist source reporting a placement that another source does not show
- campaign spend totals that differ between a user upload and an advertising export
- territory data that uses different region definitions or suppression thresholds

### Conflict policy

SongTrace should not silently hide conflicts or pick a winner without explanation.

When conflicts are detected in future functionality, the product should prefer one of these outcomes:

1. preserve all conflicting evidence and surface the uncertainty
2. produce a lower-confidence conclusion with a clear rationale
3. produce no conclusion when the conflict blocks trustworthy interpretation
4. ask for additional evidence or human review

Conflict resolution rules should be introduced only when the current product has concrete conflicting evidence to evaluate. Until then, the strategy is to preserve traceability and avoid overconfident conclusions.

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

The current `Confidence` model intentionally stays simple: a level and rationale. That is appropriate while the reasoning system remains small. The model should evolve only when current rules and evidence types need more expressive confidence behavior.

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
