"""Command-line entry point for Stock DD MAS."""

import argparse
import sys
from pathlib import Path

from stock_dd.exceptions import ResearchDataError
from stock_dd.pipeline import run_offline_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="stock-dd",
        description=(
            "Generate an offline stock due-diligence report from a JSON research file."
        ),
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input JSON reserach file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=("Optional report output path. Defaults to the reports directory."),
    )

    return parser


def main() -> int:
    """Run the Stock DD command-line application."""

    parser = build_parser()
    arguments = parser.parse_args()

    try:
        result = run_offline_pipeline(
            input_path=arguments.input,
            output_path=arguments.output,
        )
    except ResearchDataError as error:
        print(
            f"Input data error: {error}",
            file=sys.stderr,
        )
        return 2
    except OSError as error:
        print(
            f"File system error: {error}",
            file=sys.stderr,
        )
        return 1

    print(f"Report created for {result.company_ticker}: {result.output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
