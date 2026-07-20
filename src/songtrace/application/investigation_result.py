"""Result produced by an investigation service."""

from __future__ import annotations

from dataclasses import dataclass

from songtrace.domain.conclusion import Conclusion
from songtrace.domain.observation import Observation


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    """Observations and conclusions produced during an investigation."""

    observations: tuple[Observation, ...]
    conclusions: tuple[Conclusion, ...]
