import logging

import pytest

from stock_dd.logging_config import configure_logging


def test_configure_logging_defaults_to_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Normal mode should hide informational progress logs."""

    configuration: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        configuration.update(kwargs)

    monkeypatch.setattr(
        logging,
        "basicConfig",
        fake_basic_config,
    )

    configure_logging()

    assert configuration["level"] == logging.WARNING
    assert configuration["force"] is True


def test_configure_logging_uses_info_in_verbose_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verbose mode should display informational progress logs."""

    configuration: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        configuration.update(kwargs)

    monkeypatch.setattr(
        logging,
        "basicConfig",
        fake_basic_config,
    )

    configure_logging(verbose=True)

    assert configuration["level"] == logging.INFO
