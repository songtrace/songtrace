# Spotify Evidence Acquisition Checklist

## Purpose

This checklist defines what SongTrace should learn from Spotify-related evidence before implementing a Spotify connector.

It is intentionally not an implementation plan for OAuth, API clients, persistence, account linking, or provider-specific domain objects. Its purpose is to keep the first Spotify integration narrow, evidence-first, provider-neutral, and testable against local data.

SongTrace should use Spotify evidence to support explainable investigations such as:

- Did a track receive meaningful Spotify exposure?
- Did stream or save activity increase during the same window?
- Is the evidence strong enough to support a conclusion?
- What source attribution remains missing?
- Which facts are directly observed, inferred, or unavailable?

## Product principle

Spotify should be treated as one evidence source in a connected music ecosystem, not as the center of SongTrace's architecture.

SongTrace should not become a Spotify dashboard. Spotify data should enter through the same provider-neutral boundary as other sources:

```text
RawEvidenceSource -> RawEvidenceRecord -> EvidenceImporter -> Evidence
```

The reasoning engine should continue to operate only on normalized `Evidence`, `Observation`, `Conclusion`, and `Confidence` models.

SongTrace exposes `spotify_connector_descriptor()` as provider-facing planning metadata for this future boundary. The descriptor records expected ingestion methods, evidence kinds, freshness characteristics, and reliability considerations. It does not load records, perform OAuth, call Spotify APIs, store credentials, or create domain evidence.

Before any live Spotify work, developers can check local credential environment variable presence with:

```sh
uv run songtrace validate-spotify-environment
```

This command reads `SONGTRACE_SPOTIFY_CLIENT_ID` and `SONGTRACE_SPOTIFY_CLIENT_SECRET` only to determine whether nonblank values are present. It does not print values, call Spotify APIs, perform OAuth, exchange tokens, store secrets, or create evidence.

To validate that configured credentials can obtain a client-credentials token, use:

```sh
uv run songtrace validate-spotify-api-access
```

That command makes a single Spotify Accounts token request and reports only safe status. It does not print or store tokens, call Spotify Web API data endpoints, import evidence, perform a browser OAuth flow, or introduce provider-specific domain objects.

## Source categories

Spotify-related evidence may come from more than one source category.

| Source category | Likely access pattern | Expected role |
| --- | --- | --- |
| Spotify for Artists | User-authorized account access, exports, screenshots, or reports available to the artist/team | Account-specific performance evidence such as streams, saves, listeners, territory movement, and audience behavior where available. |
| Spotify Developer Platform | App credentials and/or user authorization depending on endpoint | Public or authorized metadata such as track identity, artist identity, album identity, current playlist contents, and playlist metadata where available. |
| Commercial playlist/intelligence providers | Subscription or licensed export/API | Historical playlist tracking, playlist metadata, follower counts, curator metadata, charting, and discovery context that may not be available directly from Spotify APIs. |
| User-maintained records | CSV/XLSX/manual notes created by an artist, manager, label, or analyst | Human-curated evidence for campaigns, playlist adds, outreach, context, or private observations. |

These sources may overlap, disagree, or have different freshness and historical depth. SongTrace should preserve provenance rather than collapsing them into unsupported certainty.

## Evidence categories to acquire

### Track identity

Track identity evidence anchors all downstream attribution work.

Candidate fields:

- recording artist
- track title
- ISRC when available
- Spotify track ID when available
- album/release title when useful
- release date or release window when useful
- source reference for the identity record

Current model mapping:

- `TrackIdentity.artist`
- `TrackIdentity.title`
- `TrackIdentity.isrc`
- `Evidence.track`
- provider-specific identifiers should remain in `reference` or future provenance metadata until a concrete identity model extension is justified

Availability classification:

| Evidence | Classification | Notes |
| --- | --- | --- |
| Artist/title/album metadata | API-obtainable and user-exportable | Useful for matching, but metadata alone does not prove engagement source. |
| ISRC | Often obtainable | Best near-term stable cross-provider identifier, but may be absent, wrong, duplicated, or different across versions. |
| Spotify track ID | API-obtainable | Useful as a source reference, but should not become a domain dependency. |

### Playlist placement evidence

Playlist placement evidence supports the current `playlist_placement` signal.

Candidate fields:

- track identity
- playlist name or provider-safe reference
- playlist ID or URL when available
- playlist owner/curator type when available
- placement observed date
- placement occurred/add date if known
- removal date if known
- position if known
- playlist follower count or reach proxy if known
- whether placement is editorial, algorithmic, user-curated, paid, or unknown

