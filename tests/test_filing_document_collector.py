"""Tests for the filing-document collector contract."""

from datetime import UTC, date, datetime

import pytest

from stock_dd.collectors import (
    CollectedFilingDocument,
    DiscoveredFiling,
    FilingDocumentCollector,
    FilingDocumentRequest,
)


class StubFilingDocumentCollector:
    """Small implementation used to test the contract."""

    @property
    def provider_name(self) -> str:
        return "stub"

    def collect(
        self,
        request: FilingDocumentRequest,
    ) -> CollectedFilingDocument:
        return CollectedFilingDocument(
            provider=self.provider_name,
            request=request,
            source_url=(
                request.filing.primary_document_url or "https://example.com/filing.htm"
            ),
            retrieved_at=datetime(2026, 8, 29, 19, 0, tzinfo=UTC),
            content=b"<html>filing</html>",
            content_type="text/html",
        )


def test_filing_document_accepts_compatible_implementation() -> None:
    collector = StubFilingDocumentCollector()

    assert isinstance(
        collector,
        FilingDocumentCollector,
    )


def test_filing_document_request_normalizes_cik() -> None:
    filing = DiscoveredFiling(
        accession_number="0000320193-25-000079",
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url="https://example.com/index",
    )

    request = FilingDocumentRequest(
        cik=" 320193 ",
        filing=filing,
    )

    assert request.cik == "0000320193"


@pytest.mark.parametrize(
    "cik",
    [
        "",
        "   ",
        "not-a-cik",
        "12345678901",
    ],
)
def test_filing_document_request_rejects_invalid_cik(
    cik: str,
) -> None:
    filing = DiscoveredFiling(
        accession_number="0000320193-25-000079",
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url="https://example.com/index",
    )

    with pytest.raises(
        ValueError,
        match="cik must contain",
    ):
        FilingDocumentRequest(
            cik=cik,
            filing=filing,
        )
