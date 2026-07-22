"""Deterministic selection support for high-value music intelligence data sources."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class MusicDataAccessMode(StrEnum):
    """High-level access modes for music intelligence data sources."""

    USER_EXPORT = "user_export"
    USER_AUTHORIZED = "user_authorized"
    COMMERCIAL_SUBSCRIPTION = "commercial_subscription"
    PARTNER_ACCESS = "partner_access"
    MANUAL_RECORD = "manual_record"


class MusicDataFormat(StrEnum):
    """Common formats for music intelligence source data."""

    API = "api"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    DASHBOARD = "dashboard"
    MANUAL_ENTRY = "manual_entry"


class MusicEvidenceCapability(StrEnum):
    """Evidence capabilities relevant to SongTrace proof-case investigations."""

    STREAM_TIMELINE = "stream_timeline"
    LISTENER_TIMELINE = "listener_timeline"
    SAVE_ENGAGEMENT = "save_engagement"
    SOURCE_ATTRIBUTION = "source_attribution"
    HISTORICAL_PLAYLIST_TIMELINE = "historical_playlist_timeline"
    PLAYLIST_CONTEXT = "playlist_context"
    TERRITORY_TIMELINE = "territory_timeline"
    SOCIAL_CULTURAL_SIGNALS = "social_cultural_signals"
    ROYALTY_COMMERCIAL_CONTEXT = "royalty_commercial_context"
    TRACK_IDENTITY = "track_identity"


_PROOF_CASE_WEIGHTS: dict[MusicEvidenceCapability, int] = {
    MusicEvidenceCapability.SOURCE_ATTRIBUTION: 5,
    MusicEvidenceCapability.HISTORICAL_PLAYLIST_TIMELINE: 5,
    MusicEvidenceCapability.STREAM_TIMELINE: 4,
    MusicEvidenceCapability.TERRITORY_TIMELINE: 4,
    MusicEvidenceCapability.PLAYLIST_CONTEXT: 3,
    MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS: 3,
    MusicEvidenceCapability.LISTENER_TIMELINE: 2,
    MusicEvidenceCapability.SAVE_ENGAGEMENT: 2,
    MusicEvidenceCapability.ROYALTY_COMMERCIAL_CONTEXT: 2,
    MusicEvidenceCapability.TRACK_IDENTITY: 1,
}


@dataclass(frozen=True, slots=True)
class MusicDataProviderCandidate:
    """Provider candidate for real-world music intelligence evidence.

    This is selection metadata, not a connector. It does not authenticate, fetch,
    parse, persist, normalize provider data, or call external services.
    """

    name: str
    access_modes: tuple[MusicDataAccessMode, ...]
    likely_formats: tuple[MusicDataFormat, ...]
    capabilities: tuple[MusicEvidenceCapability, ...]
    strengths: tuple[str, ...]
    constraints: tuple[str, ...]
    proof_case_relevance: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text(self.name, "name must not be blank"))
        object.__setattr__(
            self,
            "access_modes",
            _required_unique_tuple(self.access_modes, "access_modes"),
        )
        object.__setattr__(
            self,
            "likely_formats",
            _required_unique_tuple(self.likely_formats, "likely_formats"),
        )
        object.__setattr__(
            self,
            "capabilities",
            _required_unique_tuple(self.capabilities, "capabilities"),
        )
        object.__setattr__(self, "strengths", _required_text_tuple(self.strengths, "strengths"))
        object.__setattr__(self, "constraints", _optional_text_tuple(self.constraints))
        object.__setattr__(
            self,
            "proof_case_relevance",
            _required_text(self.proof_case_relevance, "proof_case_relevance must not be blank"),
        )

    @property
    def proof_case_score(self) -> int:
        """Return a deterministic score for the Everything Is Fading proof-case needs."""

        return sum(_PROOF_CASE_WEIGHTS[capability] for capability in self.capabilities)


@dataclass(frozen=True, slots=True)
class RankedMusicDataProvider:
    """Deterministically ranked provider candidate."""

    rank: int
    candidate: MusicDataProviderCandidate
    score: int

    def __post_init__(self) -> None:
        if self.rank < 1:
            msg = "rank must be positive"
            raise ValueError(msg)
        if self.score < 0:
            msg = "score must not be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class MusicDataProviderCatalog:
    """Immutable catalog of currently relevant provider candidates."""

    candidates: tuple[MusicDataProviderCandidate, ...]

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        if not candidates:
            msg = "candidates must not be empty"
            raise ValueError(msg)
        names = tuple(candidate.name.casefold() for candidate in candidates)
        if len(set(names)) != len(names):
            msg = "candidates must not contain duplicate names"
            raise ValueError(msg)
        object.__setattr__(self, "candidates", candidates)

    @classmethod
    def default(cls) -> MusicDataProviderCatalog:
        """Return the current deterministic provider candidates for proof-case validation."""

        return cls(
            candidates=(
                _chartmetric_candidate(),
                _soundcharts_candidate(),
                _songstats_candidate(),
                _viberate_candidate(),
                _music_tomorrow_candidate(),
                _spotontrack_candidate(),
                _spotify_for_artists_candidate(),
                _distributor_reports_candidate(),
                _ascap_royalty_statements_candidate(),
                _youtube_studio_candidate(),
                _luminate_candidate(),
            )
        )


def rank_music_data_providers(
    catalog: MusicDataProviderCatalog | None = None,
) -> tuple[RankedMusicDataProvider, ...]:
    """Rank provider candidates deterministically for the current proof case."""

    selected_catalog = catalog or MusicDataProviderCatalog.default()
    ordered = sorted(
        selected_catalog.candidates,
        key=lambda candidate: (-candidate.proof_case_score, candidate.name.casefold()),
    )
    return tuple(
        RankedMusicDataProvider(rank=index, candidate=candidate, score=candidate.proof_case_score)
        for index, candidate in enumerate(ordered, start=1)
    )


def _chartmetric_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Chartmetric",
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV, MusicDataFormat.API),
        capabilities=(
            MusicEvidenceCapability.HISTORICAL_PLAYLIST_TIMELINE,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Broad cross-platform intelligence candidate.",
            "Likely useful for historical playlist and social context.",
        ),
        constraints=("Paid access and export/API terms must be verified.",),
        proof_case_relevance=(
            "Strong candidate for historical playlist and social context around a spike."
        ),
    )


def _soundcharts_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Soundcharts",
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV, MusicDataFormat.API),
        capabilities=(
            MusicEvidenceCapability.HISTORICAL_PLAYLIST_TIMELINE,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Monitoring-oriented music intelligence candidate.",
            "Potentially useful for playlist, chart, and social movement timelines.",
        ),
        constraints=("Plan-level feature access and historical depth must be verified.",),
        proof_case_relevance=(
            "Strong candidate if historical playlist/source exports are available."
        ),
    )


def _songstats_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Songstats",
        access_modes=(
            MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,
            MusicDataAccessMode.USER_AUTHORIZED,
        ),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV),
        capabilities=(
            MusicEvidenceCapability.HISTORICAL_PLAYLIST_TIMELINE,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Potentially accessible track-level playlist/chart notification source.",
            "May be practical for near-term private export profiling.",
        ),
        constraints=(
            "Exportability, historical depth, and exact track coverage must be verified.",
        ),
        proof_case_relevance="Good candidate for practical playlist and chart movement validation.",
    )


def _viberate_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Viberate",
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV),
        capabilities=(
            MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Cross-channel artist and audience intelligence candidate.",
            "May help connect social, market, and playlist context.",
        ),
        constraints=("Track-level historical detail and exportability must be verified.",),
        proof_case_relevance="Useful if the spike has social, territory, or cross-channel context.",
    )


def _music_tomorrow_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Music Tomorrow",
        access_modes=(
            MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,
            MusicDataAccessMode.PARTNER_ACCESS,
        ),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV, MusicDataFormat.API),
        capabilities=(
            MusicEvidenceCapability.STREAM_TIMELINE,
            MusicEvidenceCapability.SOURCE_ATTRIBUTION,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Analytics and growth intelligence candidate for catalog teams.",
            "Potentially relevant if source-attribution and playlist context are exportable.",
        ),
        constraints=(
            "Access model, catalog coverage, and historical export detail must be verified.",
        ),
        proof_case_relevance=(
            "Potentially strong if it can expose attribution around streaming spikes."
        ),
    )


def _spotontrack_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="SpotOnTrack",
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV),
        capabilities=(
            MusicEvidenceCapability.HISTORICAL_PLAYLIST_TIMELINE,
            MusicEvidenceCapability.PLAYLIST_CONTEXT,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Playlist- and chart-focused intelligence candidate.",
            "Could be useful for validating historical playlist placement leads.",
        ),
        constraints=("Current coverage, exportability, and licensing terms must be verified.",),
        proof_case_relevance=(
            "Focused candidate for playlist history if available for the target track."
        ),
    )


def _spotify_for_artists_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Spotify for Artists",
        access_modes=(MusicDataAccessMode.USER_EXPORT, MusicDataAccessMode.USER_AUTHORIZED),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV),
        capabilities=(
            MusicEvidenceCapability.STREAM_TIMELINE,
            MusicEvidenceCapability.LISTENER_TIMELINE,
            MusicEvidenceCapability.SAVE_ENGAGEMENT,
            MusicEvidenceCapability.SOURCE_ATTRIBUTION,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Artist-authorized first-party platform analytics.",
            "Likely strongest Spotify path for streams, listeners, saves, sources, "
            "and territories.",
        ),
        constraints=(
            "Requires artist/team access for relevant catalog.",
            "Exact export shape and historical depth must be profiled locally.",
        ),
        proof_case_relevance=(
            "High value if access exists for the Warrel Dane catalog or comparable "
            "export shapes."
        ),
    )


def _distributor_reports_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Distributor or label-service reports",
        access_modes=(MusicDataAccessMode.USER_EXPORT, MusicDataAccessMode.PARTNER_ACCESS),
        likely_formats=(MusicDataFormat.CSV, MusicDataFormat.XLSX, MusicDataFormat.PDF),
        capabilities=(
            MusicEvidenceCapability.STREAM_TIMELINE,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.ROYALTY_COMMERCIAL_CONTEXT,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Often available to rights holders or teams.",
            "Useful for connecting platform activity to commercial reporting.",
        ),
        constraints=("Source attribution and playlist detail may be limited or delayed.",),
        proof_case_relevance="High value for validating when and where commercial impact appeared.",
    )


def _ascap_royalty_statements_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="ASCAP royalty statements",
        access_modes=(MusicDataAccessMode.USER_EXPORT,),
        likely_formats=(MusicDataFormat.CSV, MusicDataFormat.PDF),
        capabilities=(
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.ROYALTY_COMMERCIAL_CONTEXT,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Available private proof-case evidence already used locally.",
            "Useful for commercial timeline and territory/source-class clues.",
        ),
        constraints=(
            "Royalty statements are lagging and usually do not identify upstream causes.",
        ),
        proof_case_relevance=(
            "Essential for the money timeline, but insufficient alone for attribution."
        ),
    )


def _youtube_studio_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="YouTube Studio",
        access_modes=(MusicDataAccessMode.USER_EXPORT, MusicDataAccessMode.USER_AUTHORIZED),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV),
        capabilities=(
            MusicEvidenceCapability.STREAM_TIMELINE,
            MusicEvidenceCapability.SOURCE_ATTRIBUTION,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.SOCIAL_CULTURAL_SIGNALS,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "First-party video/platform analytics for owned channels.",
            "Can reveal video, search, referral, geography, and time-series context when relevant.",
        ),
        constraints=("Only useful for owned or accessible channels/assets.",),
        proof_case_relevance=(
            "Important if the spike was video-driven or tied to YouTube discovery."
        ),
    )


def _luminate_candidate() -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name="Luminate",
        access_modes=(
            MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,
            MusicDataAccessMode.PARTNER_ACCESS,
        ),
        likely_formats=(MusicDataFormat.DASHBOARD, MusicDataFormat.CSV, MusicDataFormat.XLSX),
        capabilities=(
            MusicEvidenceCapability.STREAM_TIMELINE,
            MusicEvidenceCapability.TERRITORY_TIMELINE,
            MusicEvidenceCapability.ROYALTY_COMMERCIAL_CONTEXT,
            MusicEvidenceCapability.TRACK_IDENTITY,
        ),
        strengths=(
            "Industry-grade consumption and market data candidate.",
            "Potentially strong for authoritative activity context.",
        ),
        constraints=("Likely expensive, enterprise-oriented, and subject to strict licensing.",),
        proof_case_relevance=(
            "Potentially valuable, but may be less practical as the first paid source "
            "to trial."
        ),
    )


def _required_unique_tuple[T](items: Iterable[T], field_name: str) -> tuple[T, ...]:
    normalized = tuple(items)
    if not normalized:
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    if len(set(normalized)) != len(normalized):
        msg = f"{field_name} must not contain duplicates"
        raise ValueError(msg)
    return normalized


def _required_text_tuple(items: Iterable[str], field_name: str) -> tuple[str, ...]:
    normalized = _optional_text_tuple(items)
    if not normalized:
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    return normalized


def _optional_text_tuple(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(item.strip() for item in items if item.strip())


def _required_text(value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized
