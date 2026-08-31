"""Persist raw filing documents for auditing and offline replay."""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Final

from stock_dd.collectors.filing_documents import (
    CollectedFilingDocument,
)
from stock_dd.exceptions import RawDataStorageError

_SAFE_PATH_COMPONENT: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


@dataclass(frozen=True, slots=True, kw_only=True)
class StoredRawFilingDocument:
    """Metadata describing one stored raw filing document."""

    path: Path
    sha256: str
    size_bytes: int


def save_raw_filing_document(
    document: CollectedFilingDocument,
    root_directory: str | Path,
) -> StoredRawFilingDocument:
    """Persist the exact bytes returned for one filing document."""

    provider = _validate_path_component(
        document.provider.lower(),
        field_name="provider",
    )

    cik = _validate_path_component(
        document.request.cik,
        field_name="cik",
    )

    accession_number = _validate_path_component(
        document.request.filing.accession_number,
        field_name="accession_number",
    )

    primary_document = document.request.filing.primary_document

    if primary_document is None:
        raise RawDataStorageError(
            "Filing primary document name is required for raw storage."
        )

    document_name = _validate_path_component(
        primary_document,
        field_name="primary_document",
    )

    retrieved_at = _require_aware_datetime(
        document.retrieved_at,
    )

    timestamp = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")

    output_directory = (
        Path(root_directory) / provider / "filings" / cik / accession_number
    )

    output_path = output_directory / f"{timestamp}__{document_name}"

    digest = hashlib.sha256(document.content).hexdigest()

    temporary_path: Path | None = None

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if output_path.exists():
            raise RawDataStorageError(
                f"Raw filing document already exists: {output_path}"
            )

        with NamedTemporaryFile(
            mode="wb",
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_directory,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(document.content)

        temporary_path.replace(output_path)

    except RawDataStorageError:
        raise

    except OSError as error:
        raise RawDataStorageError(
            f"Could not save raw filing document to {output_path}: {error}"
        ) from error

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)

    return StoredRawFilingDocument(
        path=output_path,
        sha256=digest,
        size_bytes=len(document.content),
    )


def _require_aware_datetime(
    value: datetime,
) -> datetime:
    """Return a timezone-aware datetime converted to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise RawDataStorageError("'retrieved_at' must be timezone-aware.")

    return value.astimezone(UTC)


def _validate_path_component(
    value: str,
    *,
    field_name: str,
) -> str:
    """Validate text before using it in a filesystem path."""

    if not _SAFE_PATH_COMPONENT.fullmatch(value):
        raise RawDataStorageError(
            f"'{field_name}' cannot be used safely in a path: {value!r}"
        )

    return value
