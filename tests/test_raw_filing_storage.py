"""Tests for raw SEC filing-document storage."""

import hashlib
from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

import pytest

from stock_dd.collectors import (
    CollectedFilingDocument,
    DiscoveredFiling,
    FilingDocumentRequest,
)
from stock_dd.exceptions import RawDataStorageError
from stock_dd.storage.raw_filings import (
    save_raw_filing_document,
)

FIXED_RETRIEVAL_TIME = datetime(2026, 8, 29, 19, 0, tzinfo=UTC)

PRIMARY_DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"

FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm"

RAW_CONTENT = b"\x00<html><body>SEC filing \xe2\x80\x94 exact bytes</body></html>\xff"


def _make_document(
    *,
    retrieved_at: datetime = FIXED_RETRIEVAL_TIME,
    provider: str = "sec",
    accession_number: str = "0000320193-25-000079",
    primary_document: str | None = "aapl-20250927.htm",
    content: bytes = RAW_CONTENT,
) -> CollectedFilingDocument:
    """Create a collected filing document used by storage tests."""

    primary_document_url = (
        PRIMARY_DOCUMENT_URL if primary_document is not None else None
    )

    filing = DiscoveredFiling(
        accession_number=accession_number,
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url=FILING_INDEX_URL,
        primary_document=primary_document,
        primary_document_url=primary_document_url,
    )

    request = FilingDocumentRequest(
        cik="320193",
        filing=filing,
    )

    return CollectedFilingDocument(
        provider=provider,
        request=request,
        source_url=primary_document_url or FILING_INDEX_URL,
        retrieved_at=retrieved_at,
        content=content,
        content_type="text/html",
    )


def test_save_raw_filing_document_preserves_exact_bytes(
    tmp_path: Path,
) -> None:
    document = _make_document()

    result = save_raw_filing_document(
        document,
        tmp_path,
    )

    expected_path = (
        tmp_path
        / "sec"
        / "filings"
        / "0000320193"
        / "0000320193-25-000079"
        / "20260829T190000000000Z__aapl-20250927.htm"
    )

    assert result.path == expected_path
    assert result.path.read_bytes() == document.content

    assert result.sha256 == hashlib.sha256(document.content).hexdigest()

    assert result.size_bytes == len(document.content)


def test_save_raw_filing_document_converts_timestamp_to_utc(
    tmp_path: Path,
) -> None:
    toronto_offset = timezone(timedelta(hours=-4))

    retrieved_at = datetime(
        2026,
        8,
        29,
        15,
        0,
        tzinfo=toronto_offset,
    )

    document = _make_document(retrieved_at=retrieved_at)

    result = save_raw_filing_document(
        document,
        tmp_path,
    )

    assert result.path.name == "20260829T190000000000Z__aapl-20250927.htm"


def test_save_raw_filing_document_rejects_naive_timestamp(
    tmp_path: Path,
) -> None:
    document = _make_document(
        retrieved_at=datetime(
            2026,
            8,
            29,
            19,
            0,
        ),
    )

    with pytest.raises(
        RawDataStorageError,
        match="retrieved_at.*timezone-aware",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )


def test_save_raw_filing_document_requires_primary_document_name(
    tmp_path: Path,
) -> None:
    document = _make_document(
        primary_document=None,
    )

    with pytest.raises(
        RawDataStorageError,
        match="primary document name is required",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )


def test_save_raw_filing_document_rejects_unsafe_primary_document(
    tmp_path: Path,
) -> None:
    document = _make_document(primary_document="../filing.htm")

    with pytest.raises(
        RawDataStorageError,
        match="primary_document",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )


def test_save_raw_filinig_document_rejects_unsafe_provider(
    tmp_path: Path,
) -> None:
    document = _make_document(
        provider="../sec",
    )

    with pytest.raises(
        RawDataStorageError,
        match="provider",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )


def test_save_raw_filing_document_rejects_unsafe_accession_number(
    tmp_path: Path,
) -> None:
    document = _make_document(
        accession_number="../filing",
    )

    with pytest.raises(
        RawDataStorageError,
        match="accession_number",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )


def test_save_raw_filing_document_does_not_overwrite_existing_file(
    tmp_path: Path,
) -> None:
    document = _make_document()

    first_result = save_raw_filing_document(
        document,
        tmp_path,
    )

    original_byte = first_result.path.read_bytes()

    with pytest.raises(
        RawDataStorageError,
        match="already exists",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )

    assert first_result.path.read_bytes() == original_byte
    assert original_byte == document.content


def test_save_raw_filing_document_cleans_temporary_file_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = _make_document()

    def fail_replace(
        self: Path,
        target: Path,
    ) -> Path:
        raise OSError(f"Could not replace {target}")

    monkeypatch.setattr(
        Path,
        "replace",
        fail_replace,
    )

    with pytest.raises(
        RawDataStorageError,
        match="Could not save raw filing document",
    ):
        save_raw_filing_document(
            document,
            tmp_path,
        )

    output_directory = (
        tmp_path / "sec" / "filings" / "0000320193" / "0000320193-25-000079"
    )

    assert output_directory.exists()
    assert tuple(output_directory.iterdir()) == ()
