"""Application service for SEC filing-evidence ingestion."""

import hashlib
from collections.abc import Callable
from uuid import uuid4

from stock_dd.collectors import CollectedFilingDocument
from stock_dd.exceptions import NormalizationError
from stock_dd.models import (
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
)
from stock_dd.repositories import EvidenceSourceRepository
from stock_dd.storage.raw_filings import StoredRawFilingDocument


def _new_evidence_source_id() -> EvidenceSourceId:
    """Create a new internal evidence-source identifier."""

    return EvidenceSourceId(f"source-{uuid4()}")


class SECFilingEvidenceIngestionService:
    """Promote one stored SEC filing snapshot into trusted evidence."""

    def __init__(
        self,
        evidence_repository: EvidenceSourceRepository,
        *,
        source_id_factory: Callable[[], EvidenceSourceId] = _new_evidence_source_id,
    ) -> None:
        self._evidence_repository = evidence_repository
        self._source_id_factory = source_id_factory

    def ingest(
        self,
        document: CollectedFilingDocument,
        stored_document: StoredRawFilingDocument,
    ) -> EvidenceSource:
        """Create and persist evidence for one stored SEC filing snapshot."""

        self._validate_inputs(
            document,
            stored_document,
        )

        filing = document.request.filing

        source = EvidenceSource(
            source_id=self._source_id_factory(),
            source_type=EvidenceSourceType.REGULATORY_FILING,
            title=f"SEC {filing.form} filing {filing.accession_number}",
            publisher="U.S. Securities and Exchange Commission",
            retrieved_at=document.retrieved_at,
            published_on=filing.filed_on,
            url=document.source_url,
            external_id=filing.accession_number,
            filing_form=filing.form,
            raw_file_path=stored_document.path.as_posix(),
            sha256=stored_document.sha256,
            language="en",
        )

        self._evidence_repository.save(source)

        return source

    @staticmethod
    def _validate_inputs(
        document: CollectedFilingDocument,
        stored_document: StoredRawFilingDocument,
    ) -> None:
        """Ensure collected and stored filing metadata describe the same bytes."""

        if document.provider.lower() != "sec":
            raise NormalizationError(
                "SEC filing-evidence ingestion requires a document collected from SEC."
            )

        expected_url = document.request.filing.primary_document_url

        if expected_url is None or document.source_url != expected_url:
            raise NormalizationError(
                "Collected filing source URL does not match the discovered primary-document URL."
            )

        expected_size = len(document.content)

        if stored_document.size_bytes != expected_size:
            raise NormalizationError(
                "Stored filing size does not match the collected document."
            )

        expected_sha256 = hashlib.sha256(document.content).hexdigest()

        if stored_document.sha256 != expected_sha256:
            raise NormalizationError(
                "Stored filing SHA-256 does not match the collected document."
            )