Current model mapping:

- `EvidenceKind.PLAYLIST_ACTIVITY`
- `EvidenceSignal.PLAYLIST_PLACEMENT`
- `Evidence.occurred_at` for the placement/add timestamp when known
- `Evidence.observed_at` for when SongTrace or the user observed/imported it
- `Evidence.reference` for provider-neutral playlist reference or source reference
- `Evidence.track` for track identity when supplied

Availability classification:

| Evidence | Classification | Notes |
| --- | --- | --- |
| Current playlist membership | API-obtainable for accessible playlists | Good for present-state evidence, weaker for historical attribution unless observed at the relevant time. |
| Historical playlist add/remove dates | Often commercially gated or user-supplied | Public APIs may not provide historical placement timelines. Treat absence as missing evidence, not proof no placement occurred. |
| Playlist type and curator context | Partly obtainable | Editorial, algorithmic, user-generated, and paid contexts should eventually be distinguished for confidence. |
| Exact placement position over time | Often unavailable or provider-dependent | Useful but should not be required for initial deterministic conclusions. |

### Stream growth evidence

Stream growth evidence supports the current `stream_growth` signal.

Candidate fields:

- track identity
- metric window start/end
- reported stream count or growth percentage where available
- baseline window if available
- territory/platform segment if available
- source export/report reference
- observed/imported timestamp

Current model mapping:

- `EvidenceKind.AUDIENCE_ACTIVITY`
- `EvidenceSignal.STREAM_GROWTH`
- `Evidence.occurred_at` for the end of the activity window or most specific reported event timestamp
- `Evidence.reference` for source report/export reference
- `Evidence.track` for track identity when supplied

Availability classification:

| Evidence | Classification | Notes |
| --- | --- | --- |
| Account-specific streams | User-exportable or account-authorized where available | Likely strongest via Spotify for Artists or authorized reports, not necessarily public API. |
| Public popularity/proxy metrics | API-obtainable with limitations | Useful as context but not equivalent to stream counts. Do not treat popularity as direct stream evidence. |
| Territory-level streams | User-exportable/account-authorized where available | Important for diagnosis, but availability and granularity may vary. |

### Save growth evidence

Save growth evidence supports the current `save_growth` signal.

Candidate fields:

- track identity
- metric window start/end
- save count or growth percentage where available
- baseline window if available
- source export/report reference
- observed/imported timestamp

Current model mapping:

- `EvidenceKind.AUDIENCE_ACTIVITY`
- `EvidenceSignal.SAVE_GROWTH`
- `Evidence.occurred_at` for the end of the activity window or most specific reported event timestamp
- `Evidence.reference` for source report/export reference
- `Evidence.track` for track identity when supplied

Availability classification:

| Evidence | Classification | Notes |
| --- | --- | --- |
| Account-specific saves | User-exportable or account-authorized where available | Important for engagement quality. Access may be limited compared with stream summaries. |
| Public save counts | Usually unavailable | Do not infer saves from public popularity or playlist placement alone. |

### Territory, date, and source breakdowns

These are not required for the current playlist engagement rule, but they are important for diagnosing the real-world case.

Candidate fields:

- country or territory
- city or market if available and privacy-safe
- date or reporting period
- stream/save/listener metric type
- source platform/report
- track identity

Availability classification:

| Evidence | Classification | Notes |
| --- | --- | --- |
| Territory movement | User-exportable/account-authorized where available | Supports `where` questions and future opportunity detection. |
| Daily or weekly windows | Partly obtainable | Needed to align playlist exposure, social events, campaigns, and royalties. |
| Exact traffic source attribution | Often unavailable | Spotify evidence alone may not identify whether a specific tweet, Instagram post, video, or campaign caused listening. |

## Normalization checklist

Before a Spotify source becomes a connector, confirm that each record can answer these questions without exposing provider-specific objects to the domain:

- What provider-neutral `EvidenceKind` does this record represent?
- Which `EvidenceSignal`, if any, does it carry?
- What is the exact `source_name`?
- What is the most appropriate `summary` for human review?
- What does `occurred_at` mean for this source: event time, report period end, observation time, or export period?
- Is `observed_at` supplied by the source, or should `EvidenceImporter` apply its batch fallback timestamp?
- What provider-neutral `reference` preserves traceability without leaking credentials or sensitive raw payloads?
- Does the row include enough `TrackIdentity` to correlate with playlist, royalty, and platform activity evidence?
- Does the source record represent direct evidence, derived evidence, or a weak proxy?
- What freshness, reporting lag, or historical-depth limitation should affect confidence later?

