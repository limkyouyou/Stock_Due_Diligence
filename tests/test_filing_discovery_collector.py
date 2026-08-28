"""Tests for the filing-discovery collector contract."""

from datetime import UTC, date, datetime

import pytest

from stock_dd.collectors import (
    DiscoveredFiling,
    FilingDiscoveryCollector,
    FilingDiscoveryDataset,
    FilingDiscoveryRequest,
)

FIXED_COLLECTION_TIME = datetime(2026, 8, 28, 15, 0, tzinfo=UTC)


class StubFilingDiscoveryCollector:
    """Small filing-discovery implementation used to test the contract."""

    @property
    def provider_name(self) -> str:
        """Return the stub provider name."""

        return "stub"

    def discover(
        self,
        request: FilingDiscoveryRequest,
    ) -> FilingDiscoveryDataset:
        """Return fixed filing metadata for the test company."""

        filings = (
            (
                DiscoveredFiling(
                    accession_number="0000320193-25-000079",
                    form="10-K",
                    filed_on=date(2025, 10, 31),
                    reported_date=date(2025, 9, 27),
                    accepted_at=datetime(2025, 10, 31, 6, 1, tzinfo=UTC),
                    primary_document="aapl-20250927.htm",
                    filing_index_url="https://example.com/0000320193-25-000079",
                    primary_document_url="https://example.com/aapl-20250927.htm",
                ),
            )
            if request.cik == "0000320193"
            else ()
        )

        return FilingDiscoveryDataset(
            provider=self.provider_name,
            request=request,
            collected_at=FIXED_COLLECTION_TIME,
            filings=filings,
        )


def test_filing_discovery_collector_accepts_compatible_implementation() -> None:
    collector = StubFilingDiscoveryCollector()

    assert isinstance(
        collector,
        FilingDiscoveryCollector,
    )


def test_filing_discovery_request_normalizes_input() -> None:
    request = FilingDiscoveryRequest(
        cik=" 320193 ",
        forms=(
            " def 14a ",
            "10-k",
            "8-k",
        ),
        filed_from=date(2021, 1, 1),
        as_of_date=date(2026, 8, 28),
    )

    assert request.cik == "0000320193"
    assert request.forms == (
        "DEF 14A",
        "10-K",
        "8-K",
    )


def test_filing_discovery_collector_returns_dataset() -> None:
    collector: FilingDiscoveryCollector = StubFilingDiscoveryCollector()

    request = FilingDiscoveryRequest(
        cik="0000320193",
        forms=(
            "DEF 14A",
            "10-K",
            "8-K",
        ),
        filed_from=date(2021, 1, 1),
        as_of_date=date(2026, 8, 28),
    )

    result = collector.discover(request)

    assert result.provider == "stub"
    assert result.request == request
    assert result.collected_at == FIXED_COLLECTION_TIME
    assert result.filings == (
        DiscoveredFiling(
            accession_number="0000320193-25-000079",
            form="10-K",
            filed_on=date(2025, 10, 31),
            reported_date=date(2025, 9, 27),
            accepted_at=datetime(
                2025,
                10,
                31,
                6,
                1,
                tzinfo=UTC,
            ),
            primary_document="aapl-20250927.htm",
            filing_index_url="https://example.com/0000320193-25-000079",
            primary_document_url="https://example.com/aapl-20250927.htm",
        ),
    )


def test_filing_discovery_collector_can_return_no_filings() -> None:
    collector: FilingDiscoveryCollector = StubFilingDiscoveryCollector()

    request = FilingDiscoveryRequest(
        cik="1",
        forms=("10-K",),
        as_of_date=date(2026, 8, 28),
    )

    result = collector.discover(request)

    assert result.filings == ()


@pytest.mark.parametrize(
    "cik",
    [
        "",
        "   ",
        "not-a-cik",
        "12345678901",
    ],
)
def test_filing_discovery_request_rejects_invalid_cik(
    cik: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="cik must contain",
    ):
        FilingDiscoveryRequest(
            cik=cik,
            forms=("10-K",),
            as_of_date=date(2026, 8, 28),
        )


@pytest.mark.parametrize(
    "forms",
    [
        (),
        ("",),
        ("   ",),
    ],
)
def test_filing_discovery_request_rejects_missing_forms(
    forms: tuple[str, ...],
) -> None:
    with pytest.raises(
        ValueError,
        match="forms must contain",
    ):
        FilingDiscoveryRequest(
            cik="0000320193",
            forms=forms,
            as_of_date=date(2026, 8, 28),
        )


def test_filing_discovery_request_rejects_duplicate_forms() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        FilingDiscoveryRequest(
            cik="0000320193",
            forms=(
                "10-K",
                "10-K",
            ),
            as_of_date=date(2026, 8, 28),
        )


def test_filing_discovery_request_rejects_inverted_date_range() -> None:
    with pytest.raises(
        ValueError,
        match="filed_from must not be after as_of_date",
    ):
        FilingDiscoveryRequest(
            cik="0000320193",
            forms=("10-K",),
            filed_from=date(2026, 9, 1),
            as_of_date=date(2026, 8, 28),
        )
