# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "SongTrace 0.1.0" in result.stdout


def test_rank_music_data_providers_text_output() -> None:
    result = runner.invoke(app, ["rank-music-data-providers"])

    assert result.exit_code == 0
    assert "SongTrace Music Data Provider Ranking" in result.stdout
    assert "Purpose: proof_case_investigation" in result.stdout
    assert "Chartmetric" in result.stdout
    assert "Spotify for Artists" in result.stdout
    assert "SONGTRACE_SPOTIFY" not in result.stdout


def test_rank_music_data_providers_json_output() -> None:
    result = runner.invoke(app, ["rank-music-data-providers", "--output", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    provider_names = [provider["name"] for provider in payload["providers"]]

    assert payload["purpose"] == "proof_case_investigation"
    assert "Chartmetric" in provider_names
    assert "Spotify for Artists" in provider_names
    assert all(provider["rank"] >= 1 for provider in payload["providers"])
    assert all(provider["score"] >= 0 for provider in payload["providers"])


def test_investigate() -> None:
    result = runner.invoke(
        app,
        [
            "investigate",
            "--artist",
            "Warrel Dane",
            "--track",
            "Everything Is Fading",
        ],
    )

    assert result.exit_code == 0
    assert "SongTrace Investigation" in result.stdout
    assert "Warrel Dane" in result.stdout
    assert "Everything Is Fading" in result.stdout
    assert "Awaiting evidence" in result.stdout
