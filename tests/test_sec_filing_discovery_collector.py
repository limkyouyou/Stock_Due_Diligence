"""Tests for SEC filing discovery."""

from datetime import UTC, date, datetime

import httpx
import pytest

from stock_dd.collectors import (
    DiscoveredFiling,
    FilingDiscoveryCollector,
    FilingDiscoveryRequest,
    SECFilingDiscoveryCollector,
)
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

TEST_USER_AGENT = "Stock DD MAS test@example.com"

FIXED_COLLECTION_TIME = datetime(
    2026,
    8,
    28,
    19,
    0,
    tzinfo=UTC,
)


def _filing_columns(
    *,
    accession_numbers: list[str],
    filing_dates: list[str],
    forms: list[str],
    report_dates: list[str],
    acceptance_times: list[str],
    primary_documents: list[str],
    items: list[str],
) -> dict[str, object]:
    return {
        "accessionNumber": accession_numbers,
        "filingDate": filing_dates,
        "form": forms,
        "reportDate": report_dates,
        "acceptanceDateTime": acceptance_times,
        "primaryDocument": primary_documents,
        "items": items,
    }


def test_discover_filters_recent_and_overlapping_history() -> None:
    requests: list[httpx.Request] = []

    recent = _filing_columns(
        accession_numbers=[
            "0000320193-27-000001",
            "0000320193-26-000050",
            "0000320193-25-000080",
            "0000320193-25-000079",
        ],
        filing_dates=[
            "2027-01-10",
            "2026-08-01",
            "2025-11-05",
            "2025-10-31",
        ],
        forms=[
            "10-K",
            "8-K",
            "10-K/A",
            "10-K",
        ],
        report_dates=[
            "2026-12-31",
            "2026-08-01",
            "2025-09-27",
            "2025-09-27",
        ],
        acceptance_times=[
            "2027-01-10T12:00:00.000Z",
            "2026-08-01T20:30:26.000Z",
            "2025-11-05T12:00:00.000Z",
            "2025-10-31T18:04:43.000Z",
        ],
        primary_documents=[
            "future.htm",
            "current-report.htm",
            "amendment.htm",
            "annual-report.htm",
        ],
        items=[
            "",
            "5.02,9.01",
            "",
            "",
        ],
    )

    historical = _filing_columns(
        accession_numbers=[
            "0000320193-24-000050",
            "0000320193-22-000040",
        ],
        filing_dates=[
            "2024-01-15",
            "2022-01-10",
        ],
        forms=[
            "DEF 14A",
            "10-K",
        ],
        report_dates=[
            "2024-01-01",
            "2021-12-31",
        ],
        acceptance_times=[
            "2024-01-15T15:00:00.000Z",
            "2022-01-10T15:00:00.000Z",
        ],
        primary_documents=[
            "proxy.htm",
            "old-annual.htm",
        ],
        items=[
            "",
            "",
        ],
    )

    main_payload: dict[str, object] = {
        "filings": {
            "recent": recent,
            "files": [
                {
                    "name": "CIK0000320193-submissions-001.json",
                    "filingCount": 100,
                    "filingFrom": "2020-01-01",
                    "filingTo": "2024-12-31",
                },
                {
                    "name": "CIK0000320193-submissions-002.json",
                    "filingCount": 1000,
                    "filingFrom": "1994-01-01",
                    "filingTo": "2014-12-31",
                },
            ],
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url.path.endswith("CIK0000320193.json"):
            return httpx.Response(
                status_code=200,
                json=main_payload,
            )

        if request.url.path.endswith("CIK0000320193-submissions-001.json"):
            return httpx.Response(
                status_code=200,
                json=historical,
            )

        raise AssertionError(f"Unexpected SEC request: {request.url}")

    collector = SECFilingDiscoveryCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    typed_collector: FilingDiscoveryCollector = collector

    request = FilingDiscoveryRequest(
        cik="320193",
        forms=(
            "DEF 14A",
            "10-K",
            "8-K",
        ),
        filed_from=date(2023, 1, 1),
        as_of_date=date(2026, 8, 28),
    )

    result = typed_collector.discover(request)

    assert result.provider == "sec"
    assert result.request == request
    assert result.collected_at == FIXED_COLLECTION_TIME

    assert result.filings == (
        DiscoveredFiling(
            accession_number="0000320193-26-000050",
            form="8-K",
            filed_on=date(2026, 8, 1),
            report_date=date(2026, 8, 1),
            accepted_at=datetime(
                2026,
                8,
                1,
                20,
                30,
                26,
                tzinfo=UTC,
            ),
            primary_document="current-report.htm",
            filing_index_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019326000050/"
                "0000320193-26-000050-index.htm"
            ),
            primary_document_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019326000050/"
                "current-report.htm"
            ),
            items=("5.02", "9.01"),
        ),
        DiscoveredFiling(
            accession_number="0000320193-25-000079",
            form="10-K",
            filed_on=date(2025, 10, 31),
            report_date=date(2025, 9, 27),
            accepted_at=datetime(
                2025,
                10,
                31,
                18,
                4,
                43,
                tzinfo=UTC,
            ),
            primary_document="annual-report.htm",
            filing_index_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019325000079/"
                "0000320193-25-000079-index.htm"
            ),
            primary_document_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019325000079/"
                "annual-report.htm"
            ),
        ),
        DiscoveredFiling(
            accession_number="0000320193-24-000050",
            form="DEF 14A",
            filed_on=date(2024, 1, 15),
            report_date=date(2024, 1, 1),
            accepted_at=datetime(
                2024,
                1,
                15,
                15,
                0,
                tzinfo=UTC,
            ),
            primary_document="proxy.htm",
            filing_index_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019324000050/"
                "0000320193-24-000050-index.htm"
            ),
            primary_document_url=(
                "https://www.sec.gov/Archives/edgar/data/"
                "320193/000032019324000050/"
                "proxy.htm"
            ),
        ),
    )

    assert len(requests) == 2

    assert requests[0].url.path == "/submissions/CIK0000320193.json"
    assert requests[1].url.path == "/submissions/CIK0000320193-submissions-001.json"

    assert all(request.headers["User-Agent"] == TEST_USER_AGENT for request in requests)


