"""Tests for the SEC company-identity collector."""

from datetime import UTC, datetime

import httpx
import pytest

from stock_dd.collectors import (
    CollectedCompanyIdentity,
    CompanyIdentityCollector,
)
from stock_dd.collectors.sec import SECCompanyIdentityCollector
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

FIXED_COLLECTION_TIME = datetime(2026, 8, 27, 14, 0, tzinfo=UTC)

TEST_USER_AGENT = "Stock DD MAS test@example.com"

VALID_PAYLOAD: dict[str, object] = {
    "fields": [
        "cik",
        "name",
        "ticker",
        "exchange",
    ],
    "data": [
        [
            320193,
            "Apple Inc.",
            "AAPL",
            "Nasdaq",
        ],
    ],
}


def test_sec_collector_satisfies_company_identity_contract() -> None:
    collector = SECCompanyIdentityCollector(TEST_USER_AGENT)

    typed_collector: CompanyIdentityCollector = collector

    assert typed_collector.provider_name == "sec"


def test_collector_returns_matching_sec_identity() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        return httpx.Response(
            status_code=200,
            json=VALID_PAYLOAD,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    result = collector.collect(" aapl ")

    assert result.provider == "sec"
    assert result.requested_ticker == "AAPL"
    assert result.collected_at == FIXED_COLLECTION_TIME
    assert result.matches == (
        CollectedCompanyIdentity(
            legal_name="Apple Inc.",
            cik="0000320193",
            ticker="AAPL",
            exchange="Nasdaq",
        ),
    )

    assert len(requests) == 1

    request = requests[0]

    assert request.url.host == "www.sec.gov"
    assert request.url.path == "/files/company_tickers_exchange.json"
    assert request.headers["User-Agent"] == TEST_USER_AGENT
    assert request.headers["Accept"] == "application/json"


def test_collect_can_return_multiple_matches_and_missing_exchange() -> None:
    payload: dict[str, object] = {
        "fields": [
            "cik",
            "name",
            "ticker",
            "exchange",
        ],
        "data": [
            [
                1,
                "Example One",
                "DUP",
                None,
            ],
            [
                2,
                "Example Two",
                "DUP",
                "NYSE",
            ],
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    result = collector.collect("dup")

    assert result.matches == (
        CollectedCompanyIdentity(
            legal_name="Example One",
            cik="0000000001",
            ticker="DUP",
            exchange=None,
        ),
        CollectedCompanyIdentity(
            legal_name="Example Two",
            cik="0000000002",
            ticker="DUP",
            exchange="NYSE",
        ),
    )


def test_collect_returns_empty_matches_for_unknown_ticker() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=VALID_PAYLOAD,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    result = collector.collect("UNKNOWN")

    assert result.matches == ()


def test_collect_rejects_empty_ticker() -> None:
    collector = SECCompanyIdentityCollector(TEST_USER_AGENT)

    with pytest.raises(
        ValueError,
        match="ticker must not be empty",
    ):
        collector.collect("   ")


def test_constructor_rejects_empty_user_agent() -> None:
    with pytest.raises(
        ConfigurationError,
        match="SEC User-Agent must not be empty",
    ):
        SECCompanyIdentityCollector("   ")


def test_constructor_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_seconds must be greater than zero",
    ):
        SECCompanyIdentityCollector(
            TEST_USER_AGENT,
            timeout_seconds=0,
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (429, "rate limit"),
        (403, "access was denied"),
        (500, "HTTP status 500"),
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

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT, transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
        CollectorError,
        match=message,
    ):
        collector.collect("AAPL")


def test_collect_translates_network_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT, transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
        CollectorError,
        match="SEC company-identity request failed",
    ):
        collector.collect("AAPL")


def test_collect_rejects_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"not valid JSON",
            headers={"Content-Type": "application/json"},
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="returned invalid JSON",
    ):
        collector.collect("AAPL")


def test_collect_rejects_non_object_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[],
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="unexpected JSON value",
    ):
        collector.collect("AAPL")


def test_collect_rejects_unexpected_field_schema() -> None:
    payload: dict[str, object] = {
        "fields": [
            "ticker",
            "name",
        ],
        "data": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="unexpected field schema",
    ):
        collector.collect("AAPL")


def test_collect_rejects_missing_data_rows() -> None:
    payload: dict[str, object] = {
        "fields": [
            "cik",
            "name",
            "ticker",
            "exchange",
        ],
        "data": "not-a-list",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match="missing its data rows",
    ):
        collector.collect("AAPL")


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ([320193, "Apple Inc.", "AAPL"], "malformed row"),
        ([True, "Apple Inc.", "AAPL", "Nasdaq"], "invalid CIK"),
        ([320193, "   ", "AAPL", "Nasdaq"], "invalid company name"),
        ([320193, "Apple Inc.", "   ", "Nasdaq"], "invalid ticker"),
        ([320193, "Apple Inc.", "AAPL", 123], "invalid exchange"),
    ],
)
def test_collect_rejects_invalid_rows(
    row: object,
    message: str,
) -> None:
    payload: dict[str, object] = {
        "fields": [
            "cik",
            "name",
            "ticker",
            "exchange",
        ],
        "data": [row],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=payload,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        CollectorError,
        match=message,
    ):
        collector.collect("AAPL")
