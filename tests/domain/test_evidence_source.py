"""Tests for the EvidenceSource domain value object."""

from dataclasses import FrozenInstanceError

import pytest

from songtrace.domain.evidence_source import EvidenceSource


def test_creates_evidence_source() -> None:
    source = EvidenceSource("spotify")

    assert source.name == "spotify"
    assert str(source) == "spotify"


@pytest.mark.parametrize(
    ("provided", "expected"),
    [
        ("Spotify", "spotify"),
        (" ASCAP ", "ascap"),
        ("apple music", "apple_music"),
        ("YouTube Music", "youtube_music"),
    ],
)
def test_normalizes_source_name(provided: str, expected: str) -> None:
    assert EvidenceSource(provided).name == expected


@pytest.mark.parametrize("name", ["", " ", "\n"])
def test_rejects_empty_source_name(name: str) -> None:
    with pytest.raises(ValueError, match="source name must not be empty"):
        EvidenceSource(name)


def test_evidence_source_is_immutable() -> None:
    source = EvidenceSource("spotify")

    with pytest.raises(FrozenInstanceError):
        source.name = "youtube"  # type: ignore[misc]


def test_sources_with_equal_names_are_equal() -> None:
    assert EvidenceSource("Spotify") == EvidenceSource("spotify")
