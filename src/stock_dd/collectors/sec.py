"""Collect company-identity data from SEC ticker associations."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Final, cast

import httpx

from stock_dd.collectors.company_identity import (
    CollectedCompanyIdentity,
    CompanyIdentityDataset,
)
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

_COMPANY_TICKERS_URL: Final = "https://www.sec.gov/files/company_tickers_exchange.json"
_DEFAULT_TIMEOUT_SECONDS: Final = 10.0
_EXPECTED_FIELDS: Final = (
    "cik",
    "name",
    "ticker",
    "exchange",
)


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(UTC)


class SECCompanyIdentityCollector:
    """Collect company-identity matches from SEC ticker associations."""

    def __init__(
        self,
        user_agent: str,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        cleaned_user_agent = user_agent.strip()

        if not cleaned_user_agent:
            raise ConfigurationError("SEC User-Agent must not be empty.")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        self._user_agent = cleaned_user_agent
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._clock = clock

    @property
    def provider_name(self) -> str:
        """Return SEC's stable internal provider name."""

        return "sec"

    def collect(self, ticker: str) -> CompanyIdentityDataset:
        """Collect SEC company-identity matches for a ticker."""

        normalized_ticker = ticker.strip().upper()

        if not normalized_ticker:
            raise ValueError("ticker must not be empty.")

        logger.info(
            "Collecting SEC company identity: ticker=%s",
            normalized_ticker,
        )

        with httpx.Client(
            headers={
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            },
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            payload = self._request_json(client)

        matches = self._parse_matches(
            payload,
            requested_ticker=normalized_ticker,
        )
        collected_at = self._clock()

        logger.info(
            "Completed SEC company identity collection: ticker=%s, matches=%d",
            normalized_ticker,
            len(matches),
        )

        return CompanyIdentityDataset(
            provider=self.provider_name,
            requested_ticker=normalized_ticker,
            collected_at=collected_at,
            matches=matches,
        )

    def _request_json(
        self,
        client: httpx.Client,
    ) -> dict[str, object]:
        """Request and validate the SEC ticker-association payload."""

        try:
            response = client.get(_COMPANY_TICKERS_URL)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise CollectorError(
                self._create_status_error_message(
                    status_code=error.response.status_code,
                )
            ) from error
        except httpx.RequestError as error:
            raise CollectorError(
                f"SEC company-identity request failed: {type(error).__name__}."
            ) from error

        try:
            payload: object = response.json()
        except ValueError as error:
            raise CollectorError(
                "SEC returned invalid JSON for company identities."
            ) from error

        if not isinstance(payload, dict):
            raise CollectorError(
                "SEC returned an unexpected JSON value for company identities."
            )

        return cast(dict[str, object], payload)

    @classmethod
    def _parse_matches(
        cls,
        payload: dict[str, object],
        *,
        requested_ticker: str,
    ) -> tuple[CollectedCompanyIdentity, ...]:
        """Parse identity rows matching the requested ticker."""

        fields = payload.get("fields")

        if fields != list(_EXPECTED_FIELDS):
            raise CollectorError(
                "SEC company-identity payload has an unexpected field schema."
            )

        rows = payload.get("data")

        if not isinstance(rows, list):
            raise CollectorError(
                "SEC company-identity payload is missing its data rows."
            )

        matches: list[CollectedCompanyIdentity] = []

        for raw_row in rows:
            cik, legal_name, ticker, exchange = cls._parse_row(raw_row)

            if ticker != requested_ticker:
                continue

            matches.append(
                CollectedCompanyIdentity(
                    legal_name=legal_name,
                    cik=f"{cik:010d}",
                    ticker=ticker,
                    exchange=exchange,
                )
            )

        return tuple(matches)

    @staticmethod
    def _parse_row(
        raw_row: object,
    ) -> tuple[int, str, str, str | None]:
        """Validate and normalize one SEC ticker-association row."""

        if not isinstance(raw_row, list) or len(raw_row) != 4:
            raise CollectorError(
                "SEC company-identity payload contains a malformed row."
            )

        raw_cik, raw_name, raw_ticker, raw_exchange = raw_row

        if (
            isinstance(raw_cik, bool)
            or not isinstance(raw_cik, int)
            or raw_cik <= 0
            or raw_cik > 9_999_999_999
        ):
            raise CollectorError(
                "SEC company-identity payload contains an invalid CIK."
            )

        if not isinstance(raw_name, str) or not raw_name.strip():
            raise CollectorError(
                "SEC company-identity payload contains invalid company name."
            )

        if not isinstance(raw_ticker, str) or not raw_ticker.strip():
            raise CollectorError(
                "SEC company-identity payload contains an invalid ticker."
            )

        if raw_exchange is not None and not isinstance(raw_exchange, str):
            raise CollectorError(
                "SEC company-identity payload contains an invalid exchange."
            )

        exchange = (
            raw_exchange.strip() or None if isinstance(raw_exchange, str) else None
        )

        return (
            raw_cik,
            raw_name.strip(),
            raw_ticker.strip().upper(),
            exchange,
        )

    @staticmethod
    def _create_status_error_message(
        *,
        status_code: int,
    ) -> str:
        """Create a safe message for an unsuccessful SEC response."""

        if status_code == 429:
            return "SEC rate limit was reached during company-identity collection."

        if status_code == 403:
            return "SEC access was denied during company-identity collection. Check the configured User-Agent."

        return f"SEC company-identity request failed with HTTP status {status_code}."
