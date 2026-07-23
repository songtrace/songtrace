# SongTrace Intelligence Strategy

## Purpose

SongTrace's intelligence strategy defines how the product turns evidence into understanding.

Analytics produce measurements. SongTrace produces explainable events, conclusions, opportunities, and eventually evidence-backed recommendations. The intelligence layer should remain traceable, deterministic where possible, and honest about uncertainty.

The core model is:

```text
Evidence -> Observation -> Event/Conclusion -> Opportunity -> Recommendation
```

The intelligence layer should remain independent of ingestion mechanisms and vertical-specific provider semantics. Whether evidence enters SongTrace through REST APIs, OAuth APIs, CSV imports, Excel reports, PDF statements, manual uploads, webhooks, or future Evidence Connectors, the reasoning engine should operate only on normalized evidence, observations, events, conclusions, confidence, opportunities, and future recommendations.

Music-specific adapters should translate ASCAP, Spotify, TikTok, distributor, playlist, touring, marketing, and royalty data into generic reasoning primitives. The same core should eventually be capable of supporting analogous evidence-to-action products in other domains.

## Observation Extraction

Observation extraction turns validated evidence into factual patterns.

An observation should not be a guess. It should describe a relationship or pattern supported by specific evidence IDs.

Examples include:

- stream growth after playlist placement
- save growth after playlist placement
- territory acceleration after campaign activity
- renewed catalog activity after social attention

The current `ObservationExtractor` is intentionally narrow and deterministic. That is the right foundation. Future extractors should expand carefully and continue relying on structured evidence fields rather than parsing prose summaries or provider-specific source objects.

## Rule-Based Investigations

Rule-based investigations evaluate structured observations against explicit rules.

The current rule catalog model is an early version of this strategy. It separates investigative knowledge from the investigator that evaluates rules.

Rules should remain:

- explicit
- immutable
- deterministic
- provider-neutral
- testable
- traceable to observation kinds

SongTrace should not rush into a generic rules engine. Rule complexity should grow only when real investigation needs require it.

## Events

An event is a meaningful state or change detected from observations. Events help users understand what happened or what is happening before the system claims a full causal explanation.

Music event examples include:

- commercial impact confirmed
- platform activity corroborated
- territory momentum detected
- likely upstream trigger identified
- causal source confirmed
- market opportunity detected

Events should include supporting observations, status, confidence or uncertainty, missing evidence, and recommended next evidence to collect.

## Conclusions

A conclusion is an inference supported by observations or events.

A conclusion should include:

- a clear statement
- supporting observation IDs
- confidence
- rationale
- creation time

Conclusions should not be created unless required observations are present. They should not rely on summary text or hidden provider assumptions.

## Explainability

Explainability is a product requirement, not a presentation feature.

Every conclusion should be explainable through a traceable chain:

```text
Conclusion -> Observation IDs -> Evidence IDs -> Source and reference
```

Future recommendations should follow the same principle:

```text
Recommendation -> Conclusion IDs -> Observation IDs -> Evidence IDs
```

Users should be able to understand why SongTrace reached a conclusion, what evidence supports it, and what remains uncertain.

## Confidence Scoring

Confidence should communicate how strongly the available evidence supports a conclusion.

The current confidence model is intentionally simple:

- level
- rationale

Future confidence scoring may consider:

- source reliability
- source freshness
- number of independent evidence sources
- consistency across platforms
- historical depth
- contradicting evidence
- missing evidence
- rule strength
- temporal alignment

Confidence should never imply certainty where the evidence only supports correlation.

## Alternative Hypotheses

As the reasoning engine matures, SongTrace should represent competing explanations.

For example, stream growth after playlist placement may be consistent with playlist impact, but alternative hypotheses might include:

- social content momentum
- paid campaign effects
- press coverage
- seasonal behavior
- catalog-wide artist momentum
- external cultural events

Alternative hypotheses should be linked to supporting, contradicting, and missing evidence.

## Missing Evidence

Missing evidence is itself important intelligence.

SongTrace should eventually identify evidence gaps such as:

- no save data available
- no campaign data available
- playlist placement timing unknown
- territory data too coarse
- social activity unavailable
- commercial provider data not licensed

This prevents unsupported certainty and helps users decide what data to acquire next.

## Recommendation Engine

Recommendations are future outputs based on events, conclusions, confidence, risk, cost, and opportunity.

A recommendation should answer:

- What action is suggested?
- What evidence supports it?
- What conclusion does it rely on?
- How confident is SongTrace?
- What could make the recommendation wrong?
- What evidence would improve confidence?

Recommendations should not be introduced until the evidence, observation, event, conclusion, and confidence layers are strong enough to support decision-making.

## Opportunity Engine

The Opportunity Engine identifies evidence-backed growth opportunities by comparing market context against current performance. It is a core product direction, not merely a future add-on.

Potential opportunity types include:

- territory and scene/genre gap opportunities
- audience-segment opportunities
- platform opportunities
- catalog reactivation candidates
- campaign efficiency opportunities
- release-timing opportunities
- collaboration opportunities
- content-format opportunities

Opportunities should be ranked by expected value, confidence, cost, risk, evidence quality, freshness, and actionability.

A target use case is comparing daily or recurring market trends in major territories against an artist's territory performance. If a relevant scene or genre is growing in a territory where the artist has little traction, SongTrace should surface that gap and recommend evidence-backed next actions such as playlist research, local media outreach, targeted advertising tests, community research, comparable-artist analysis, or touring-market validation.

## Explainable AI

AI can eventually help SongTrace synthesize structured intelligence into useful explanations and strategic options.

AI should operate over SongTrace's structured objects:

- Evidence
- Observations
- Events
- Conclusions
- Opportunities
- Confidence
- future Recommendations

AI should not create evidence, invent facts, hide uncertainty, or reason directly over raw provider payloads as if they were verified domain truth.

AI-assisted output should include citations or references back to the evidence and observations that support material claims.

## Human-in-the-Loop Decision Support

SongTrace should support human decision-makers, not replace them.

Humans should remain responsible for:

- approving recommendations
- interpreting strategic tradeoffs
- deciding budgets
- accepting risk
- providing context unavailable in data
- correcting or dismissing weak conclusions

Feedback from human decisions can eventually improve rule quality, confidence calibration, and recommendation ranking.

## Intelligence Strategy Outcome

SongTrace should become capable of explaining:

- what changed
- what is happening now
- what evidence supports that event or change
- what likely contributed to it
- what alternatives should be considered
- what evidence is missing
- which opportunities deserve attention
- what actions are reasonably supported
- how confident the system is and why

The system should produce understanding, not just reports.
