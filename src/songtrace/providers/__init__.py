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
from songtrace.providers.spotify_connector_descriptor import spotify_connector_descriptor
from songtrace.providers.spotify_environment import (
    SPOTIFY_CLIENT_ID_ENV,
    SPOTIFY_CLIENT_SECRET_ENV,
    SpotifyEnvironmentStatus,
    validate_spotify_environment,
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
    "SpotifyEnvironmentStatus",
    "profile_ascap_csv_layout",
    "spotify_connector_descriptor",
    "summarize_ascap_work",
    "validate_spotify_environment",
]
