"""Test for the Financial Modeling Prep collector."""

from datetime import UTC, datetime

import httpx
import pytest

from stock_dd.collectors.base import FinancialDataCollector
from stock_dd.collectors.fmp import FMPFinancialDataCollector
from stock_dd.exceptions import CollectorError, ConfigurationError

FIXED_COLLECTION_TIME = datetime(
    2026,
    7,
    31,
    18,
    30,
    tzinfo=UTC,
)


def test_fmp_collector_satisfies_collector_interface() -> None:
    collector = FMPFinancialDataCollector("test-key")

    typed_collector: FinancialDataCollector = collector

    assert typed_collector.provider_name == "fmp"


def test_collect_retrieves_all_expected_payloads() -> None:
    requests: list[httpx.Request] = []

    responses: dict[str, object] = {
        "/stable/profile": [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
            }
        ],
        "/stable/income-statement": [
            {
                "symbol": "AAPL",
                "calendarYear": "2025",
                "revenue": 100,
            }
        ],
        "/stable/balance-sheet-statement": [
            {
                "symbol": "AAPL",
                "calendarYear": "2025",
                "cashAndCashEquivalents": 50,
            }
        ],
        "/stable/cash-flow-statement": [
            {
                "symbol": "AAPL",
                "calendarYear": "2025",
                "operatingCashFlow": 30,
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        payload = responses[request.url.path]

        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = FMPFinancialDataCollector(
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    result = collector.collect(
        " aapl ",
        annual_limit=3,
    )

    assert result.provider == "fmp"
    assert result.ticker == "AAPL"
    assert result.collected_at == FIXED_COLLECTION_TIME

    assert set(result.payloads) == {
        "profile",
        "income_statements",
        "balance_sheets",
        "cash_flow_statements",
    }

    assert len(requests) == 4

    requests_by_path = {request.url.path: request for request in requests}

    profile_request = requests_by_path["/stable/profile"]

    assert profile_request.url.params["symbol"] == "AAPL"
    assert "period" not in profile_request.url.params
    assert profile_request.headers["apikey"] == "test-api-key"

    statement_paths = {
        "/stable/income-statement",
        "/stable/balance-sheet-statement",
        "/stable/cash-flow-statement",
    }

    for path in statement_paths:
        request = requests_by_path[path]

        assert request.url.params["symbol"] == "AAPL"
        assert request.url.params["period"] == "annual"
        assert request.url.params["limit"] == "3"
        assert request.headers["apikey"] == "test-api-key"


def test_collect_rejects_empty_ticker() -> None:
    collector = FMPFinancialDataCollector("test-key")

    with pytest.raises(
        ValueError,
        match="ticker must not be empty",
    ):
        collector.collect("   ")


def test_collect_rejects_non_positive_annual_limit() -> None:
    collector = FMPFinancialDataCollector("test-key")

    with pytest.raises(
        ValueError,
        match="annual_limit must be greter than zero",
    ):
        collector.collect("AAPL", annual_limit=0)


def test_constructor_rejects_empty_api_key() -> None:
    with pytest.raises(
        ConfigurationError,
        match="FMP API key must not be empty",
    ):
        FMPFinancialDataCollector("   ")


def test_constructor_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_seconds must be greater than zero",
    ):
        FMPFinancialDataCollector(
            "test-key",
            timeout_seconds=0,
        )


def test_collect_translates_rate_limit_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=429,
            json={"error": "Limit reached"},
        )

    collector = FMPFinancialDataCollector(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="rate limit was reached",
    ):
        collector.collect("AAPL")


def test_collect_translates_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    collector = FMPFinancialDataCollector(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
    ):
        collector.collect("AAPL")


def test_collect_rejects_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"not valid JSON",
            headers={"Content-Type": "application/json"},
        )

    collector = FMPFinancialDataCollector(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="returned invalid JSON",
    ):
        collector.collect("AAPL")


def test_collect_rejects_fmp_error_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"Error Message": "Invalid API KEY"},
        )

    collector = FMPFinancialDataCollector(
        "test-key", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
        CollectorError,
        match="Invalid API KEY",
    ):
        collector.collect("AAPL")
