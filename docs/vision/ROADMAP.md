# SongTrace Roadmap

## Product Direction

SongTrace is evolving from a deterministic investigation engine into an evidence-driven intelligence platform for the music industry.

The roadmap is organized around increasing product maturity, not around individual providers or dashboards. Each stage builds on the same core reasoning model:

```text
Evidence -> Observation -> Conclusion -> Recommendation
```

The near-term priority is to make this pipeline reliable, explainable, and easy to extend. Later stages can add richer diagnosis, opportunity detection, and AI-assisted strategic support.

## Product Maturity Stages

### 1. Investigation

The investigation stage answers: "What happened, and what conclusion is supported by the evidence we have?"

Current and near-term capabilities include:

- importing raw evidence records
- validating evidence into domain entities
- extracting structured observations
- evaluating deterministic investigation rules
- producing traceable conclusions
- preserving exact evidence and observation provenance

This stage should remain small, deterministic, and highly tested.

### 2. Diagnosis

The diagnosis stage answers: "Why might this have happened, and what alternative explanations should be considered?"

Future capabilities may include:

- temporal-window analysis
- trend and anomaly observations
- campaign-context reasoning
- platform and territory comparisons
- supporting and contradicting evidence
- missing-evidence identification
- competing hypotheses

Diagnosis should not claim causal certainty from correlation. It should explain what is supported, what is uncertain, and what evidence would improve confidence.

### 3. Decision Support

The decision-support stage answers: "What actions are reasonably supported?"

Future capabilities may include:

- evidence-backed recommendations
- opportunity ranking
- risk and uncertainty representation
- estimated effort and investment ranges
- recommendation dismissal and feedback tracking
- repeatable strategic reports

Recommendations should remain traceable to evidence, observations, conclusions, and confidence.

### 4. Strategic Advisor

The strategic-advisor stage answers: "How should a human team think about this situation?"

Future capabilities may include:

- explainable AI synthesis
- alternative strategy generation
- critique of proposed actions
- natural-language explanation of evidence-backed conclusions
- questions for human decision-makers
- auditability and model-version tracking

AI should reason only over structured SongTrace evidence, observations, conclusions, recommendations, and confidence. It should not create evidence or treat raw provider data as unverified truth.

## Major GitHub Epics

SongTrace's long-term work is organized into six major epics:

1. **Evidence and Data Strategy**
   - Defines what evidence SongTrace needs, where it can come from, and which conclusions are possible with available data.

2. **Data Source Integration Platform**
   - Builds provider-neutral ingestion for public APIs, commercial providers, user uploads, and future sources.

3. **Intelligence and Reasoning Engine**
   - Expands deterministic reasoning into richer observations, hypotheses, conclusions, and explanation models.

4. **Market Opportunity Engine**
   - Identifies evidence-backed opportunities across artists, tracks, catalogs, territories, audiences, platforms, and campaigns.

5. **Explainable AI Advisor**
   - Uses AI to synthesize structured SongTrace evidence into explanations, hypotheses, questions, and strategic options.

6. **Commercialization and Industry Partnerships**
   - Defines target users, provider partnerships, commercial tiers, and a sustainable path for the product.

## Near-Term Development Philosophy

Near-term development should prioritize:

- simple domain models
- deterministic behavior
- explicit invariants
- traceability
- provider neutrality
- strong tests
- small vertical slices

The project should avoid speculative architecture. New abstractions should appear only when the current codebase has a concrete need for them.

Near-term implementation should continue strengthening the current pipeline:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence -> ObservationExtractor -> SimpleInvestigator -> Conclusion
```

## Long-Term Product Direction

Long term, SongTrace should become a trusted reasoning layer above fragmented music data sources.

The product should help users:

- understand performance changes
- diagnose likely contributors
- compare alternative explanations
- identify missing evidence
- surface evidence-backed opportunities
- make better strategic decisions

SongTrace should not compete by being the largest data warehouse. It should compete by making evidence understandable, explainable, and actionable.
