"""Provider-independent contracts for financial-data collectors."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RawFinancialDataset:
    """Raw financial data retrieved from one external provider."""

    provider: str
    ticker: str
    collected_at: datetime
    payloads: Mapping[str, object]


@runtime_checkable
class FinancialDataCollector(Protocol):
    """Contract implemented by financial-data provider adapters."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    def collect(
        self,
        ticker: str,
        *,
        annual_limit: int = 5,
    ) -> RawFinancialDataset:
        """Collect raw company and annual financial data."""

        ...
