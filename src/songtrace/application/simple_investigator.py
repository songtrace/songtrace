"""A small deterministic investigator used for the first vertical slice."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from songtrace.application.investigation_result import InvestigationResult
from songtrace.domain.conclusion import Conclusion
from songtrace.domain.confidence import Confidence, ConfidenceLevel
from songtrace.domain.observation import Observation, ObservationKind

Clock = Callable[[], datetime]


class SimpleInvestigator:
    """Infer a narrow, explainable conclusion from structured observations."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or _utc_now

    def investigate(
        self,
        observations: tuple[Observation, ...],
    ) -> InvestigationResult:
        """Investigate observations using deterministic domain rules."""

        conclusions: list[Conclusion] = []

        stream_observation = self._find_observation(
            observations,
            kind=ObservationKind.PLAYLIST_STREAM_GROWTH,
        )
        save_observation = self._find_observation(
            observations,
            kind=ObservationKind.PLAYLIST_SAVE_GROWTH,
        )

        if stream_observation and save_observation:
            conclusions.append(
                Conclusion(
                    statement=(
                        "Editorial playlist placement likely drove renewed listener engagement."
                    ),
                    supporting_observation_ids=(
                        stream_observation.id,
                        save_observation.id,
                    ),
                    confidence=Confidence(
                        level=ConfidenceLevel.HIGH,
                        rationale=(
                            "Stream and save activity both increased after the playlist placement."
                        ),
                    ),
                    created_at=self._clock(),
                )
            )

        return InvestigationResult(
            observations=observations,
            conclusions=tuple(conclusions),
        )

    @staticmethod
    def _find_observation(
        observations: tuple[Observation, ...],
        kind: ObservationKind,
    ) -> Observation | None:
        for observation in observations:
            if observation.kind is kind:
                return observation

        return None


def _utc_now() -> datetime:
    return datetime.now(UTC)
