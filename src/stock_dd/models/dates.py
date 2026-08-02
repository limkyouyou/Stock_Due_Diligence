"""Date-related value objects used by Stock DD domain models."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class DatePrecision(StrEnum):
    """Precision available for a partially known date."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"


@dataclass(frozen=True, slots=True, kw_only=True)
class PartialDate:
    """A calendar date whose month or day may be unknown."""

    year: int
    month: int | None = None
    day: int | None = None

    def __post_init__(self) -> None:
        """Ensure the supplied date components form a valid partial date."""

        if self.month is None:
            if self.day is not None:
                raise ValueError("month is required when day is provided")

            date(self.year, 1, 1)
            return

        if self.day is None:
            date(self.year, self.month, 1)
            return

        date(self.year, self.month, self.day)

    @property
    def precision(self) -> DatePrecision:
        """Return the precision supported by the available components."""

        if self.month is None:
            return DatePrecision.YEAR

        if self.day is None:
            return DatePrecision.MONTH

        return DatePrecision.DAY
