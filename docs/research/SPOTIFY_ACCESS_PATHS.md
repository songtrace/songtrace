# Spotify Access Paths Research

## Purpose

This document captures what SongTrace currently knows about Spotify data access paths and what remains uncertain before building additional Spotify Evidence Connectors.

SongTrace should not assume that Spotify's public developer API can provide every piece of evidence needed to explain a real-world performance spike. Spotify should be treated as one participant in a connected music ecosystem, not as the center of SongTrace's architecture.

## Current conclusion

SongTrace has confirmed a meaningful limitation in the tested Spotify Web API playlist path:

- playlist metadata is readable
- playlist track items are not readable for the tested playlists
- track-item access returns `403` under both client credentials and scoped user-token access
- the failure occurs for both SongTrace's paged request and a minimal `/tracks?limit=1` request

This means Spotify Web API playlist metadata can support candidate discovery and context, but current playlist item access should not be treated as a dependable source for verified playlist placement evidence.

It does **not** prove that a track is absent from a playlist, that playlist exposure was irrelevant, or that playlist evidence cannot be obtained from other authorized, exported, licensed, or commercial sources.

## Access path summary

| Access path | Current status | Likely evidence value | Current SongTrace posture |
| --- | --- | --- | --- |
| Spotify Web API: client credentials | Tested locally | Track/release metadata, playlist metadata, search candidates | Useful for metadata and candidate discovery; not enough for verified placement when item access is blocked. |
| Spotify Web API: user OAuth token | Tested locally with playlist read scopes | User-authorized metadata and accessible playlist data where permitted | Useful for diagnostics; did not unlock tested playlist item access. Do not build assumptions on it yet. |
| Spotify for Artists | Available to the user for Ghost Ship Octavius; exact export shape not yet inspected | Account-authorized streams, listeners, saves, territories, sources, playlist/source attribution if exposed | Strong candidate for private local profiling before any connector implementation. |
| Spotify Developer app review/quota modes | Not yet researched in project docs beyond local diagnostics | May affect quota, app availability, or policy compliance | Treat as uncertain. Do not assume app review unlocks playlist item or historical attribution evidence. |
| Label, distributor, or Spotify partner reporting | Not available through normal SongTrace code path today | Potentially richer account, catalog, source, or royalty-adjacent reporting | Treat as commercial/partner access; evaluate only when a real authorized source exists. |
| Commercial music intelligence providers | Future candidate sources | Historical playlist tracking, playlist adds/removes, curator context, follower counts, social/chart context | Likely important for attribution questions that Spotify Web API cannot answer directly. |
| User-owned exports and private local files | Already used safely for ASCAP and local evidence validation | Real-world evidence in CSV, XLSX, PDF, screenshots, reports, or manual records | Preferred near-term path when users can provide authorized exports. |

## Confirmed Web API diagnostics

The following was validated locally using SongTrace diagnostic commands.

### Tested credentials and scopes

Client-credentials access used:

- `SONGTRACE_SPOTIFY_CLIENT_ID`
- `SONGTRACE_SPOTIFY_CLIENT_SECRET`

User-token access used a fresh Spotify OAuth token with:

- `playlist-read-private`
- `playlist-read-collaborative`

The user token was confirmed valid because playlist metadata was readable.

### Tested request shapes

SongTrace tested:

1. Playlist metadata request.
2. Existing paged playlist track-items request.
3. Minimal playlist track-items request using `/tracks?limit=1` without custom field projection.

### Observed behavior

| Probe | Client credentials | User token with playlist scopes |
| --- | --- | --- |
| Playlist metadata | readable | readable |
| Paged playlist track items | `spotify_playlist_tracks_http_error_403` | `spotify_playlist_tracks_http_error_403` |
| Minimal playlist track items | `spotify_playlist_minimal_tracks_http_error_403` | `spotify_playlist_minimal_tracks_http_error_403` |

### Interpretation

The playlist item failure is not explained by:

- missing user token
- expired user token
- missing expected playlist read scopes
- client-credentials-only access
- custom field projection
- pagination shape

The safest interpretation is:

> SongTrace's current Spotify Web API path can discover playlist candidates and read playlist metadata, but cannot verify track membership through playlist item reads for the tested playlists.

## Spotify Web API role

The Spotify Web API remains useful for:

- track metadata lookup
- artist/title/album/ISRC validation when exposed
- Spotify track IDs as provider references
- playlist metadata lookup
- playlist search candidate discovery
- public context that can guide human investigation

The Spotify Web API should not currently be treated as sufficient for:

- historical playlist placement timelines
- definitive playlist membership verification when item access returns `403`
- playlist add/remove dates
- source-of-stream attribution
- explaining millions of historical plays by itself

If future Spotify access changes, SongTrace can revisit this with diagnostics before changing evidence semantics.

## Spotify for Artists role

