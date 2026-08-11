"""Repository contracts for company executives."""

from typing import Protocol, runtime_checkable

from stock_dd.models import Executive, ExecutiveId


@runtime_checkable
class ExecutiveRepository(Protocol):
    """Persistence contract for executive identities."""

    def save(self, executive: Executive) -> None:
        """Persist an executive identity."""

        ...

    def get(
        self,
        executive_id: ExecutiveId,
    ) -> Executive | None:
        """Return an executive by their internal identifier."""

        ...
