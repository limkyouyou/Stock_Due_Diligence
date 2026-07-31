"""Load and validate configuration for Stock DD MAS."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

from stock_dd.exceptions import ConfigurationError

_FINANCIAL_API_KEY = "STOCK_DD_FINANCIAL_API_KEY"
_RAW_DATA_DIRECTORY = "STOCK_DD_RAW_DATA_DIR"


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from the environment."""

    financial_api_key: str | None = field(repr=False)
    raw_data_directory: Path

    def require_financial_api_key(self) -> str:
        """Return the financial API key or raise a configurationi error."""

        if self.financial_api_key is None:
            raise ConfigurationError(
                f"Required environment variable "
                f"'{_FINANCIAL_API_KEY}' is missing or empty."
            )

        return self.financial_api_key


def load_settings(
    *,
    env_file: str | Path | None = ".env",
) -> Settings:
    """
    Load settings from a dotenv file and environment variables.

    Real environment variables take priority over values read from the dotenv file.
    """

    values: dict[str, str | None] = {}

    if env_file is not None:
        dotenv_path = Path(env_file)

        if dotenv_path.is_file():
            values.update(dotenv_values(dotenv_path))

    values.update(os.environ)

    raw_data_directory = _clean_optional(values.get(_RAW_DATA_DIRECTORY)) or "data/raw"

    return Settings(
        financial_api_key=_clean_optional(values.get(_FINANCIAL_API_KEY)),
        raw_data_directory=Path(raw_data_directory),
    )


def _clean_optional(value: str | None) -> str | None:
    """Strip an optional string and convert empty values to None."""

    if value is None:
        return None

    cleaned_value = value.strip()

    if not cleaned_value:
        return None

    return cleaned_value
