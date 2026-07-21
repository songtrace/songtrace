# ruff: noqa: F403,F405
from tests.presentation.cli.fixtures import *


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "SongTrace 0.1.0" in result.stdout


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
