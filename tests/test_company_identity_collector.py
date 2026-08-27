"""Tests for the company-identity collector contract."""

from datetime import UTC, datetime

from stock_dd.collectors import (
    CollectedCompanyIdentity,
    CompanyIdentityCollector,
    CompanyIdentityDataset,
)

FIXED_COLLECTION_TIME = datetime(
    2026,
    8,
    26,
    17,
    30,
    tzinfo=UTC,
)


class StubCompanyIdentityCollector:
    """Small collector implementation used to test the contract."""

    @property
    def provider_name(self) -> str:
        """Return the stub provider name."""

        return "stub"

    def collect(self, ticker: str) -> CompanyIdentityDataset:
        """Return a fixed identity match for AAPL."""

        normalized_ticker = ticker.strip().upper()

        matches = (
            (
                CollectedCompanyIdentity(
                    legal_name="Apple Inc.",
                    cik="0000320193",
                    ticker="AAPL",
                    exchange="Nasdaq",
                ),
            )
            if normalized_ticker == "AAPL"
            else ()
        )

        return CompanyIdentityDataset(
            provider=self.provider_name,
            requested_ticker=normalized_ticker,
            collected_at=FIXED_COLLECTION_TIME,
            matches=matches,
        )


def test_company_identity_collector_accepts_compatible_implementation() -> None:
    collector = StubCompanyIdentityCollector()

    assert isinstance(collector, CompanyIdentityCollector)


def test_company_identity_collector_returns_identity_dataset() -> None:
    collector: CompanyIdentityCollector = StubCompanyIdentityCollector()

    result = collector.collect(" aapl ")

    assert result == CompanyIdentityDataset(
        provider="stub",
        requested_ticker="AAPL",
        collected_at=FIXED_COLLECTION_TIME,
        matches=(
            CollectedCompanyIdentity(
                legal_name="Apple Inc.",
                cik="0000320193",
                ticker="AAPL",
                exchange="Nasdaq",
            ),
        ),
    )


def test_company_identity_collector_can_return_no_matches() -> None:
    collector: CompanyIdentityCollector = StubCompanyIdentityCollector()

    result = collector.collect("UNKNOWN")

    assert result.matches == ()
