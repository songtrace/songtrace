# Spotify for Artists Export Profiling Guide

## Purpose

This guide defines a private-safe workflow for inspecting Spotify for Artists exports before SongTrace implements any Spotify for Artists importer or Evidence Connector.

The goal is to learn the shape and semantics of authorized artist-account exports without committing private data, exposing account information, or prematurely designing abstractions.

## Product context

SongTrace has confirmed that the tested Spotify Web API playlist item path cannot currently verify playlist membership for the tested playlists. Spotify for Artists may be a stronger evidence path because it can expose artist-authorized analytics rather than public catalog metadata.

A Spotify for Artists export may help SongTrace understand:

- when stream or listener activity changed
- whether save activity is available
- where activity occurred by country, city, or territory
- whether source-of-stream categories are available
- whether playlist/source breakdowns are available
- what date granularity is available
- whether exported files can become provider-neutral evidence

This guide is for local validation only. It does not introduce an importer, connector, API integration, or source-specific domain model.

## Private workspace

Place Spotify for Artists exports only in an ignored local workspace such as:

```text
.songtrace-private/spotify-for-artists/
```

Do not commit exports, screenshots, account data, downloaded reports, or derived files that contain private values.

If multiple artists or projects are profiled locally, keep them separated in private subdirectories. Do not use private artist names in committed fixture paths, tests, or documentation unless they are intentionally public and reviewed.

## What to look for in Spotify for Artists

Inspect the Spotify for Artists interface for export or download options in areas such as:

- song analytics
- release analytics
- audience analytics
- source of streams
- playlists or playlist-driven streams
- listener trends
- save or engagement metrics
- country, city, or territory views
- date range filters
- campaign or release-specific views

The exact navigation and export availability may change over time. Record what is available locally, but avoid hardcoding assumptions into SongTrace until a concrete export shape is profiled.

## Export types to identify

For each private export, record the export type locally using safe labels such as:

- `track_timeseries`
- `release_timeseries`
- `audience_summary`
- `source_of_streams`
- `playlist_sources`
- `territory_breakdown`
- `city_breakdown`
- `save_or_engagement_summary`
- `unknown_spotify_for_artists_export`

These labels are not domain model values. They are local profiling notes to help decide which importer, if any, should be built later.

## Private-safe facts to record

When inspecting an export manually, it is usually safe to record these facts in a local note or future private-safe profiler output:

- file extension, such as CSV or XLSX
- approximate export type
- whether the export is track-level, release-level, artist-level, or aggregate
- selected date range, if not sensitive
- number of rows
- number of columns
- column names, if they do not reveal private account or campaign values
- date/time columns present
- metric columns present by category, without values
- source/category columns present
- playlist/source/territory fields present, without values
- whether the file appears to include a header row
- whether the file appears to include totals, footers, or metadata rows
- whether there are multiple sheets, if XLSX
- whether the row grain appears daily, weekly, monthly, per-track, per-country, per-source, or unknown

Prefer descriptions of structure over raw values.

## Do not expose

Do not paste, commit, or include in GitHub issues/PRs:

- private export files
- screenshots containing private analytics
- account IDs
- team IDs
- user IDs
- private artist/team account names unless intentionally public and reviewed
- raw row values
- stream counts
- listener counts
- save counts
- revenue or royalty values
- territory/city values if sensitive
- playlist names if they reveal private campaign or account information
- campaign names
- token values
- authorization codes
- client secrets
- refresh tokens

If a future profiler is added, it should default to structural metadata only and avoid printing raw data values.

## Evidence semantics to determine

Before implementing an importer, determine what each export row means.

Important questions:

- What does one row represent?
- Is the row a daily time-series point, a date-range aggregate, a source category, a playlist, a territory, or another grain?
- Does the export include explicit track identity?
- Does it include ISRC, Spotify track ID, artist, title, release, or another identifier?
- Does the export represent direct observed activity or a derived summary?
- What does each date mean: event date, report date, export date, period start, or period end?
- Are metrics exact counts, rounded counts, percentages, ranks, or suppressed values?
- Are small values hidden or thresholded?
- Are source categories mutually exclusive?
- Are playlist/source breakdowns current-state, historical, or aggregate over a selected period?
- Can the data support `stream_growth`, `save_growth`, `playlist_placement`, territory evidence, source attribution evidence, or only context?

SongTrace should not map exports to `Evidence` until these semantics are clear.

## Candidate Evidence mapping

A future Spotify for Artists importer may produce provider-neutral evidence such as:

| Export evidence | Possible SongTrace mapping | Notes |
| --- | --- | --- |
| Stream movement over time | `EvidenceKind.AUDIENCE_ACTIVITY` with `EvidenceSignal.STREAM_GROWTH` | Requires clear period semantics and baseline/comparison logic. |
| Save movement over time | `EvidenceKind.AUDIENCE_ACTIVITY` with `EvidenceSignal.SAVE_GROWTH` | Only if saves are available and semantically clear. |
| Playlist/source breakdown | Possible playlist/source attribution evidence | Do not treat category summaries as exact playlist placement unless names/timestamps substantiate placement. |
| Country/city activity | Future territory/market evidence | Current domain may need extension before detailed territory evidence is represented. |
| Track identity fields | Identity/supporting metadata evidence | Useful for cross-source matching; metadata alone is not engagement evidence. |

These mappings are planning notes, not implementation commitments.

## Recommended local profiling note template

Use this template locally when inspecting a private export. Do not commit completed private notes unless all sensitive values have been removed.

```text
Export label:
Private file path: .songtrace-private/spotify-for-artists/...
File extension:
Approximate export type:
Artist/account scope:
Track/release scope:
Selected date range:
Rows:
Columns:
Column names safe to share:
Date columns present:
Metric columns present:
Source/category fields present:
Playlist/source fields present:
Territory/city fields present:
Row grain hypothesis:
Potential EvidenceKind/EvidenceSignal mapping:
Unknowns:
Privacy concerns:
```

## Future profiler expectations

A future private-safe profiler should be introduced only after a real export shape exists locally.

A profiler should report structural facts such as:

- file extension
- sheet names for XLSX, if safe
- row count
- column count
- column names when safe
- detected date columns
- detected metric-like columns by name only
- whether sheets or rows appear to contain source, playlist, territory, or track identity fields
- whether the file can be parsed deterministically

A profiler should not print raw values, metric counts, account identifiers, token values, or screenshots.

## Relationship to existing docs

Related documents:

- [Spotify Access Paths Research](../research/SPOTIFY_ACCESS_PATHS.md)
- [Spotify Evidence Acquisition Checklist](SPOTIFY_EVIDENCE_ACQUISITION.md)
- [Local Evidence Validation Guide](../LOCAL_EVIDENCE_VALIDATION.md)
- [SongTrace Data Strategy](../vision/DATA_STRATEGY.md)

## Non-goals

This guide does not introduce:

- a Spotify for Artists importer
- a Spotify for Artists API connector
- browser automation or scraping
- OAuth changes
- token persistence
- provider-specific domain entities
- committed private fixtures
- production data retention policy
- evidence generation from unprofiled exports
