# SongTrace Product Vision

## Mission

SongTrace is an evidence-driven intelligence platform for understanding why music performance changes, where growth opportunities may exist, and what actions are reasonably supported by the available evidence.

The mission is to help artists, managers, labels, publishers, marketers, and other music professionals move from raw metrics to explainable understanding and better decisions. Analytics tools report what happened. SongTrace is designed to explain what the evidence suggests, what remains uncertain, which opportunities deserve attention, and what decisions could be supported next.

Music is the first vertical because it has immediate real-world value and strong personal relevance for the founding proof cases. The underlying reasoning model should remain generic enough to later support similar evidence-to-action products in other domains.

## Product Philosophy

SongTrace is not a reporting dashboard. It is a reasoning system built around traceable evidence.

Most music analytics products aggregate measurements: streams, saves, playlist placements, social activity, audience geography, campaign performance, chart movement, and other signals. Those measurements are valuable, but they do not automatically explain why performance changed or what a team should do next.

SongTrace treats measurements as evidence. Evidence is interpreted into observations. Observations support events, conclusions, opportunities, and eventually recommendations. Each step must remain explainable and traceable.

```text
Evidence -> Observation -> Event/Conclusion -> Opportunity -> Recommendation
```

This model is intentionally conservative. SongTrace should prefer clear, deterministic reasoning before AI-assisted interpretation. AI may help synthesize and explain, but it must reason over structured SongTrace evidence, observations, conclusions, and confidence. It must not become the source of factual truth.

## Guiding Principles

### Evidence before interpretation

SongTrace should distinguish facts from interpretations.

- Evidence records what was observed.
- Observations describe factual patterns supported by evidence.
- Conclusions explain what those observations suggest.
- Recommendations, when introduced, should propose actions supported by conclusions.

### Traceability is mandatory

Every observation must reference supporting evidence. Every conclusion must reference supporting observations. Future recommendations should reference supporting conclusions and evidence-backed rationale.

A user should always be able to ask: "Why does SongTrace say this?" and receive a clear answer grounded in specific evidence.

### Provider and vertical neutrality

SongTrace must not be designed around one data vendor, streaming platform, distributor, commercial provider, or even one long-term vertical. Providers and vertical adapters supply evidence; they should not define the reasoning model.

Provider-specific and music-specific schemas should be translated into provider-neutral records before they reach the reasoning engine. The core reasoning engine should operate on general concepts such as evidence, observations, events, trends, confidence, missing evidence, opportunities, recommendations, risk, and provenance.

### Connected Music Ecosystem

SongTrace should not attempt to replace the music intelligence providers, artist tools, distributor portals, rights organizations, analytics products, and internal systems that users already rely on.

Instead, SongTrace should become the evidence-driven intelligence layer above that ecosystem. Users should be able to bring their own data by connecting services, subscriptions, exports, reports, and internal records they already have permission to use.

SongTrace's value should come from combining evidence across providers into explainable observations, conclusions, and future recommendations—not from becoming another isolated reporting dashboard.

### Deterministic reasoning first

The first layer of intelligence should be deterministic and testable. Rules, observation extraction, and confidence policies should be explicit before introducing AI assistance.

This keeps the system explainable, debuggable, and suitable for contributors.

### AI as assistant, not authority

AI can help summarize evidence, propose hypotheses, generate explanations, identify missing evidence, and critique recommendations. It should not create evidence, hide uncertainty, or make unsupported factual claims.

AI output should be grounded in structured SongTrace data:

- Evidence
- Observations
- Conclusions
- Confidence
- Provenance

It should not reason directly over raw provider payloads unless those payloads have been normalized into SongTrace evidence.

## What SongTrace Is

SongTrace is:

- an evidence-driven reasoning platform with music as its first vertical
- a system for explaining performance changes and detecting meaningful music events
- a provider-neutral evidence pipeline
- a traceable conclusion engine
- a connected intelligence layer above existing music tools and data providers
- a bring-your-own-data platform for evidence users already have permission to access
- a future decision-support and market opportunity platform
- a foundation for explainable AI-assisted music strategy

## What SongTrace Is Not

SongTrace is not:

- a generic analytics dashboard
- a replacement for every music-data provider
- a destination that requires users to abandon their existing tools, subscriptions, exports, or internal systems
- a black-box prediction engine
- a system that guarantees commercial success
- an autonomous marketing decision-maker
- a tool that treats correlation as causal certainty

## Core Model

### Evidence

Evidence is a validated fact collected from a source. It may come from a public API, user upload, distributor export, commercial provider, or future source. Evidence should include provenance, timing, kind, and structured signals where possible.

### Observation

An observation is a factual pattern extracted from evidence. For example, playlist placement evidence plus stream-growth evidence can support an observation that streams increased after playlist placement.

### Event

An event is a meaningful state or change detected from evidence-backed observations. In music, events may include commercial activity confirmed, platform activity corroborated, likely upstream trigger identified, causal source confirmed, or market opportunity detected. The concept should remain generic enough to support analogous events in future domains.

### Conclusion

A conclusion is an inference supported by one or more observations. Conclusions include confidence and rationale. They should never appear without traceable support.

### Opportunity

An opportunity is a possible area for growth or action suggested by evidence. In music, this may include a territory, platform, audience, campaign, playlist ecosystem, media market, or touring market where market signals and current performance indicate upside.

### Recommendation

Recommendations are a future layer. A recommendation should describe a possible action and explain why the evidence supports it, what risks remain, and what evidence would strengthen or weaken it.

Recommendations should emerge only after the evidence, observation, conclusion, and confidence layers are strong enough to support decision-making.

## Long-Term Vision

Long term, SongTrace should become an evidence-based reasoning and decision-support platform that proves itself first in the music industry while preserving a reusable, vertical-agnostic reasoning core.

It should help users answer questions such as:

- What changed?
- What evidence supports that?
- What likely contributed to the change?
- What alternative explanations should be considered?
- What evidence is missing?
- What opportunities deserve attention?
- What actions are reasonably supported?

The product should complement data providers. It should help users understand what the data means, what deserves attention, which opportunities are underserved, and which actions are supported by trustworthy evidence.

In the long term, SongTrace should support a connected music ecosystem where evidence can arrive through APIs, uploads, reports, royalty statements, internal systems, and future integrations. The reasoning engine should remain unaware of how evidence entered the system. Its responsibility is to reason over normalized evidence, observations, conclusions, confidence, and future recommendations.
