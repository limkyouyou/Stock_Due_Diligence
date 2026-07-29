"""Appication-specific exceptions for Stock DD MAS."""


class StockDDError(Exception):
    """Base exception for expected Stock DD application errors."""


class ResearchDataError(StockDDError):
    """Raised when research data cannot be loaded or validated."""