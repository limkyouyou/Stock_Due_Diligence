"""Collect raw company and financial-statement data from FMP."""

from collections.abc import Callable
from datetime import UTC, datetime
import logging
from typing import Final

import httpx

from stock_dd import __version__
from stock_dd.collectors.base import RawFinancialDataset
from stock_dd.exceptions import CollectorError, ConfigurationError


logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL: Final = "https://financialmodelingprep.com/stable/"
_DEFAULT_TIMEOUT_SECONDS: Final = 10.0

_STATEMENT_ENDPOINTS: Final = {
    "income_statements": "income-statement",
    "balance_sheets": "balance-sheet-statement",
    "cash_flow_statements": "cash-flow-statement",
}


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(UTC)


class FMPFinancialDataCollector:
    """Collect raw financial data from Financial Modeling Prep."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        cleaned_api_key = api_key.strip()

        if not cleaned_api_key:
            raise ConfigurationError("FMP API key must not be empty")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        self._api_key = cleaned_api_key
        self._base_url = f"{base_url.rstrip('/')}/"
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._clock = clock

    @property
    def provider_name(self) -> str:
        """Return FMP's stable internal provider name."""

        return "fmp"

    def collect(
        self,
        ticker: str,
        *,
        annual_limit: int = 5,
    ) -> RawFinancialDataset:
        """Collect raw profile and annual financial-statement data."""

        normalized_ticker = ticker.strip().upper()

        if not normalized_ticker:
            raise ValueError("ticker must not be empty.")

        if annual_limit <= 0:
            raise ValueError("annual_limit must be greter than zero.")

        logger.info(
            "Collecting FMP financial data: ticker=%s, annual_limit=%d",
            normalized_ticker,
            annual_limit,
        )

        with httpx.Client(
            base_url=self._base_url,
            headers={
                "Accept": "application/json",
                "apikey": self._api_key,
                "User-Agent": f"stock-dd/{__version__}",
            },
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            payloads: dict[str, object] = {
                "profile": self._request_json(
                    client,
                    endpoint="profile",
                    params={"symbol": normalized_ticker},
                )
            }

            statement_parameters: dict[str, str | int] = {
                "symbol": normalized_ticker,
                "period": "annual",
                "limit": annual_limit,
            }

            for payload_name, endpoint in _STATEMENT_ENDPOINTS.items():
                payloads[payload_name] = self._request_json(
                    client,
                    endpoint=endpoint,
                    params=statement_parameters,
                )

        collected_at = self._clock()

        logger.info(
            "Completed FMP financial collectioni: ticker=%s",
            normalized_ticker,
        )

        return RawFinancialDataset(
            provider=self.provider_name,
            ticker=normalized_ticker,
            collected_at=collected_at,
            payloads=payloads,
        )

    def _request_json(
        self,
        client: httpx.Client,
        *,
        endpoint: str,
        params: dict[str, str | int],
    ) -> object:
        """Request one FMP endpoint and return its JSON response."""

        try:
            response = client.get(
                endpoint,
                params=params,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise CollectorError(
                self._create_status_error_message(
                    endpoint=endpoint,
                    status_code=error.response.status_code,
                )
            ) from error
        except httpx.RequestError as error:
            raise CollectorError(
                f"FMP request failed for '{endpoint}': {type(error).__name__}."
            ) from error

        try:
            payload: object = response.json()
        except ValueError as error:
            raise CollectorError(
                f"FMP returned invalid JSON for '{endpoint}'."
            ) from error

        if not isinstance(payload, dict | list):
            raise CollectorError(
                f"FMP returned an unexpeced JSON value for '{endpoint}'."
            )

        if isinstance(payload, dict):
            raw_error_message: object = payload.get("Error Message")

            if isinstance(raw_error_message, str) and raw_error_message.strip():
                raise CollectorError(
                    "FMP returns an error for "
                    f"'{endpoint}': {raw_error_message.strip()}"
                )

        return payload

    @staticmethod
    def _create_status_error_message(
        *,
        endpoint: str,
        status_code: int,
    ) -> str:
        """Create a safe message for an unsuccessful HTTP status."""

        if status_code in {401, 403}:
            return f"FMP authentication or authorization failed for '{endpoint}'."

        if status_code == 429:
            return f"FMP rate limit was reached while requesting '{endpoint}'."

        return f"FMP request failed for '{endpoint}' with HTTP status {status_code}."
