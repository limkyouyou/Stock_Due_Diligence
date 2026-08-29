"""Tests for the SEC filing-document collector."""

from datetime import UTC, date, datetime

import httpx
import pytest

from stock_dd.collectors import (
    CollectedFilingDocument,
    DiscoveredFiling,
    FilingDocumentCollector,
    FilingDocumentRequest,
    SECFilingDocumentCollector,
)
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

TEST_USER_AGENT = "Stock DD MAS test@example.com"

FIXED_RETRIEVAL_TIME = datetime(
    2026,
    8,
    29,
    19,
    0,
    tzinfo=UTC,
)

PRIMARY_DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"

FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm"


def _make_filing(
    *,
    primary_document: str | None = "aapl-20250927.htm",
    primary_document_url: str | None = PRIMARY_DOCUMENT_URL,
) -> DiscoveredFiling:
    """Create filing metadata used by SEC document tests."""

    return DiscoveredFiling(
        accession_number="0000320193-25-000079",
        form="10-K",
        filed_on=date(2025, 10, 31),
        filing_index_url=FILING_INDEX_URL,
        primary_document=primary_document,
        primary_document_url=primary_document_url,
    )


def _make_request(
    *,
    filing: DiscoveredFiling | None = None,
) -> FilingDocumentRequest:
    """Create a filing-document request used by tests."""

    return FilingDocumentRequest(
        cik="320193",
        filing=filing or _make_filing(),
    )


def test_sec_filing_document_collector_satisfies_contract() -> None:
    collector = SECFilingDocumentCollector(TEST_USER_AGENT)

    typed_collector: FilingDocumentCollector = collector

    assert typed_collector.provider_name == "sec"


def test_collect_returns_exact_sec_document_bytes() -> None:
    requests: list[httpx.Request] = []

    content = b"\x00<html><body>SEC filing \xe2\x80\x94 exact bytes</body></html>\xff"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        return httpx.Response(
            status_code=200,
            content=content,
            headers={
                "Content-Type": "text/html; charset=utf-8",
            },
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_RETRIEVAL_TIME,
    )

    request = _make_request()

    result = collector.collect(request)

    assert result == CollectedFilingDocument(
        provider="sec",
        request=request,
        source_url=PRIMARY_DOCUMENT_URL,
        retrieved_at=FIXED_RETRIEVAL_TIME,
        content=content,
        content_type="text/html",
    )

    assert len(requests) == 1

    sent_request = requests[0]

    assert str(sent_request.url) == PRIMARY_DOCUMENT_URL
    assert sent_request.headers["User-Agent"] == TEST_USER_AGENT
    assert sent_request.headers["Accept"] == "*/*"


def test_collect_preserves_missing_content_type() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"<html>filing</html>",
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_RETRIEVAL_TIME,
    )

    result = collector.collect(_make_request())

    assert result.content_type is None


def test_collect_rejects_missing_primary_document_url() -> None:
    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
    )

    filing = _make_filing(
        primary_document_url=None,
    )

    with pytest.raises(
        CollectorError,
        match="does not provide a primary-document URL",
    ):
        collector.collect(_make_request(filing=filing))


@pytest.mark.parametrize(
    "url",
    [
        "http://www.sec.gov/Archives/edgar/data/320193/filing.htm",
        "https://data.sec.gov/Archives/edgar/data/320193/filing.htm",
        "https://www.sec.gov/not-the-edgar-archive/filing.htm",
        "https://example.com/filing.htm",
    ],
)
def test_collect_rejects_non_sec_archive_url(
    url: str,
) -> None:
    collector = SECFilingDocumentCollector(TEST_USER_AGENT)

    filing = _make_filing(
        primary_document_url=url,
    )

    with pytest.raises(
        CollectorError,
        match="not a valid SEC EDGAR archive URL",
    ):
        collector.collect(_make_request(filing=filing))


def test_constructor_rejects_empty_user_agent() -> None:
    with pytest.raises(
        ConfigurationError,
        match="SEC User-Agent must not be empty",
    ):
        SECFilingDocumentCollector("    ")


def test_constructor_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_seconds must be greater than zero",
    ):
        SECFilingDocumentCollector(
            TEST_USER_AGENT,
            timeout_seconds=0,
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (
            403,
            "access was denied",
        ),
        (
            429,
            "rate limit",
        ),
        (
            500,
            "HTTP status 500",
        ),
    ],
)
def test_collect_translates_http_errors(
    status_code: int,
    message: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match=message,
    ):
        collector.collect(_make_request())


def test_collect_translates_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="SEC filing-document request failed",
    ):
        collector.collect(_make_request())


def test_collect_rejects_empty_response_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"",
            request=request,
        )

    collector = SECFilingDocumentCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="returned an empty filing document",
    ):
        collector.collect(_make_request())
