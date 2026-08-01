"""Appication-specific exceptions for Stock DD MAS."""


class StockDDError(Exception):
    """Base exception for expected Stock DD application errors."""


class ResearchDataError(StockDDError):
    """Raised when research data cannot be loaded or validated."""


class ConfigurationError(StockDDError):
    """Raised when required application configuration is invalid or missing."""


class CollectorError(StockDDError):
    """Raised when an external data collector cannot complete its work."""


class RawDataStorageError(StockDDError):
    """Raised when raw provider data cannot be stored safely."""


class NormalizationError(StockDDError):
    """Raised when provider data cannot be normalized safely."""
