"""Tests for SEC filing-evidence ingestion."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from stock_dd.collectors import (
    CollectedFilingDocument,
    DiscoveredFiling,
    FilingDocumentRequest,
)
from stock_dd.exceptions import NormalizationError
from stock_dd.models import (
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
)
from stock_dd.repositories import EvidenceSourceRepository
from stock_dd.services import SECFilingEvidenceIngestionService
from stock_dd.storage.raw_filings import StoredRawFilingDocument

RETRIEVED_AT = datetime(
    2026,
    8,
    30,
    15,
    0,
    tzinfo=UTC,
)

CONTENT = b"<html><body>SEC filing</body></html>"

PRIMARY_DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"


class InMemoryEvidenceSourceRepository:
    """Small evidence repository used by service tests."""

    def __init__(self) -> None:
        self.sources: dict[
            EvidenceSourceId,
            EvidenceSource,
        ] = {}

    def save(
        self,
        source: EvidenceSource,
    ) -> None:
        self.sources[source.source_id] = source

    def get(
        self,
        source_id: EvidenceSourceId,
    ) -> EvidenceSource | None:
        return self.sources.get(source_id)

    def find_by_external_id(
        self,
        external_id: str,
        *,
        source_type: EvidenceSourceType | None = None,
    ) -> tuple[EvidenceSource, ...]:
        return tuple(
            source
            for source in self.sources.values()
            if source.external_id == external_id
            and (source_type is None or source.source_type is source_type)
        )


def _make_document(
    *,
    provider: str = "sec",
    source_url: str = PRIMARY_DOCUMENT_URL,
    content: bytes = CONTENT,
) -> CollectedFilingDocument:
    filing = DiscoveredFiling(
        accession_number="0000320193-25-000079",
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm",
        primary_document="aapl-20250927.htm",
        primary_document_url=PRIMARY_DOCUMENT_URL,
    )

    return CollectedFilingDocument(
        provider=provider,
        request=FilingDocumentRequest(
            cik="320193",
            filing=filing,
        ),
        source_url=source_url,
        retrieved_at=RETRIEVED_AT,
        content=content,
        content_type="text/html",
    )


def _make_stored_document(
    *,
    content: bytes = CONTENT,
    sha256: str | None = None,
    size_bytes: int | None = None,
) -> StoredRawFilingDocument:
    return StoredRawFilingDocument(
        path=Path("data/raw/sec/filings/0000320193/0000320193-25-000079/filing.htm"),
        sha256=sha256 if sha256 is not None else hashlib.sha256(content).hexdigest(),
        size_bytes=size_bytes if size_bytes is not None else len(content),
    )


def test_sec_filing_evidence_service_satisfies_repository_contract() -> None:
    repository = InMemoryEvidenceSourceRepository()

    assert isinstance(
        repository,
        EvidenceSourceRepository,
    )


def test_ingest_creates_trusted_evidence_source() -> None:
    repository = InMemoryEvidenceSourceRepository()

    service = SECFilingEvidenceIngestionService(
        repository,
        source_id_factory=lambda: EvidenceSourceId("source-apple-10k"),
    )

    document = _make_document()
    stored_document = _make_stored_document()

    result = service.ingest(
        document,
        stored_document,
    )

    expected = EvidenceSource(
        source_id=EvidenceSourceId("source-apple-10k"),
        source_type=EvidenceSourceType.REGULATORY_FILING,
        title="SEC 10-K filing 0000320193-25-000079",
        publisher="U.S. Securities and Exchange Commission",
        retrieved_at=RETRIEVED_AT,
        published_on=date(2025, 10, 31),
        url=PRIMARY_DOCUMENT_URL,
        external_id="0000320193-25-000079",
        filing_form="10-K",
        raw_file_path="data/raw/sec/filings/0000320193/0000320193-25-000079/filing.htm",
        sha256=hashlib.sha256(CONTENT).hexdigest(),
        language="en",
    )

    assert result == expected
    assert repository.get(EvidenceSourceId("source-apple-10k")) == expected


def test_ingest_creates_new_source_for_each_snapshot() -> None:
    repository = InMemoryEvidenceSourceRepository()

    source_ids = iter(
        (
            EvidenceSourceId("source-first"),
            EvidenceSourceId("source-second"),
        )
    )

    service = SECFilingEvidenceIngestionService(
        repository,
        source_id_factory=lambda: next(source_ids),
    )

    document = _make_document()
    stored_document = _make_stored_document()

    first = service.ingest(
        document,
        stored_document,
    )
    second = service.ingest(
        document,
        stored_document,
    )

    assert first.source_id == EvidenceSourceId("source-first")
    assert second.source_id == EvidenceSourceId("source-second")

    assert repository.find_by_external_id(
        "0000320193-25-000079",
        source_type=EvidenceSourceType.REGULATORY_FILING,
    ) == (
        first,
        second,
    )


def test_ingest_rejects_non_sec_document() -> None:
    service = SECFilingEvidenceIngestionService(InMemoryEvidenceSourceRepository())

    with pytest.raises(
        NormalizationError,
        match="requires a document collected from SEC",
    ):
        service.ingest(
            _make_document(provider="other"),
            _make_stored_document(),
        )


def test_ingest_rejects_mismatched_source_url() -> None:
    service = SECFilingEvidenceIngestionService(InMemoryEvidenceSourceRepository())

    with pytest.raises(
        NormalizationError,
        match="source URL does not match",
    ):
        service.ingest(
            _make_document(
                source_url="https://www.sec.gov/Archives/edgar/data/320193/other.htm"
            ),
            _make_stored_document(),
        )


def test_ingest_rejects_mismatched_size() -> None:
    service = SECFilingEvidenceIngestionService(InMemoryEvidenceSourceRepository())

    with pytest.raises(
        NormalizationError,
        match="size does not match",
    ):
        service.ingest(
            _make_document(),
            _make_stored_document(
                size_bytes=len(CONTENT) + 1,
            ),
        )


def test_ingest_rejects_mismatched_sha256() -> None:
    service = SECFilingEvidenceIngestionService(InMemoryEvidenceSourceRepository())

    with pytest.raises(
        NormalizationError,
        match="SHA-256 does not match",
    ):
        service.ingest(
            _make_document(),
            _make_stored_document(
                sha256="0" * 64,
            ),
        )
