"""Provider-neutral descriptors for future evidence connector capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from songtrace.domain.evidence import EvidenceKind


class EvidenceIngestionMethod(StrEnum):
    """Supported categories of evidence ingestion mechanisms."""

    REST_API = "rest_api"
    OAUTH_API = "oauth_api"
    CSV_IMPORT = "csv_import"
    EXCEL_IMPORT = "excel_import"
    PDF_REPORT = "pdf_report"
    EMAIL_ATTACHMENT = "email_attachment"
    MANUAL_UPLOAD = "manual_upload"
    WEBHOOK = "webhook"
    FUTURE_INTEGRATION = "future_integration"


@dataclass(frozen=True, slots=True)
class EvidenceConnectorDescriptor:
    """Describe what a future evidence connector can provide.

    The descriptor is planning metadata only. It does not load records, hold
    credentials, or expose provider-specific objects to the domain model.
    """

    source_name: str
    supported_ingestion_methods: tuple[EvidenceIngestionMethod, ...]
    produced_evidence_kinds: tuple[EvidenceKind, ...]
    freshness_characteristics: str
    reliability_characteristics: str
    authentication_method: str | None = None

    def __post_init__(self) -> None:
        source_name = self.source_name.strip()
        if not source_name:
            msg = "source_name must not be blank"
            raise ValueError(msg)

        authentication_method = self.authentication_method
        if authentication_method is not None:
            authentication_method = authentication_method.strip()
            if not authentication_method:
                msg = "authentication_method must not be blank when provided"
                raise ValueError(msg)

        supported_ingestion_methods = tuple(self.supported_ingestion_methods)
        if not supported_ingestion_methods:
            msg = "supported_ingestion_methods must not be empty"
            raise ValueError(msg)
        if len(set(supported_ingestion_methods)) != len(supported_ingestion_methods):
            msg = "supported_ingestion_methods must not contain duplicates"
            raise ValueError(msg)

        produced_evidence_kinds = tuple(self.produced_evidence_kinds)
        if not produced_evidence_kinds:
            msg = "produced_evidence_kinds must not be empty"
            raise ValueError(msg)
        if len(set(produced_evidence_kinds)) != len(produced_evidence_kinds):
            msg = "produced_evidence_kinds must not contain duplicates"
            raise ValueError(msg)

        freshness_characteristics = self.freshness_characteristics.strip()
        if not freshness_characteristics:
            msg = "freshness_characteristics must not be blank"
            raise ValueError(msg)

        reliability_characteristics = self.reliability_characteristics.strip()
        if not reliability_characteristics:
            msg = "reliability_characteristics must not be blank"
            raise ValueError(msg)

        object.__setattr__(self, "source_name", source_name)
        object.__setattr__(self, "authentication_method", authentication_method)
        object.__setattr__(self, "supported_ingestion_methods", supported_ingestion_methods)
        object.__setattr__(self, "produced_evidence_kinds", produced_evidence_kinds)
        object.__setattr__(self, "freshness_characteristics", freshness_characteristics)
        object.__setattr__(self, "reliability_characteristics", reliability_characteristics)
