"""Provider-independent contract for filing-discovery collectors."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True, kw_only=True)
class FilingDiscoveryRequest:
    """Criteria for discovering company filings."""

    cik: str
    forms: tuple[str, ...]
    as_of_date: date
    filed_from: date | None = None

    def __post_init__(self) -> None:
        normalized_cik = self.cik.strip()

        if (
            not normalized_cik
            or not normalized_cik.isdigit()
            or len(normalized_cik) > 10
        ):
            raise ValueError("cik must contain between 1 and 10 digits.")

        normalized_forms = tuple(form.strip().upper() for form in self.forms)

        if not normalized_forms or any(not form for form in normalized_forms):
            raise ValueError("forms must contain at least one non-empty form.")

        if len(set(normalized_forms)) != len(normalized_forms):
            raise ValueError("forms must not contain duplicates.")

        if self.filed_from is not None and self.filed_from > self.as_of_date:
            raise ValueError("filed_from must not be after as_of_date.")

        object.__setattr__(
            self,
            "cik",
            normalized_cik.zfill(10),
        )
        object.__setattr__(
            self,
            "forms",
            normalized_forms,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DiscoveredFiling:
    """Normalized metadata for one discovered filing."""

    accession_number: str
    form: str
    filed_on: date
    filing_index_url: str
    reported_date: date | None = None
    accepted_at: datetime | None = None
    primary_document: str | None = None
    primary_document_url: str | None = None
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class FilingDiscoveryDataset:
    """Filing metadata collected for one discovery request."""

    provider: str
    request: FilingDiscoveryRequest
    collected_at: datetime
    filings: tuple[DiscoveredFiling, ...]


@runtime_checkable
class FilingDiscoveryCollector(Protocol):
    """Contract implemented by filing-discovery provider adapters."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    def discover(
        self,
        request: FilingDiscoveryRequest,
    ) -> FilingDiscoveryDataset:
        """Discover filings matching the request."""

        ...
