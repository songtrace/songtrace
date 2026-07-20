import pytest
from pydantic import ValidationError

from songtrace.core.domain import TrackIdentity


def test_track_identity_strips_whitespace() -> None:
    track = TrackIdentity(
        artist="  Warrel Dane  ",
        title="  Everything Is Fading  ",
    )

    assert track.artist == "Warrel Dane"
    assert track.title == "Everything Is Fading"


def test_track_identity_rejects_empty_artist() -> None:
    with pytest.raises(ValidationError):
        TrackIdentity(
            artist="",
            title="Everything Is Fading",
        )
