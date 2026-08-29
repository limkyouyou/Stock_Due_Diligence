"""Discover company filings through the SEC submissions API."""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Final, cast

import httpx

from stock_dd.collectors.filings import (
    DiscoveredFiling,
    FilingDiscoveryDataset,
    FilingDiscoveryRequest,
)
from stock_dd.exceptions import (
    CollectorError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

_SUBMISSIONS_BASE_URL: Final = "https://data.sec.gov/submissions"
_ARCHIVES_BASE_URL: Final = "https://www.sec.gov/Archives/edgar/data"
_DEFAULT_TIMEOUT_SECONDS: Final = 10.0

_ACCESSION_PATTERN: Final = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class _HistoricalSubmissionFile:
    """Metadata for one SEC historical-submissions file."""

    name: str
    filing_from: date
    filing_to: date


class SECFilingDiscoveryCollector:
    """Discover filings using the SEC submissions API."""

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

    def discover(
        self,
        request: FilingDiscoveryRequest,
    ) -> FilingDiscoveryDataset:
        """Discover SEC filings matching the request."""

        logger.info(
            "Discovering SEC filings: cik=%s, forms=%s",
            request.cik,
            request.forms,
        )

        with httpx.Client(
            headers={
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            },
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            payload = self._request_json(
                client,
                (f"{_SUBMISSIONS_BASE_URL}/CIK{request.cik}.json"),
            )

            filings_object = self._require_object(
                payload,
                "filings",
                context="SEC submissions payload",
            )
            recent = self._require_object(
                filings_object,
                "recent",
                context="SEC submissions filings",
            )

            discovered = list(
                self._parse_filing_table(
                    recent,
                    request=request,
                )
            )

            for historical_file in self._parse_historical_files(filings_object):
                if not self._overlaps_request(historical_file, request):
                    continue

                historical_payload = self._request_json(
                    client,
                    f"{_SUBMISSIONS_BASE_URL}/{historical_file.name}",
                )

                discovered.extend(
                    self._parse_filing_table(
                        historical_payload,
                        request=request,
                    )
                )

        discovered.sort(
            key=lambda filing: (
                filing.filed_on,
                filing.accession_number,
            ),
            reverse=True,
        )

        result = FilingDiscoveryDataset(
            provider=self.provider_name,
            request=request,
            collected_at=self._clock(),
            filings=tuple(discovered),
        )

        logger.info(
            "Completed SEC filing discovery: cik=%s, filings=%s",
            request.cik,
            len(result.filings),
        )

        return result

    def _request_json(
        self,
        client: httpx.Client,
        url: str,
    ) -> dict[str, object]:
        """Request one SEC JSON resource."""

        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code

            if status_code == 429:
                message = "SEC rate limit was reached during filing discovery."
            elif status_code == 403:
                message = "SEC access was denied during filing discovery. Check the configured User-Agent."
            else:
                message = f"SEC filing-discovery request failed with HTTP status {status_code}."

            raise CollectorError(message) from error

        except httpx.RequestError as error:
            raise CollectorError(
                f"SEC filing-discovery request failed: {type(error).__name__}."
            ) from error

        try:
            payload: object = response.json()
        except ValueError as error:
            raise CollectorError(
                "SEC returned invalid JSON during filing discovery."
            ) from error

        if not isinstance(payload, dict):
            raise CollectorError(
                "SEC returned an unexpected JSON value during filing discovery."
            )

        return cast(dict[str, object], payload)

    @staticmethod
    def _require_object(
        payload: dict[str, object],
        key: str,
        *,
        context: str,
    ) -> dict[str, object]:
        """Return a required JSON object."""

        value = payload.get(key)

        if not isinstance(value, dict):
            raise CollectorError(f"{context} is missing required object '{key}'.")

        return cast(dict[str, object], value)

    @classmethod
    def _parse_historical_files(
        cls,
        filings_object: dict[str, object],
    ) -> tuple[_HistoricalSubmissionFile, ...]:
        """Parse SEC historical-submission file metadata."""

        raw_files = filings_object.get("files")

        if raw_files is None:
            return ()

        if not isinstance(raw_files, list):
            raise CollectorError(
                "SEC submissions payload contains invalid historical-file metadata."
            )

        historical_files: list[_HistoricalSubmissionFile] = []

        for raw_file in raw_files:
            if not isinstance(raw_file, dict):
                raise CollectorError(
                    "SEC submissions payload contains malformed historical-file metadata."
                )

            file_data = cast(dict[str, object], raw_file)

            name = cls._require_text(
                file_data.get("name"),
                field_name="historical filename",
            )

            if "/" in name or "\\" in name:
                raise CollectorError("SEC historical-submission filename is invalid.")

            filing_from = cls._require_date(
                file_data.get("filingFrom"),
                field_name="historical filingFrom",
            )
            filing_to = cls._require_date(
                file_data.get("filingTo"),
                field_name="historical filingTo",
            )

            if filing_from > filing_to:
                raise CollectorError("SEC historical-submission date range is invalid.")

            historical_files.append(
                _HistoricalSubmissionFile(
                    name=name,
                    filing_from=filing_from,
                    filing_to=filing_to,
                )
            )

        return tuple(historical_files)

    @staticmethod
    def _overlaps_request(
        historical_file: _HistoricalSubmissionFile,
        request: FilingDiscoveryRequest,
    ) -> bool:
        """Return whether a historical file overlaps the request."""

        if historical_file.filing_from > request.as_of_date:
            return False

        if (
            request.filed_from is not None
            and historical_file.filing_to < request.filed_from
        ):
            return False

        return True

    @classmethod
    def _parse_filing_table(
        cls,
        table: dict[str, object],
        *,
        request: FilingDiscoveryRequest,
    ) -> tuple[DiscoveredFiling, ...]:
        """Parse and filter one SEC parallel-array filing table."""

        accessions = cls._require_column(
            table,
            "accessionNumber",
        )
        filing_dates = cls._require_column(
            table,
            "filingDate",
        )
        forms = cls._require_column(
            table,
            "form",
        )

        row_count = len(accessions)

        if len(filing_dates) != row_count or len(forms) != row_count:
            raise CollectorError(
                "SEC filing-discovery columns have inconsistent lengths."
            )

        report_dates = cls._optional_column(
            table,
            "reportDate",
            row_count=row_count,
        )
        acceptance_times = cls._optional_column(
            table,
            "acceptanceDateTime",
            row_count=row_count,
        )
        primary_documents = cls._optional_column(
            table,
            "primaryDocument",
            row_count=row_count,
        )
        items_values = cls._optional_column(
            table,
            "items",
            row_count=row_count,
        )

        discovered: list[DiscoveredFiling] = []

        for index in range(row_count):
            form = cls._require_text(
                forms[index],
                field_name="form",
            ).upper()

            filed_on = cls._require_date(
                filing_dates[index],
                field_name="filingDate",
            )

            if form not in request.forms:
                continue

            if filed_on > request.as_of_date:
                continue

            if request.filed_from is not None and filed_on < request.filed_from:
                continue

            accession_number = cls._require_text(
                accessions[index],
                field_name="accessionNumber",
            )

            if not _ACCESSION_PATTERN.fullmatch(accession_number):
                raise CollectorError(
                    "SEC filing-discovery payload contains an invalid accession number."
                )

            primary_document = cls._optional_text(
                primary_documents[index],
                field_name="primaryDocument",
            )

            filing_index_url, primary_document_url = cls._build_archive_urls(
                cik=request.cik,
                accession_number=accession_number,
                primary_document=primary_document,
            )

            discovered.append(
                DiscoveredFiling(
                    accession_number=accession_number,
                    form=form,
                    filed_on=filed_on,
                    filing_index_url=filing_index_url,
                    report_date=cls._optional_date(
                        report_dates[index],
                        field_name="reportDate",
                    ),
                    accepted_at=cls._optional_datetime(
                        acceptance_times[index],
                    ),
                    primary_document=primary_document,
                    primary_document_url=primary_document_url,
                    items=cls._parse_items(items_values[index]),
                )
            )

        return tuple(discovered)

    @staticmethod
    def _require_column(
        table: dict[str, object],
        field_name: str,
    ) -> list[object]:
        """Return a required parallel-array column."""

        value = table.get(field_name)

        if not isinstance(value, list):
            raise CollectorError(
                f"SEC filing-discovery payload is missing required column '{field_name}'."
            )

        return cast(list[object], value)

    @staticmethod
    def _optional_column(
        table: dict[str, object],
        field_name: str,
        *,
        row_count: int,
    ) -> list[object]:
        """Return an optional parallel-array column."""

        value = table.get(field_name)

        if value is None:
            return [None] * row_count

        if not isinstance(value, list) or len(value) != row_count:
            raise CollectorError(
                f"SEC filing-discovery optional column '{field_name}' has an invalid length."
            )

        return cast(list[object], value)

    @staticmethod
    def _require_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Return a required non-empty string."""

        if not isinstance(value, str) or not value.strip():
            raise CollectorError(
                f"SEC filing-discovery payload contains an invalid {field_name}."
            )

        return value.strip()

    @classmethod
    def _require_date(
        cls,
        value: object,
        *,
        field_name: str,
    ) -> date:
        """Return a required ISO date."""

        text = cls._require_text(
            value,
            field_name=field_name,
        )

        try:
            return date.fromisoformat(text)
        except ValueError as error:
            raise CollectorError(
                f"SEC filing-discovery payload contains an invalid {field_name}."
            ) from error

    @classmethod
    def _optional_date(
        cls,
        value: object,
        *,
        field_name: str,
    ) -> date | None:
        """Return an optional ISO date."""

        if value is None or value == "":
            return None

        return cls._require_date(
            value,
            field_name=field_name,
        )

    @staticmethod
    def _optional_text(
        value: object,
        *,
        field_name: str,
    ) -> str | None:
        """Return an optional non-empty string."""

        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise CollectorError(
                f"SEC filing-discovery payload contains an invalid {field_name}."
            )

        cleaned = value.strip()

        return cleaned or None

    @staticmethod
    def _optional_datetime(
        value: object,
    ) -> datetime | None:
        """Return an optional SEC acceptance date-time."""

        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise CollectorError(
                "SEC filing-discovery payload contains an invalid acceptanceDateTime."
            )

        cleaned = value.strip()

        try:
            if len(cleaned) == 14 and cleaned.isdigit():
                return datetime.strptime(
                    cleaned,
                    "%Y%m%d%H%M%S",
                )

            return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError as error:
            raise CollectorError(
                "SEC filing-discovery payload contains an invalid acceptanceDateTime."
            ) from error

    @staticmethod
    def _parse_items(
        value: object,
    ) -> tuple[str, ...]:
        """Parse SEC comma-separated filing items."""

        if value is None or value == "":
            return ()

        if not isinstance(value, str):
            raise CollectorError(
                "SEC filing-discovery payload contains invalid filing items."
            )

        return tuple(item.strip() for item in value.split(",") if item.strip())

    @staticmethod
    def _build_archive_urls(
        *,
        cik: str,
        accession_number: str,
        primary_document: str | None,
    ) -> tuple[str, str | None]:
        """Build SEC archive URLs for one filing."""

        archive_cik = str(int(cik))
        accession_directory = accession_number.replace(
            "-",
            "",
        )

        directory_url = f"{_ARCHIVES_BASE_URL}/{archive_cik}/{accession_directory}"

        filing_index_url = f"{directory_url}/{accession_number}-index.htm"

        primary_document_url = (
            f"{directory_url}/{primary_document}"
            if primary_document is not None
            else None
        )

        return filing_index_url, primary_document_url
