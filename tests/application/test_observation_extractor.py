"""Tests for deterministic observation extraction from evidence."""

from datetime import UTC, datetime
from uuid import UUID

from songtrace.application.observation_extractor import ObservationExtractor
from songtrace.domain.evidence import Evidence, EvidenceKind, EvidenceSignal
from songtrace.domain.evidence_source import EvidenceSource
from songtrace.domain.observation import ObservationKind

_NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
_OBSERVED_AT = datetime(2026, 7, 20, 21, 30, tzinfo=UTC)
_PLAYLIST_ID = UUID("00000000-0000-0000-0000-000000000001")
_STREAM_ID = UUID("00000000-0000-0000-0000-000000000002")
_SAVE_ID = UUID("00000000-0000-0000-0000-000000000003")
_OTHER_ID = UUID("00000000-0000-0000-0000-000000000004")


def test_generates_stream_observation_from_playlist_and_stream_growth_evidence() -> None:
    playlist_evidence = _playlist_evidence()
    stream_evidence = _stream_evidence()

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence)
    )

    assert len(observations) == 1
    assert observations[0].kind is ObservationKind.PLAYLIST_STREAM_GROWTH
    assert observations[0].summary == "Streams increased after playlist placement."
    assert observations[0].supporting_evidence_ids == (_PLAYLIST_ID, _STREAM_ID)
    assert observations[0].observed_at == _OBSERVED_AT


def test_generates_save_observation_from_playlist_and_save_growth_evidence() -> None:
    playlist_evidence = _playlist_evidence()
    save_evidence = _save_evidence()

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, save_evidence)
    )

    assert len(observations) == 1
    assert observations[0].kind is ObservationKind.PLAYLIST_SAVE_GROWTH
    assert observations[0].summary == "Save activity increased after playlist placement."
    assert observations[0].supporting_evidence_ids == (_PLAYLIST_ID, _SAVE_ID)
    assert observations[0].observed_at == _OBSERVED_AT


def test_generates_stream_and_save_observations_together() -> None:
    playlist_evidence = _playlist_evidence()
    stream_evidence = _stream_evidence()
    save_evidence = _save_evidence()

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence, save_evidence)
    )

    assert [observation.kind for observation in observations] == [
        ObservationKind.PLAYLIST_STREAM_GROWTH,
        ObservationKind.PLAYLIST_SAVE_GROWTH,
    ]
    assert [observation.summary for observation in observations] == [
        "Streams increased after playlist placement.",
        "Save activity increased after playlist placement.",
    ]
    assert observations[0].supporting_evidence_ids == (_PLAYLIST_ID, _STREAM_ID)
    assert observations[1].supporting_evidence_ids == (_PLAYLIST_ID, _SAVE_ID)


def test_generates_no_observations_when_playlist_evidence_is_missing() -> None:
    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (_stream_evidence(), _save_evidence())
    )

    assert observations == ()


def test_ignores_unrelated_evidence() -> None:
    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (_unrelated_evidence(),)
    )

    assert observations == ()


def test_uses_injected_clock_for_observed_at_deterministically() -> None:
    observed_times = (
        datetime(2026, 7, 20, 1, 0, tzinfo=UTC),
        datetime(2026, 7, 20, 2, 0, tzinfo=UTC),
    )
    times = iter(observed_times)

    observations = ObservationExtractor(clock=lambda: next(times)).extract(
        (_playlist_evidence(), _stream_evidence(), _save_evidence())
    )

    assert tuple(observation.observed_at for observation in observations) == observed_times


def test_references_exact_supporting_evidence_ids() -> None:
    playlist_evidence = _playlist_evidence()
    stream_evidence = _stream_evidence()
    unrelated_evidence = _unrelated_evidence()

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (unrelated_evidence, playlist_evidence, stream_evidence)
    )

    assert observations[0].supporting_evidence_ids == (playlist_evidence.id, stream_evidence.id)
    assert unrelated_evidence.id not in observations[0].supporting_evidence_ids


def test_summary_text_does_not_control_matching_when_structured_signals_are_present() -> None:
    playlist_evidence = _evidence(
        id=_PLAYLIST_ID,
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="Track received a curated feature.",
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
    )
    stream_evidence = _evidence(
        id=_STREAM_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Weekly listener behavior changed.",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )
    save_evidence = _evidence(
        id=_SAVE_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Collection behavior changed.",
        signals=(EvidenceSignal.SAVE_GROWTH,),
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence, save_evidence)
    )

    assert len(observations) == 2


def test_summary_keywords_do_not_generate_observations_without_structured_signals() -> None:
    playlist_evidence = _evidence(
        id=_PLAYLIST_ID,
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="Track was ADDED to an Editorial PLAYLIST.",
        signals=(),
    )
    stream_evidence = _evidence(
        id=_STREAM_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="STREAMS GREW 48% week over week.",
        signals=(),
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence)
    )

    assert observations == ()


def _playlist_evidence() -> Evidence:
    return _evidence(
        id=_PLAYLIST_ID,
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track received editorial playlist placement.",
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
    )


def _stream_evidence() -> Evidence:
    return _evidence(
        id=_STREAM_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% week over week.",
        signals=(EvidenceSignal.STREAM_GROWTH,),
    )


def _save_evidence() -> Evidence:
    return _evidence(
        id=_SAVE_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Save activity increased 31% week over week.",
        signals=(EvidenceSignal.SAVE_GROWTH,),
    )


def _unrelated_evidence() -> Evidence:
    return _evidence(
        id=_OTHER_ID,
        kind=EvidenceKind.MEDIA_COVERAGE,
        summary="A blog mentioned the track.",
        signals=(),
    )


def _evidence(
    *,
    id: UUID,
    kind: EvidenceKind,
    summary: str,
    signals: tuple[EvidenceSignal, ...],
) -> Evidence:
    return Evidence(
        source=EvidenceSource("spotify"),
        kind=kind,
        summary=summary,
        observed_at=_NOW,
        signals=signals,
        id=id,
    )
