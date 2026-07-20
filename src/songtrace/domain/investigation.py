from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from songtrace.domain.track import TrackIdentity


class InvestigationStatus(StrEnum):
    """The current state of a SongTrace investigation."""

    AWAITING_EVIDENCE = "Awaiting evidence"


class Investigation(BaseModel):
    """A structured investigation into a track's performance."""

    model_config = ConfigDict(frozen=True)

    track: TrackIdentity
    status: InvestigationStatus = InvestigationStatus.AWAITING_EVIDENCE
