"""Configure application logging for Stock DD MAS."""

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(*, verbose: bool = False) -> None:
    """Configure logging for the command-line application."""
    log_level = logging.INFO if verbose else logging.WARNING

    logging.basicConfig(
        level=log_level,
        format=_LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
