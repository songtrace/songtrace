"""Tests for deterministic observation extraction from evidence."""

from datetime import UTC, datetime
from uuid import UUID

from songtrace.application.observation_extractor import ObservationExtractor
from songtrace.domain.evidence import Evidence, EvidenceKind, EvidenceSignal
from songtrace.domain.evidence_source import EvidenceSource
from songtrace.domain.observation import ObservationKind
from songtrace.domain.track import TrackIdentity

_NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
_OBSERVED_AT = datetime(2026, 7, 20, 21, 30, tzinfo=UTC)
_PLAYLIST_ID = UUID("00000000-0000-0000-0000-000000000001")
_STREAM_ID = UUID("00000000-0000-0000-0000-000000000002")
_SAVE_ID = UUID("00000000-0000-0000-0000-000000000003")
_OTHER_ID = UUID("00000000-0000-0000-0000-000000000004")
_ROYALTY_ID = UUID("00000000-0000-0000-0000-000000000005")


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


def test_generates_stream_observation_when_track_identities_match() -> None:
    track = TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    playlist_evidence = _playlist_evidence(track=track)
    stream_evidence = _stream_evidence(track=track)

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence)
    )

    assert len(observations) == 1
    assert observations[0].kind is ObservationKind.PLAYLIST_STREAM_GROWTH
    assert observations[0].supporting_evidence_ids == (playlist_evidence.id, stream_evidence.id)


def test_generates_save_observation_when_track_identities_match() -> None:
    track = TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    playlist_evidence = _playlist_evidence(track=track)
    save_evidence = _save_evidence(track=track)

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, save_evidence)
    )

    assert len(observations) == 1
    assert observations[0].kind is ObservationKind.PLAYLIST_SAVE_GROWTH
    assert observations[0].supporting_evidence_ids == (playlist_evidence.id, save_evidence.id)


def test_does_not_generate_playlist_observations_when_known_track_identities_differ() -> None:
    playlist_evidence = _playlist_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    )
    stream_evidence = _stream_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Brother", isrc="USABC0800002")
    )
    save_evidence = _save_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Brother", isrc="USABC0800002")
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence, save_evidence)
    )

    assert observations == ()


def test_missing_track_identity_preserves_existing_playlist_observation_behavior() -> None:
    playlist_evidence = _playlist_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    )
    stream_evidence = _stream_evidence(track=None)

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence)
    )

    assert len(observations) == 1
    assert observations[0].supporting_evidence_ids == (playlist_evidence.id, stream_evidence.id)


def test_same_artist_and_title_with_different_isrc_does_not_match() -> None:
    playlist_evidence = _playlist_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    )
    stream_evidence = _stream_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800002")
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence)
    )

    assert observations == ()


def test_uses_first_compatible_track_identity_pair_deterministically() -> None:
    other_playlist = _playlist_evidence(
        id=UUID("00000000-0000-0000-0000-000000000006"),
        track=TrackIdentity(artist="Warrel Dane", title="Brother", isrc="USABC0800002"),
    )
    matching_playlist = _playlist_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    )
    stream_evidence = _stream_evidence(
        track=TrackIdentity(artist="Warrel Dane", title="Everything Is Fading", isrc="USABC0800001")
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (other_playlist, matching_playlist, stream_evidence)
    )

    assert len(observations) == 1
    assert observations[0].supporting_evidence_ids == (matching_playlist.id, stream_evidence.id)


def test_generates_royalty_reported_observation() -> None:
    royalty_evidence = _royalty_evidence()

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract((royalty_evidence,))

    assert len(observations) == 1
    assert observations[0].kind is ObservationKind.ROYALTY_REPORTED
    assert observations[0].summary == "Royalty activity was reported."
    assert observations[0].supporting_evidence_ids == (_ROYALTY_ID,)
    assert observations[0].observed_at == _OBSERVED_AT


def test_generates_no_playlist_observations_when_playlist_evidence_is_missing() -> None:
    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (_stream_evidence(), _save_evidence())
    )

    assert observations == ()


def test_ignores_unrelated_evidence() -> None:
    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (_unrelated_evidence(),)
    )

    assert observations == ()


def test_generates_playlist_and_royalty_observations_together_in_deterministic_order() -> None:
    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (_royalty_evidence(), _playlist_evidence(), _stream_evidence(), _save_evidence())
    )

    assert [observation.kind for observation in observations] == [
        ObservationKind.PLAYLIST_STREAM_GROWTH,
        ObservationKind.PLAYLIST_SAVE_GROWTH,
        ObservationKind.ROYALTY_REPORTED,
    ]


def test_uses_injected_clock_for_observed_at_deterministically() -> None:
    observed_times = (
        datetime(2026, 7, 20, 1, 0, tzinfo=UTC),
        datetime(2026, 7, 20, 2, 0, tzinfo=UTC),
        datetime(2026, 7, 20, 3, 0, tzinfo=UTC),
    )
    times = iter(observed_times)

    observations = ObservationExtractor(clock=lambda: next(times)).extract(
        (_playlist_evidence(), _stream_evidence(), _save_evidence(), _royalty_evidence())
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
    royalty_evidence = _evidence(
        id=_ROYALTY_ID,
        kind=EvidenceKind.ROYALTY_ACTIVITY,
        summary="ROYALTIES were REPORTED for a statement period.",
        signals=(),
    )

    observations = ObservationExtractor(clock=lambda: _OBSERVED_AT).extract(
        (playlist_evidence, stream_evidence, royalty_evidence)
    )

    assert observations == ()


def _playlist_evidence(
    *,
    id: UUID = _PLAYLIST_ID,
    track: TrackIdentity | None = None,
) -> Evidence:
    return _evidence(
        id=id,
        kind=EvidenceKind.PLAYLIST_ACTIVITY,
        summary="The track received editorial playlist placement.",
        signals=(EvidenceSignal.PLAYLIST_PLACEMENT,),
        track=track,
    )


def _stream_evidence(*, track: TrackIdentity | None = None) -> Evidence:
    return _evidence(
        id=_STREAM_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Streams increased 48% week over week.",
        signals=(EvidenceSignal.STREAM_GROWTH,),
        track=track,
    )


def _save_evidence(*, track: TrackIdentity | None = None) -> Evidence:
    return _evidence(
        id=_SAVE_ID,
        kind=EvidenceKind.AUDIENCE_ACTIVITY,
        summary="Save activity increased 31% week over week.",
        signals=(EvidenceSignal.SAVE_GROWTH,),
        track=track,
    )


def _royalty_evidence() -> Evidence:
    return _evidence(
        id=_ROYALTY_ID,
        kind=EvidenceKind.ROYALTY_ACTIVITY,
        summary="Royalties were reported for a synthetic statement period.",
        signals=(EvidenceSignal.ROYALTY_REPORTED,),
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
    track: TrackIdentity | None = None,
) -> Evidence:
    return Evidence(
        source=EvidenceSource("spotify"),
        kind=kind,
        summary=summary,
        observed_at=_NOW,
        signals=signals,
        track=track,
        id=id,
    )
