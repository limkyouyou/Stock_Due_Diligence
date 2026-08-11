"""Repository contracts for research evidence."""

from typing import Protocol, runtime_checkable

from stock_dd.models import (
    CandidateEvidence,
    CandidateEvidenceId,
    CompanyId,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
    ExecutiveId,
    VerificationStatus,
)


@runtime_checkable
class EvidenceSourceRepository(Protocol):
    """Persistence contract for external research sources."""

    def save(self, source: EvidenceSource) -> None:
        """Persist an evidence source."""

        ...

    def get(
        self,
        source_id: EvidenceSourceId,
    ) -> EvidenceSource | None:
        """Return an evidence source by its internal identifier."""

        ...

    def find_by_external_id(
        self,
        external_id: str,
        *,
        source_type: EvidenceSourceType | None = None,
    ) -> tuple[EvidenceSource, ...]:
        """Return sources matching an external identifier."""

        ...


@runtime_checkable
class CandidateEvidenceRepository(Protocol):
    """Persistence contract for unverified research claims."""

    def save(safe, candidate: CandidateEvidence) -> None:
        """Persist a candidate evidence record."""

        ...

    def get(
        self,
        candidate_id: CandidateEvidenceId,
    ) -> CandidateEvidence | None:
        """Return candidate evidence by its internal identifier."""

        ...

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence associated with a company."""

        ...

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence associated with an executive."""

        ...

    def find_by_status(
        self,
        verification_status: VerificationStatus,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence with a verification status."""

        ...