def test_constructor_rejects_empty_user_agent() -> None:
    with pytest.raises(
        ConfigurationError,
        match="SEC User-Agent must not be empty",
    ):
        SECFilingDiscoveryCollector("   ")


def test_constructor_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_seconds must be greater than zero",
    ):
        SECFilingDiscoveryCollector(
            TEST_USER_AGENT,
            timeout_seconds=0,
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (403, "SEC access was denied"),
        (429, "SEC rate limit was reached"),
        (500, "HTTP status 500"),
    ],
)
def test_discover_translates_http_errors(
    status_code: int,
    message: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            request=request,
        )

    collector = SECFilingDiscoveryCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    request = FilingDiscoveryRequest(
        cik="320193",
        forms=("10-K",),
        as_of_date=date(2026, 8, 28),
    )

    with pytest.raises(
        CollectorError,
        match=message,
    ):
        collector.discover(request)


def test_dicover_translates_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    collector = SECFilingDiscoveryCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    request = FilingDiscoveryRequest(
        cik="320193",
        forms=("10-K",),
        as_of_date=date(2026, 8, 28),
    )

    with pytest.raises(
        CollectorError,
        match="filing-discovery request failed",
    ):
        collector.discover(request)


def test_discover_rejects_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"not-json",
        )

    collector = SECFilingDiscoveryCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    request = FilingDiscoveryRequest(
        cik="320193",
        forms=("10-K",),
        as_of_date=date(2026, 8, 28),
    )

    with pytest.raises(
        CollectorError,
        match="invalid JSON",
    ):
        collector.discover(request)


def test_discover_rejects_misaligned_columns() -> None:
    payload: dict[str, object] = {
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000320193-25-000079",
                ],
                "filingDate": [
                    "2025-10-31",
                ],
                "form": [
                    "10-K",
                    "8-K",
                ],
            },
            "files": [],
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = SECFilingDiscoveryCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    request = FilingDiscoveryRequest(
        cik="320193",
        forms=("10-K",),
        as_of_date=date(2026, 8, 28),
    )

    with pytest.raises(
        CollectorError,
        match="inconsistent lengths",
    ):
        collector.discover(request)
