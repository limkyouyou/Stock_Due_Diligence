"""Appication-specific exceptions for Stock DD MAS."""


class StockDDError(Exception):
    """Base exception for expected Stock DD application errors."""


class ResearchDataError(StockDDError):
    """Raised when research data cannot be loaded or validated."""


class ConfigurationError(StockDDError):
    """Raised when required application configuration is invalid or missing."""


class CollectorError(StockDDError):
    """Raised when an external data collector cannot complete its work."""