## Local validation workflow before API work

Use private local files first. Do not commit exports, screenshots, credentials, tokens, or private account data.

### 1. Track identity

Create or transform a private local fixture so playlist and platform activity rows include the same track identity fields where possible:

```csv
track_artist,track_title,track_isrc
```

If ISRC is unavailable, continue with artist/title, but record that matching confidence is weaker.

### 2. Playlist placement CSV

Represent known playlist placement evidence with `PlaylistPlacementCsvRawEvidenceSource` shape:

```csv
id,source_name,summary,occurred_at,observed_at,reference,track_artist,track_title,track_isrc
```

Use `occurred_at` for the playlist add/placement time if known. If only an observation/export time is known, make that timestamp semantics explicit in the summary and reference until the model supports richer period/provenance metadata.

### 3. Platform activity CSV

Represent stream/save movement with `PlatformActivityCsvRawEvidenceSource` shape:

```csv
id,source_name,summary,occurred_at,observed_at,reference,signal,track_artist,track_title,track_isrc
```

Use `signal=stream_growth` or `signal=save_growth`.

### 4. Run deterministic investigation

```sh
uv run songtrace investigate-playlist-platform-csv \
  /absolute/path/to/private/playlist-placements.csv \
  /absolute/path/to/private/platform-activity.csv \
  --output json
```

The expected current result is limited but useful:

- evidence imports deterministically
- playlist and platform activity records preserve traceability
- playlist stream/save observations are generated when matching signals exist
- the existing rule catalog can produce the playlist engagement conclusion
- missing upstream evidence remains visible when no playlist/platform evidence supports attribution

## Causality and attribution limits

SongTrace must distinguish between direct attribution and supported inference.

Examples:

| Claim | Required support |
| --- | --- |
| The track was on a playlist. | Direct playlist placement evidence with source and timestamp/provenance. |
| Streams increased after playlist placement. | Playlist placement evidence plus stream-growth evidence in a compatible time window. |
| Playlist placement likely drove engagement. | Current deterministic observation combination, with exact supporting evidence IDs. |
| A specific playlist caused millions of plays. | Stronger evidence: placement timing, stream timing, reach/context, absence or accounting of competing explanations, and ideally source-attribution data. |
| A tweet, Instagram post, TikTok trend, or video caused the spike. | Direct social/video/campaign evidence plus platform activity timing and alternative-hypothesis checks. Spotify evidence alone may be insufficient. |

When exact attribution is unavailable, SongTrace should report missing evidence rather than inventing certainty.

## Expected first Spotify connector scope

A future first Spotify connector should be small. It should likely focus on one of these paths:

1. **Metadata and current playlist membership probe**
   - confirms track identity
   - checks current accessible playlist contents
   - produces playlist placement evidence only when directly observed

2. **Spotify for Artists export/import adapter**
   - starts from user-exported account data
   - normalizes streams/saves/listeners into provider-neutral evidence
   - avoids OAuth until file-based semantics are understood

3. **Account-authorized analytics connector**
   - uses OAuth only after the evidence semantics and local validation path are stable
   - produces normalized `RawEvidenceRecord` values
   - preserves provenance and avoids exposing Spotify-specific objects to the domain

The project should choose the first connector based on the evidence gap observed in local validation, not on implementation novelty.

## Open questions before implementation

- Which Spotify for Artists exports are available to the user account, and what fields do they contain?
- Can the available exports provide both stream growth and save growth, or only stream/listener summaries?
- What date granularity is available for historical periods relevant to the proof case?
- Are playlist source breakdowns available directly, or only through third-party playlist intelligence providers?
- Can current playlist API data help the historical proof case, or will it mostly help future monitoring?
- Which identifiers are most reliable for cross-source matching: ISRC, Spotify track ID, artist/title, or a combination?
- What data can be stored or displayed under Spotify's terms and the user's account permissions?

## Non-goals

This checklist does not introduce:

- Spotify API calls
- OAuth flows
- credentials or secret storage
- provider-specific domain entities
- persistence
- automatic playlist attribution
- traffic-source attribution
- AI-generated explanation
- recommendations

Those should be introduced only through focused tickets once local evidence validation shows a concrete need.
