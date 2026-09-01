"""Provider-independent contract for candidate-evidence extractors."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from stock_dd.models import (
    CandidateEvidence,
    CompanyId,
    EvidenceSource,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEvidenceExtractionRequest:
    """Input required to extract candidate evidence from one source."""

    company_id: CompanyId
    source: EvidenceSource
    content: bytes
    as_of_date: date

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("content must not be empty.")

        if (
            self.source.published_on is not None
            and self.source.published_on > self.as_of_date
        ):
            raise ValueError("source publication date must not be after as_of_date.")


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEvidenceExtractionResult:
    """Candidate evidence produced by one extractor run."""

    extractor_name: str
    extractor_version: str
    extracted_at: datetime
    candidates: tuple[CandidateEvidence, ...]

    def __post_init__(self) -> None:
        if not self.extractor_name.strip():
            raise ValueError("extractor_name must not be empty.")

        if not self.extractor_version.strip():
            raise ValueError("extractor_version must not be empty.")


@runtime_checkable
class CandidateEvidenceExtractor(Protocol):
    """Contract implemented by candidate-evidence extractors."""

    @property
    def extractor_name(self) -> str:
        """Return the extractor's stable internal name."""

        ...

    @property
    def extractor_version(self) -> str:
        """Return the extractor implementation version."""

        ...

    def extract(
        self,
        request: CandidateEvidenceExtractionRequest,
    ) -> CandidateEvidenceExtractionResult:
        """Extract candidate evidence from one source."""

        ...
