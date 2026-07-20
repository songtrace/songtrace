from typer.testing import CliRunner

from songtrace.cli.main import app

runner = CliRunner()


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
