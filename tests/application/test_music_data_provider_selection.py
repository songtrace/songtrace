from dataclasses import FrozenInstanceError

import pytest

from songtrace.application import (
    MusicDataAccessMode,
    MusicDataFormat,
    MusicDataProviderCandidate,
    MusicDataProviderCatalog,
    MusicEvidenceCapability,
    rank_music_data_providers,
)


def test_music_data_provider_candidate_valid_construction_trims_text() -> None:
    candidate = MusicDataProviderCandidate(
        name="  Example Provider  ",
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.CSV,),
        capabilities=(MusicEvidenceCapability.SOURCE_ATTRIBUTION,),
        strengths=("  useful exports  ",),
        constraints=("  verify terms  ", "   "),
        proof_case_relevance="  useful for source attribution  ",
    )

    assert candidate.name == "Example Provider"
    assert candidate.strengths == ("useful exports",)
    assert candidate.constraints == ("verify terms",)
    assert candidate.proof_case_relevance == "useful for source attribution"
    assert candidate.proof_case_score == 5


@pytest.mark.parametrize(
    ("field_name", "kwargs", "message"),
    [
        ("name", {"name": "   "}, "name must not be blank"),
        ("access_modes", {"access_modes": ()}, "access_modes must not be empty"),
        ("likely_formats", {"likely_formats": ()}, "likely_formats must not be empty"),
        ("capabilities", {"capabilities": ()}, "capabilities must not be empty"),
        ("strengths", {"strengths": ("   ",)}, "strengths must not be empty"),
        (
            "proof_case_relevance",
            {"proof_case_relevance": "   "},
            "proof_case_relevance must not be blank",
        ),
    ],
)
def test_music_data_provider_candidate_rejects_required_blank_or_empty_values(
    field_name: str,
    kwargs: dict[str, object],
    message: str,
) -> None:
    values = _candidate_kwargs()
    values.update(kwargs)

    with pytest.raises(ValueError, match=message):
        MusicDataProviderCandidate(**values)  # type: ignore[arg-type]

    assert field_name


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "access_modes": (
                    MusicDataAccessMode.USER_EXPORT,
                    MusicDataAccessMode.USER_EXPORT,
                )
            },
            "access_modes must not contain duplicates",
        ),
        (
            {"likely_formats": (MusicDataFormat.CSV, MusicDataFormat.CSV)},
            "likely_formats must not contain duplicates",
        ),
        (
            {
                "capabilities": (
                    MusicEvidenceCapability.SOURCE_ATTRIBUTION,
                    MusicEvidenceCapability.SOURCE_ATTRIBUTION,
                )
            },
            "capabilities must not contain duplicates",
        ),
    ],
)
def test_music_data_provider_candidate_rejects_duplicate_tuple_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    values = _candidate_kwargs()
    values.update(kwargs)

    with pytest.raises(ValueError, match=message):
        MusicDataProviderCandidate(**values)  # type: ignore[arg-type]


def test_music_data_provider_candidate_is_immutable() -> None:
    candidate = _candidate("Example")

    with pytest.raises(FrozenInstanceError):
        candidate.name = "Changed"  # type: ignore[misc]

    assert isinstance(candidate.capabilities, tuple)


def test_music_data_provider_catalog_default_returns_immutable_tuple_with_expected_providers() -> (
    None
):
    catalog = MusicDataProviderCatalog.default()
    names = tuple(candidate.name for candidate in catalog.candidates)

    assert isinstance(catalog.candidates, tuple)
    assert "Chartmetric" in names
    assert "Soundcharts" in names
    assert "Songstats" in names
    assert "Spotify for Artists" in names
    assert "ASCAP royalty statements" in names


def test_music_data_provider_catalog_rejects_empty_candidates() -> None:
    with pytest.raises(ValueError):
        MusicDataProviderCatalog(candidates=())


def test_music_data_provider_catalog_rejects_duplicate_names_case_insensitively() -> None:
    with pytest.raises(ValueError, match="candidates must not contain duplicate names"):
        MusicDataProviderCatalog(candidates=(_candidate("Provider"), _candidate(" provider ")))


def test_rank_music_data_providers_orders_by_score_then_name() -> None:
    lower = _candidate("Lower", capabilities=(MusicEvidenceCapability.TRACK_IDENTITY,))
    beta = _candidate("Beta", capabilities=(MusicEvidenceCapability.SOURCE_ATTRIBUTION,))
    alpha = _candidate("Alpha", capabilities=(MusicEvidenceCapability.SOURCE_ATTRIBUTION,))
    catalog = MusicDataProviderCatalog(candidates=(lower, beta, alpha))

    ranked = rank_music_data_providers(catalog)

    assert tuple(item.candidate.name for item in ranked) == ("Alpha", "Beta", "Lower")
    assert tuple(item.rank for item in ranked) == (1, 2, 3)
    assert tuple(item.score for item in ranked) == (5, 5, 1)


def test_rank_music_data_providers_default_is_deterministic() -> None:
    first = rank_music_data_providers()
    second = rank_music_data_providers()

    assert first == second
    assert first[0].score >= first[-1].score


def _candidate(
    name: str,
    *,
    capabilities: tuple[MusicEvidenceCapability, ...] = (
        MusicEvidenceCapability.SOURCE_ATTRIBUTION,
    ),
) -> MusicDataProviderCandidate:
    return MusicDataProviderCandidate(
        name=name,
        access_modes=(MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        likely_formats=(MusicDataFormat.CSV,),
        capabilities=capabilities,
        strengths=("Useful for testing.",),
        constraints=(),
        proof_case_relevance="Relevant for testing.",
    )


def _candidate_kwargs() -> dict[str, object]:
    return {
        "name": "Example Provider",
        "access_modes": (MusicDataAccessMode.COMMERCIAL_SUBSCRIPTION,),
        "likely_formats": (MusicDataFormat.CSV,),
        "capabilities": (MusicEvidenceCapability.SOURCE_ATTRIBUTION,),
        "strengths": ("Useful exports.",),
        "constraints": (),
        "proof_case_relevance": "Useful for source attribution.",
    }
