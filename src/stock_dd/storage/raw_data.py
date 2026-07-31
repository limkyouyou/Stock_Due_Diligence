"""Persist raw provider responses for auditing and offline replay."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Final

from stock_dd.collectors.base import RawFinancialDataset
from stock_dd.exceptions import RawDataStorageError

_SCHEMA_VERSION: Final = 1
_SAFE_PATH_COMPONENT: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def save_raw_financial_dataset(
    dataset: RawFinancialDataset,
    root_directory: str | Path,
) -> Path:
    """
    Save a raw financial dataset in a versioned JSON envelop.

    The file is first written to a temporary file and then moved to its final location.
    This reduces the risk of leaving a partially written JSON file if writing fails.

    Args:
        dataset: Raw provider data to store.
        root_directory: Root directory for raw provider data.

    Returns:
        Path to the saved JSON file.

    Raises:
        RawDataStorageError: If the dataset cannot be stored safely.
    """

    provider = _validate_path_component(
        dataset.provider.lower(),
        field_name="provider",
    )
    ticker = _validate_path_component(
        dataset.ticker.upper(),
        field_name="ticker",
    )
    collected_at = _require_aware_datetime(dataset.collected_at)

    timestamp = collected_at.strftime("%Y%m%dT%H%M%S%fZ")

    output_directory = Path(root_directory) / provider / ticker
    output_path = output_directory / f"{timestamp}.json"

    envelope: dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "provider": dataset.provider,
        "ticker": dataset.ticker,
        "collected_at": _format_datetime(collected_at),
        "payloads": dict(dataset.payloads),
    }

    temporary_path: Path | None = None

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if output_path.exists():
            raise RawDataStorageError(
                f"Raw financial dataset already exists: {output_path}"
            )

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_directory,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            json.dump(
                envelope,
                temporary_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            temporary_file.write("\n")

        temporary_path.replace(output_path)

    except RawDataStorageError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise RawDataStorageError(
            f"Could not save raw financial dataset to {output_path}: {error}"
        ) from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)

    return output_path


def _require_aware_datetime(value: datetime) -> datetime:
    """
    Return a datetime converted to UTC.

    A timezone-aware timestamp is required so collection times are unambiguous across computers and time zones.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        raise RawDataStorageError("'collected_at' must be timezone-aware.")

    return value.astimezone(UTC)


def _validate_path_component(
    value: str,
    *,
    field_name: str,
) -> str:
    """Validate text before using it as part of a file-system path."""

    if not _SAFE_PATH_COMPONENT.fullmatch(value):
        raise RawDataStorageError(
            f"'{field_name}' cannot be used safely in a path: {value!r}"
        )

    return value


def _format_datetime(value: datetime) -> str:
    """Firmate a UTC datetime using ISO 8601 notation."""

    return value.isoformat().replace("+00:00", "Z")
