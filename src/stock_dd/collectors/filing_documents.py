"""Provider-independent contract for filing-document collectors."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from stock_dd.collectors.filings import DiscoveredFiling


@dataclass(frozen=True, slots=True, kw_only=True)
class FilingDocumentRequest:
    """Request for one discovered filing document."""

    cik: str
    filing: DiscoveredFiling

    def __post_init__(self) -> None:
        normalized_cik = self.cik.strip()

        if (
            not normalized_cik
            or not normalized_cik.isdigit()
            or len(normalized_cik) > 10
        ):
            raise ValueError("cik must contain between 1 and 10 digits.")

        object.__setattr__(
            self,
            "cik",
            normalized_cik.zfill(10),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CollectedFilingDocument:
    """Raw filing document collected from an external provider."""

    provider: str
    request: FilingDocumentRequest
    source_url: str
    retrieved_at: datetime
    content: bytes
    content_type: str | None = None


@runtime_checkable
class FilingDocumentCollector(Protocol):
    """Contract implemented by filing-document provider adapters."""

    @property
    def provider_name(self) -> str:
        """Return the provider's stable internal name."""

        ...

    def collect(
        self,
        request: FilingDocumentRequest,
    ) -> CollectedFilingDocument:
        """Collect one raw filing document."""

        ...
