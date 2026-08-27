"""Provider-independent contract for company-identity collectors."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True, kw_only=True)
class CollectedCompanyIdentity:
    """Company identity information collected from an external provider."""

    legal_name: str
    cik: str
    ticker: str
    exchange: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class CompanyIdentityDataset:
    """Company-identity data collected for one requested ticker."""

    provider: str
    requested_ticker: str
    collected_at: datetime
    matches: tuple[CollectedCompanyIdentity, ...]


@runtime_checkable
class CompanyIdentityCollector(Protocol):
    """Contract implemented by company-identity provider adapters."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    def collect(self, ticker: str) -> CompanyIdentityDataset:
        """Collect company-identity matches for a ticker."""

        ...
