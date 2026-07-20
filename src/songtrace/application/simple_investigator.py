"""A small deterministic investigator used for the first vertical slice."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from songtrace.application.investigation_result import InvestigationResult
from songtrace.application.rule_catalog import RuleCatalog
from songtrace.domain.conclusion import Conclusion
from songtrace.domain.investigation_rule import InvestigationRule
from songtrace.domain.observation import Observation, ObservationKind

Clock = Callable[[], datetime]


class SimpleInvestigator:
    """Infer narrow, explainable conclusions from structured observations."""

    def __init__(self, clock: Clock | None = None, rule_catalog: RuleCatalog | None = None) -> None:
        self._clock = clock or _utc_now
        self._rule_catalog = rule_catalog or RuleCatalog()

    def investigate(
        self,
        observations: tuple[Observation, ...],
    ) -> InvestigationResult:
        """Investigate observations using deterministic catalog rules."""

        conclusions: list[Conclusion] = []

        for rule in self._rule_catalog.rules:
            matching_observations = self._find_matching_observations(observations, rule)

            if matching_observations is not None:
                conclusions.append(
                    Conclusion(
                        statement=rule.conclusion_statement,
                        supporting_observation_ids=tuple(
                            observation.id for observation in matching_observations
                        ),
                        confidence=rule.confidence,
                        created_at=self._clock(),
                    )
                )

        return InvestigationResult(
            observations=observations,
            conclusions=tuple(conclusions),
        )

    @staticmethod
    def _find_matching_observations(
        observations: tuple[Observation, ...],
        rule: InvestigationRule,
    ) -> tuple[Observation, ...] | None:
        matching_observations: list[Observation] = []

        for kind in rule.required_observation_kinds:
            observation = _find_observation(observations, kind)

            if observation is None:
                return None

            matching_observations.append(observation)

        return tuple(matching_observations)


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
