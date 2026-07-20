from songtrace.application import InvestigationService
from songtrace.domain import InvestigationStatus


def test_begin_investigation() -> None:
    service = InvestigationService()

    investigation = service.begin(
        artist="Warrel Dane",
        track="Everything Is Fading",
    )

    assert investigation.track.artist == "Warrel Dane"
    assert investigation.track.title == "Everything Is Fading"
    assert investigation.status is InvestigationStatus.AWAITING_EVIDENCE
