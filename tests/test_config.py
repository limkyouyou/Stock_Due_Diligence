"""Tests for application configuration."""

from pathlib import Path

import pytest

from stock_dd.config import Settings, load_settings
from stock_dd.exceptions import ConfigurationError

API_KEY_VARIABLE = "STOCK_DD_FINANCIAL_API_KEY"
RAW_DIRECTORY_VARIABLE = "STOCK_DD_RAW_DATA_DIR"
DATABASE_PATH_VARIABLE = "STOCK_DD_DATABASE_PATH"


def test_load_settings_reads_dotenv_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    monkeypatch.delenv(RAW_DIRECTORY_VARIABLE, raising=False)
    monkeypatch.delenv(
        DATABASE_PATH_VARIABLE,
        raising=False,
    )

    env_file = tmp_path / ".env"
    env_file.write_text(
        (
            "STOCK_DD_FINANCIAL_API_KEY=test-api-key\nSTOCK_DD_RAW_DATA_DIR=custom/raw\nSTOCK_DD_DATABASE_PATH=custom/stock_dd.sqlite3\n"
        ),
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file)

    assert settings.financial_api_key == "test-api-key"
    assert settings.raw_data_directory == Path("custom/raw")
    assert settings.database_path == Path("custom/stock_dd.sqlite3")


def test_environment_variables_overrider_dotenv_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "STOCK_DD_FINANCIAL_API_KEY=file-key\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(API_KEY_VARIABLE, "environment-key")

    settings = load_settings(env_file=env_file)

    assert settings.financial_api_key == "environment-key"


def test_load_settings_uses_default_storage_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    monkeypatch.delenv(RAW_DIRECTORY_VARIABLE, raising=False)
    monkeypatch.delenv(DATABASE_PATH_VARIABLE, raising=False)

    settings = load_settings(env_file=None)

    assert settings.financial_api_key is None
    assert settings.raw_data_directory == Path("data/raw")
    assert settings.database_path == Path("data/stock_dd.sqlite3")


def test_blank_api_key_is_treated_as_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(API_KEY_VARIABLE, "  ")

    settings = load_settings(env_file=None)

    assert settings.financial_api_key is None


def test_require_financial_api_key_returns_key() -> None:
    settings = Settings(
        financial_api_key="test-key",
        raw_data_directory=Path("data/raw"),
        database_path=Path("data/stock_dd.sqlite3"),
    )

    assert settings.require_financial_api_key() == "test-key"


def test_require_financial_api_key_raises_when_missing() -> None:
    settings = Settings(
        financial_api_key=None,
        raw_data_directory=Path("data/raw"),
        database_path=Path("data/stock_dd.sqlite3"),
    )

    with pytest.raises(
        ConfigurationError,
        match="STOCK_DD_FINANCIAL_API_KEY",
    ):
        settings.require_financial_api_key()


def test_settings_repr_does_not_expose_api_key() -> None:
    settings = Settings(
        financial_api_key="secret-value",
        raw_data_directory=Path("data/raw"),
        database_path=Path("data/stock_dd.sqlite3"),
    )

    assert "secret-value" not in repr(settings)


def test_blank_database_path_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DATABASE_PATH_VARIABLE,
        "   ",
    )

    settings = load_settings(env_file=None)

    assert settings.database_path == Path("data/stock_dd.sqlite3")
