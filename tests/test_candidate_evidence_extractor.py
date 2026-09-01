"""Tests for the candidate-evidence extractor contract."""

from datetime import UTC, date, datetime

import pytest

from stock_dd.extractors import (
    CandidateEvidenceExtractionRequest,
    CandidateEvidenceExtractionResult,
    CandidateEvidenceExtractor,
)
from stock_dd.models import (
    CompanyId,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
)

FIXED_EXTRACTION_TIME = datetime(
    2026,
    9,
    1,
    15,
    0,
    tzinfo=UTC,
)


class StubCandidateEvidenceExtractor:
    """Small implementation used to test the extractor contract."""

    @property
    def extractor_name(self) -> str:
        "Return the extractor name"

        return "stub"

    @property
    def extractor_version(self) -> str:
        """Return the extractor version."""

        return "1.0"

    def extract(
        self,
        request: CandidateEvidenceExtractionRequest,
    ) -> CandidateEvidenceExtractionResult:
        """Return an empty extraction result."""

        return CandidateEvidenceExtractionResult(
            extractor_name=self.extractor_name,
            extractor_version=self.extractor_version,
            extracted_at=FIXED_EXTRACTION_TIME,
            candidates=(),
        )


def _make_source(
    *,
    published_on: date = date(2025, 10, 31),
) -> EvidenceSource:
    return EvidenceSource(
        source_id=EvidenceSourceId("source-test"),
        source_type=EvidenceSourceType.REGULATORY_FILING,
        title="SEC 8-K filing",
        publisher="U.S. Securities and Exchange Commission",
        retrieved_at=datetime(
            2026,
            9,
            1,
            10,
            0,
            tzinfo=UTC,
        ),
        published_on=published_on,
        filing_form="8-K",
    )


def test_candidate_evidence_extractor_accepts_compatible_implementation() -> None:
    extractor = StubCandidateEvidenceExtractor()

    assert isinstance(
        extractor,
        CandidateEvidenceExtractor,
    )


def test_extraction_request_preserves_input() -> None:
    source = _make_source()

    request = CandidateEvidenceExtractionRequest(
        company_id=CompanyId("company-test"),
        source=source,
        content=b"<html>filing</html>",
        as_of_date=date(2026, 9, 1),
    )

    assert request.company_id == CompanyId("company-test")
    assert request.source == source
    assert request.content == b"<html>filing</html>"
    assert request.as_of_date == date(2026, 9, 1)


def test_extractor_can_return_no_candidate() -> None:
    extractor: CandidateEvidenceExtractor = StubCandidateEvidenceExtractor()

    request = CandidateEvidenceExtractionRequest(
        company_id=CompanyId("company-test"),
        source=_make_source(),
        content=b"<html>filing</html>",
        as_of_date=date(2026, 9, 1),
    )

    result = extractor.extract(request)

    assert result == CandidateEvidenceExtractionResult(
        extractor_name="stub",
        extractor_version="1.0",
        extracted_at=FIXED_EXTRACTION_TIME,
        candidates=(),
    )


def test_extraction_request_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        CandidateEvidenceExtractionRequest(
            company_id=CompanyId("company-test"),
            source=_make_source(),
            content=b"",
            as_of_date=date(2026, 9, 1),
        )


def test_extraction_request_rejects_future_source() -> None:
    with pytest.raises(
        ValueError,
        match="publication date must not be after as_of_date",
    ):
        CandidateEvidenceExtractionRequest(
            company_id=CompanyId("company-test"),
            source=_make_source(
                published_on=date(2026, 9, 2),
            ),
            content=b"<html>filing</html>",
            as_of_date=date(2026, 9, 1),
        )


@pytest.mark.parametrize(
    ("name", "version", "message"),
    [
        (
            " ",
            "1.0",
            "extractor_name must not be empty",
        ),
        (
            "stub",
            " ",
            "extractor_version must not be empty",
        ),
    ],
)
def test_extraction_result_rejects_missing_identity(
    name: str,
    version: str,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        CandidateEvidenceExtractionResult(
            extractor_name=name,
            extractor_version=version,
            extracted_at=FIXED_EXTRACTION_TIME,
            candidates=(),
        )
