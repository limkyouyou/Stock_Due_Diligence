"""Collect raw filing documents from SEC EDGAR archives."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from stock_dd.collectors.filing_documents import (
    CollectedFilingDocument,
    FilingDocumentRequest,
)
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30.0


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(UTC)


class SECFilingDocumentCollector:
    """Collect raw filing documents from SEC EDGAR."""

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

    def collect(
        self,
        request: FilingDocumentRequest,
    ) -> CollectedFilingDocument:
        """Collect the primary document for one SEC filing."""

        source_url = request.filing.primary_document_url

        if source_url is None:
            raise CollectorError(
                "Discovered filing does not provide a primary-document URL."
            )

        self._validate_sec_archive_url(source_url)

        logger.info(
            "Collecting SEC filing document: accession=%s, form=%s",
            request.filing.accession_number,
            request.filing.form,
        )

        with httpx.Client(
            headers={
                "Accept": "*/*",
                "User-Agent": self._user_agent,
            },
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            try:
                response = client.get(source_url)
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                status_code = error.response.status_code

                if status_code == 429:
                    message = (
                        "SEC rate limit was reached during filing-document collection."
                    )
                elif status_code == 403:
                    message = "SEC access was denied during filing-document collection. Check the configured User-Agent."
                else:
                    message = f"SEC filing-document request failed with HTTP status {status_code}."

                raise CollectorError(message) from error

            except httpx.RequestError as error:
                raise CollectorError(
                    f"SEC filing-document request failed: {type(error).__name__}."
                ) from error

        content = response.content

        if not content:
            raise CollectorError("SEC returned an empty filing document.")

        raw_content_type = response.headers.get("Content-Type")
        content_type = (
            raw_content_type.split(";", maxsplit=1)[0].strip().lower()
            if raw_content_type
            else None
        )

        result = CollectedFilingDocument(
            provider=self.provider_name,
            request=request,
            source_url=source_url,
            retrieved_at=self._clock(),
            content=content,
            content_type=content_type,
        )

        logger.info(
            "Completed SEC filing-document collection: accession=%s, bytes=%s",
            request.filing.accession_number,
            len(content),
        )

        return result

    @staticmethod
    def _validate_sec_archive_url(url: str) -> None:
        """Require an HTTPS SEC EDGAR archive URL."""

        parsed = httpx.URL(url)

        if (
            parsed.scheme != "https"
            or parsed.host != "www.sec.gov"
            or not parsed.path.startswith("/Archives/edgar/data/")
        ):
            raise CollectorError(
                "Filing document URL is not a valid SEC EDGAR archive URL."
            )
