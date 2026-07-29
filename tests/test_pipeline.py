"""Integration tests for the offline research pipeline."""

from pathlib import Path

from stock_dd.pipeline import run_offline_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_FILE = PROJECT_ROOT / "data" / "samples" / "northstar_robotics.json"


def test_run_offline_pipeline_creates_report(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "northstar_report.md"

    result = run_offline_pipeline(
        input_path=SAMPLE_FILE,
        output_path=output_path,
    )

    assert result.company_ticker == "NSTR"
    assert result.output_path == output_path
    assert output_path.exists()

    report = output_path.read_text(encoding="utf-8")

    assert "Northstar Robotics Inc." in report
    assert "USD 160,000,000" in report
    assert "15.94%" in report
    assert "USD 17,000,000" in report
