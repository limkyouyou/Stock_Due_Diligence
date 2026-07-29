"""Tests for the Stock DD command-line interface."""

import subprocess
import sys
from pathlib import Path

import pytest

from stock_dd import __main__ as cli
from stock_dd.exceptions import ResearchDataError
from stock_dd.pipeline import PipelineResult


def test_main_returns_zero_and_prints_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A successful pipeline run should return exit code zero."""

    input_path = tmp_path / "input.json"
    output_path = tmp_path / "report.md"

    def fake_run_offline_pipeline(
        input_path: str | Path,
        output_path: str | Path | None = None,
    ) -> PipelineResult:
        assert Path(input_path) == tmp_path / "input.json"
        assert output_path == tmp_path / "report.md"

        return PipelineResult(
            input_path=Path(input_path),
            output_path=Path(output_path),
            company_ticker="NSTR",
        )

    monkeypatch.setattr(
        cli,
        "run_offline_pipeline",
        fake_run_offline_pipeline,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stock-dd",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Report created for NSTR: {output_path}" in captured.out
    assert captured.err == ""


def test_main_returns_two_for_invalid_research_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid research data should return exit code two."""

    def fake_fun_offline_pipeline(
        input_path: str | Path,
        output_path: str | Path | None = None,
    ) -> PipelineResult:
        raise ResearchDataError("Required field is missing.")

    monkeypatch.setattr(
        cli,
        "run_offline_pipeline",
        fake_fun_offline_pipeline,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stock-dd",
            "--input",
            "invalid.json",
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Input data error: Required field is missing." in captured.err


def test_main_returns_one_for_file_system_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """File-system failres should return exit code one."""

    def fake_run_offline_pipeline(
        input_path: str | Path,
        output_path: str | Path | None = None,
    ) -> PipelineResult:
        raise OSError("Unable to write report.")

    monkeypatch.setattr(
        cli,
        "run_offline_pipeline",
        fake_run_offline_pipeline,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stock-dd",
            "--input",
            "valid.json",
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "File system error: Unable to write report." in captured.err


def test_package_entry_point_runs_complete_pipeline(
    tmp_path: Path,
) -> None:
    """Executing the package should complete the real CLI pipeline."""
    project_root = Path(__file__).resolve().parents[1]
    sample_path = project_root / "data" / "samples" / "northstar_robotics.json"
    output_path = tmp_path / "entry_point_report.md"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "stock_dd",
            "--input",
            str(sample_path),
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Report created for NSTR" in result.stdout
    assert output_path.exists()
