"""Planning descriptor for future Spotify evidence connector capabilities."""

from __future__ import annotations

from songtrace.application import EvidenceConnectorDescriptor, EvidenceIngestionMethod
from songtrace.domain.evidence import EvidenceKind


def spotify_connector_descriptor() -> EvidenceConnectorDescriptor:
    """Return provider-neutral planning metadata for future Spotify evidence ingestion."""

    return EvidenceConnectorDescriptor(
        source_name="spotify",
        authentication_method=(
            "OAuth for account-authorized analytics; public or app-authorized access "
            "where available for metadata."
        ),
        supported_ingestion_methods=(
            EvidenceIngestionMethod.REST_API,
            EvidenceIngestionMethod.OAUTH_API,
            EvidenceIngestionMethod.CSV_IMPORT,
        ),
        produced_evidence_kinds=(
            EvidenceKind.AUDIENCE_ACTIVITY,
            EvidenceKind.PLAYLIST_ACTIVITY,
        ),
        freshness_characteristics=(
            "Freshness depends on source path: current metadata may be near real-time, "
            "account analytics may have reporting lag, and user exports reflect export time."
        ),
        reliability_characteristics=(
            "Reliability depends on authorized account scope, endpoint/export availability, "
            "reporting lag, historical depth, and whether evidence is direct or a proxy."
        ),
    )