The user has Spotify for Artists access for Ghost Ship Octavius. That access may be useful for validating real export shapes and evidence semantics, even if it may not directly cover the Warrel Dane / Everything Is Fading proof case.

Spotify for Artists may help answer whether artist-authorized exports can provide:

- stream counts over time
- listener counts over time
- save counts or save-rate context
- territory or city breakdowns
- source-of-stream categories
- playlist/source breakdowns
- release-level and track-level windows
- date granularity needed for timeline analysis
- CSV/XLSX export formats suitable for deterministic import

These are stronger candidates for SongTrace evidence than inaccessible public playlist item endpoints because they are account-authorized artist analytics rather than public catalog metadata.

### What must remain uncertain until local inspection

Do not assume the following until a private Spotify for Artists export or screen/report has been profiled locally:

- exact export file format
- exact column names
- whether exports include track-level or only aggregate data
- whether exports include saves
- whether source-of-stream categories are exportable
- whether playlist names are included or only category totals
- whether historical depth covers the proof-case time window
- whether daily, weekly, monthly, or custom date windows are available
- whether the user's Ghost Ship Octavius access reflects the data shape available for Warrel Dane
- what Spotify terms permit SongTrace to store, display, or derive from the exported data

## Professional, label, distributor, and partner paths

A more professional Spotify data path may exist through label, distributor, or partner reporting channels rather than the public Web API.

Potential examples include:

- label or distributor analytics portals
- royalty/distribution statements with platform/source fields
- Spotify for Artists team access for the relevant artist/catalog
- licensed provider reports
- partner-only APIs or data feeds
- catalog-owner or distributor reporting packages

SongTrace should treat these as source-specific Evidence Connector candidates only when the user has authorized access and a concrete data shape to inspect.

The project should not introduce generic partner abstractions before a real provider/export/API requires them.

## Commercial intelligence providers

Commercial providers may be the most realistic path for historical playlist attribution and cross-platform context.

Candidate evidence from providers such as Chartmetric, Soundcharts, Songstats, Viberate, Luminate, or similar services may include:

- historical playlist adds and removes
- playlist names, curator types, and follower counts
- track position over time
- editorial versus user-generated context where available
- TikTok/social/video correlations
- chart movement
- comparable artist or catalog movement

These sources should be evaluated using SongTrace's provider-neutral data strategy:

- evidence types produced
- freshness
- historical depth
- licensing and reuse rights
- cost
- data quality
- provenance support
- fit with normalized `RawEvidenceRecord -> Evidence` import boundaries

## Bring Your Own Data strategy

The Spotify access limitation reinforces SongTrace's Bring Your Own Data principle.

SongTrace should support evidence from the data sources users already have permission to access. For Spotify-related investigations, this may include:

- Spotify for Artists exports
- distributor exports
- label-service reports
- commercial provider exports
- manual playlist placement records
- screenshots or local artifacts transformed into normalized records
- royalty statements that reveal platform/territory/revenue patterns

The reasoning engine must remain unaware of whether evidence arrived through an API, CSV, XLSX, PDF, manual upload, or commercial provider connector.

## Implications for the Everything Is Fading proof case

The proof case asks how, when, where, and why a historical spike happened.

The Spotify Web API can help identify metadata and candidate playlists, but it is unlikely to answer the historical attribution question alone. Stronger evidence will likely come from a timeline assembled from:

- ASCAP domestic and international statements
- distributor or royalty reports
- Spotify for Artists or artist/team analytics if available for the relevant catalog
- commercial playlist/source intelligence
- social/video/campaign evidence around the pre-spike window
- user-supplied playlist placement records or artifacts

Near-term SongTrace work should prioritize building deterministic, private-safe summaries of available evidence before investing further in blocked Spotify playlist item reads.

## Recommended next implementation direction

The next implementation work should focus on real available evidence, not speculative Spotify API access.

Recommended next tickets:

1. **Spotify for Artists private export profiling guidance**
   - Use [Spotify for Artists Export Profiling Guide](../validation/SPOTIFY_FOR_ARTISTS_EXPORT_PROFILING.md) to place authorized exports in `.songtrace-private` and record private-safe layout notes.
   - Add a private-safe profiler only after a real export shape is available locally.
   - Report column names, row counts, date fields, and candidate evidence semantics without exposing private values.

2. **Private-safe work timeline summary**
   - Build a deterministic timeline across ASCAP and imported evidence.
   - Identify reporting periods, territories, statement types, revenue classes, and missing upstream attribution evidence.
   - Start answering when the spike appeared before trying to explain why.

3. **Evidence gap recommendations**
   - Generate deterministic missing-evidence prompts such as needing source-of-stream data, playlist placement proof, social/campaign context, or distributor reports for specific periods.

## Non-goals

This research does not introduce:

- new API calls
- new OAuth scopes
- token storage
- provider-specific domain models
- Spotify for Artists scraping
- production authentication
- partner API integration
- commercial provider implementation
- evidence creation from unverified Spotify playlist candidates
