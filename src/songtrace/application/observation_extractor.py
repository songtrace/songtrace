"""Extract deterministic observations from collected evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from songtrace.domain.evidence import Evidence, EvidenceSignal
from songtrace.domain.observation import Observation, ObservationKind

Clock = Callable[[], datetime]


class ObservationExtractor:
    """Extract narrow, deterministic observations from evidence."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or _utc_now

    def extract(
        self,
        evidence: tuple[Evidence, ...],
    ) -> tuple[Observation, ...]:
        """Extract observations supported by the supplied evidence."""

        observations: list[Observation] = []
        playlist_evidence = _find_first(evidence, _is_playlist_placement_evidence)

        if playlist_evidence is not None:
            stream_evidence = _find_first(evidence, _is_stream_growth_evidence)
            if stream_evidence is not None:
                observations.append(
                    Observation(
                        kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
                        summary="Streams increased after playlist placement.",
                        supporting_evidence_ids=(playlist_evidence.id, stream_evidence.id),
                        observed_at=self._clock(),
                    )
                )

            save_evidence = _find_first(evidence, _is_save_growth_evidence)
            if save_evidence is not None:
                observations.append(
                    Observation(
                        kind=ObservationKind.PLAYLIST_SAVE_GROWTH,
                        summary="Save activity increased after playlist placement.",
                        supporting_evidence_ids=(playlist_evidence.id, save_evidence.id),
                        observed_at=self._clock(),
                    )
                )

        royalty_evidence = _find_first(evidence, _is_royalty_reported_evidence)
        if royalty_evidence is not None:
            observations.append(
                Observation(
                    kind=ObservationKind.ROYALTY_REPORTED,
                    summary="Royalty activity was reported.",
                    supporting_evidence_ids=(royalty_evidence.id,),
                    observed_at=self._clock(),
                )
            )

        return tuple(observations)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _find_first(
    evidence: tuple[Evidence, ...],
    predicate: Callable[[Evidence], bool],
) -> Evidence | None:
    for item in evidence:
        if predicate(item):
            return item

    return None


def _is_playlist_placement_evidence(evidence: Evidence) -> bool:
    return EvidenceSignal.PLAYLIST_PLACEMENT in evidence.signals


def _is_stream_growth_evidence(evidence: Evidence) -> bool:
    return EvidenceSignal.STREAM_GROWTH in evidence.signals


def _is_save_growth_evidence(evidence: Evidence) -> bool:
    return EvidenceSignal.SAVE_GROWTH in evidence.signals


def _is_royalty_reported_evidence(evidence: Evidence) -> bool:
    return EvidenceSignal.ROYALTY_REPORTED in evidence.signals
