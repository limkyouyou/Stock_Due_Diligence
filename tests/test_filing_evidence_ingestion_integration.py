"""Integration test for SEC filing evidence ingestion."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from stock_dd.collectors import (
    DiscoveredFiling,
    FilingDocumentRequest,
    SECFilingDocumentCollector,
)
from stock_dd.models import (
    EvidenceSourceId,
    EvidenceSourceType,
)
from stock_dd.repositories.sqlite import (
    SQLiteEvidenceSourceRepository,
)
from stock_dd.services import (
    SECFilingEvidenceIngestionService,
)
from stock_dd.storage.raw_filings import (
    save_raw_filing_document,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import (
    initialize_schema,
)

TEST_USER_AGENT = "Stock DD MAS test@example.com"

RETRIEVED_AT = datetime(
    2026,
    8,
    30,
    15,
    0,
    tzinfo=UTC,
)

CONTENT = b"<html><body>SEC filing evidence</body></html>"

PRIMARY_DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"


def test_sec_filing_snapshot_survives_raw_storage_and_sqlite_reopen(
    tmp_path: Path,
    sqlite_database_path: Path,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=CONTENT,
            headers={
                "Content-Type": "text/html; charset=utf-8",
            },
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: RETRIEVED_AT,
    )

    filing = DiscoveredFiling(
        accession_number="0000320193-25-000079",
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm",
        primary_document="aapl-20250927.htm",
        primary_document_url=PRIMARY_DOCUMENT_URL,
    )

    document = collector.collect(
        FilingDocumentRequest(
            cik="320193",
            filing=filing,
        )
    )

    stored_document = save_raw_filing_document(
        document,
        tmp_path / "raw",
    )

    assert stored_document.path.read_bytes() == CONTENT
    assert stored_document.sha256 == hashlib.sha256(CONTENT).hexdigest()

    source_id = EvidenceSourceId("source-apple-2025-10k")

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        service = SECFilingEvidenceIngestionService(
            repository,
            source_id_factory=lambda: source_id,
        )

        with transaction(connection):
            source = service.ingest(
                document,
                stored_document,
            )

        assert source.source_id == source_id

    with open_sqlite_database(sqlite_database_path) as connection:
        repository = SQLiteEvidenceSourceRepository(connection)

        persisted = repository.get(source_id)

        assert persisted is not None
        assert persisted.source_id == source_id
        assert persisted.source_type is EvidenceSourceType.REGULATORY_FILING
        assert persisted.external_id == "0000320193-25-000079"
        assert persisted.filing_form == "10-K"
        assert persisted.published_on == date(2025, 10, 31)
        assert persisted.retrieved_at == RETRIEVED_AT
        assert persisted.url == PRIMARY_DOCUMENT_URL
        assert persisted.sha256 == hashlib.sha256(CONTENT).hexdigest()
        assert persisted.raw_file_path == stored_document.path.as_posix()

        assert repository.find_by_external_id(
            "0000320193-25-000079",
            source_type=EvidenceSourceType.REGULATORY_FILING,
        ) == (persisted,)
