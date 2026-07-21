"""Provider-facing helpers for source-specific validation and future connectors."""

from songtrace.providers.ascap_csv_layout_profiler import (
    AscapCsvColumnProfile,
    AscapCsvFileProfile,
    AscapCsvLayoutProfile,
    AscapCsvNumericProfile,
    AscapCsvRowGrainProfile,
    AscapCsvStatementTypeProfile,
    profile_ascap_csv_layout,
)
from songtrace.providers.ascap_csv_raw_evidence_source import AscapCsvRawEvidenceSource
from songtrace.providers.ascap_international_incoming_csv_raw_evidence_source import (
    AscapInternationalIncomingCsvRawEvidenceSource,
)
from songtrace.providers.ascap_work_summary import AscapWorkSummary, summarize_ascap_work
from songtrace.providers.spotify_api_access import (
    SpotifyApiAccessStatus,
    validate_spotify_api_access,
)
from songtrace.providers.spotify_connector_descriptor import spotify_connector_descriptor
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyEnvironmentStatus,
    validate_spotify_environment,
)
from songtrace.providers.spotify_playlist_discovery import (
    SpotifyPlaylistDiscoveryResult,
    SpotifyPlaylistSearchCandidate,
    SpotifyPlaylistSkippedCandidate,
    discover_spotify_playlist_track_memberships,
    discover_spotify_playlist_track_memberships_for_queries,
)
from songtrace.providers.spotify_playlist_membership import (
    SpotifyPlaylistTrackMembership,
    lookup_spotify_playlist_track_membership,
)
from songtrace.providers.spotify_playlist_placement_export import (
    spotify_playlist_membership_to_raw_record,
    spotify_playlist_placement_raw_records_to_json_text,
)
from songtrace.providers.spotify_track_lookup import (
    SpotifyTrackMetadata,
    lookup_spotify_track_metadata,
)
from songtrace.providers.spotify_track_metadata_export import (
    spotify_track_metadata_raw_records_to_json_text,
    spotify_track_metadata_to_raw_record,
)

__all__ = [
    "SPOTIFY_CLIENT_ID_ENV",
    "SPOTIFY_CLIENT_SECRET_ENV",
    "AscapCsvColumnProfile",
    "AscapCsvFileProfile",
    "AscapCsvLayoutProfile",
    "AscapCsvNumericProfile",
    "AscapCsvRawEvidenceSource",
    "AscapCsvRowGrainProfile",
    "AscapCsvStatementTypeProfile",
    "AscapInternationalIncomingCsvRawEvidenceSource",
    "AscapWorkSummary",
    "SpotifyApiAccessStatus",
    "SpotifyEnvironmentStatus",
    "SpotifyPlaylistDiscoveryResult",
    "SpotifyPlaylistSearchCandidate",
    "SpotifyPlaylistSkippedCandidate",
    "SpotifyPlaylistTrackMembership",
    "SpotifyTrackMetadata",
    "discover_spotify_playlist_track_memberships",
    "discover_spotify_playlist_track_memberships_for_queries",
    "lookup_spotify_playlist_track_membership",
    "lookup_spotify_track_metadata",
    "profile_ascap_csv_layout",
    "spotify_connector_descriptor",
    "spotify_playlist_membership_to_raw_record",
    "spotify_playlist_placement_raw_records_to_json_text",
    "spotify_track_metadata_raw_records_to_json_text",
    "spotify_track_metadata_to_raw_record",
    "summarize_ascap_work",
    "validate_spotify_api_access",
    "validate_spotify_environment",
]
