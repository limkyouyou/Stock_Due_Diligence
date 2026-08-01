"""Command-line entry point for Stock DD MAS."""

import argparse
import sys
from pathlib import Path

from stock_dd.collectors.fmp import FMPFinancialDataCollector
from stock_dd.config import load_settings
from stock_dd.exceptions import ResearchDataError, StockDDError
from stock_dd.logging_config import configure_logging
from stock_dd.normalizers.fmp import normalize_fmp_dataset
from stock_dd.pipeline import (
    run_live_pipeline,
    run_offline_pipeline,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="stock-dd",
        description=("Generate stock due-diligence reports."),
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show application progress logs."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    offline_parser = subparsers.add_parser(
        "offline", help="Generate a report from a local JSON research file."
    )
    offline_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input JSON research file.",
    )
    offline_parser.add_argument(
        "--output", type=Path, help="Optional report output path."
    )

    live_parser = subparsers.add_parser(
        "live", help="Collect live financial data and generate a report."
    )
    live_parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker to research, such as AAPL",
    )
    live_parser.add_argument(
        "--annual-limit",
        type=int,
        default=5,
        help="Number of annual financial periods to request.",
    )
    live_parser.add_argument("--output", type=Path, help="Optinal report output path.")

    return parser


def main() -> int:
    """Run the Stock DD command-line application."""

    parser = build_parser()
    arguments = parser.parse_args()

    configure_logging(verbose=arguments.verbose)

    try:
        if arguments.command == "offline":
            offline_result = run_offline_pipeline(
                input_path=arguments.input,
                output_path=arguments.output,
            )

            print(
                f"Report created for {offline_result.company_ticker}: {offline_result.output_path}"
            )
            return 0

        settings = load_settings()

        collector = FMPFinancialDataCollector(settings.require_financial_api_key())

        live_result = run_live_pipeline(
            arguments.ticker,
            collector=collector,
            normalizer=normalize_fmp_dataset,
            raw_data_directory=settings.raw_data_directory,
            output_path=arguments.output,
            annual_limit=arguments.annual_limit,
        )

        print(
            f"Report created for {live_result.company_ticker}: {live_result.report_path}"
        )
        print(f"Raw data saved: {live_result.raw_data_path}")

        return 0
    except ResearchDataError as error:
        print(
            f"Input data error: {error}",
            file=sys.stderr,
        )

        return 2

    except StockDDError as error:
        print(
            f"Application error: {error}",
            file=sys.stderr,
        )

        return 2
    except OSError as error:
        print(
            f"File system error: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
