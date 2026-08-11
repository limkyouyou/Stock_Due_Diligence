"""Repository contracts for research evidence."""

from typing import Protocol, runtime_checkable

from stock_dd.models import EvidenceSource, EvidenceSourceId, EvidenceSourceType


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
