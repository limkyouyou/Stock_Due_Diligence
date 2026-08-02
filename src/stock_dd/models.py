"""Domain models for Stock DD MAS research data."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import NewType

CompanyId = NewType("CompanyId", str)
EvidenceSourceId = NewType("EvidenceSourceId", str)


class EvidenceSourceType(StrEnum):
    """Supported categories of management-research evidence."""

    REGULATORY_FILING = "regulatory_filing"
    REGULATOR_DATA = "regulator_data"
    COMPANY_DOCUMENT = "company_document"
    COMPANY_WEBPAGE = "company_webpage"
    NEWS_ARTICLE = "news_article"
    INTERVIEW = "interview"
    PROFESSIONAL_PROFILE = "professional_profile"
    DISCOVERY_SOURCE = "discovery_source"
    OTHER = "other"


@dataclass(frozen=True, slots=True, kw_only=True)
class CompanyIdentity:
    """Stable identifying information for a legal company."""

    company_id: CompanyId
    legal_name: str
    cik: str
    is_active: bool = True
    alternate_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class CompanyListing:
    """A publicly traded security listing associated with a company."""

    company_id: CompanyId
    ticker: str
    exchange: str
    security_name: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceSource:
    """An external document or webpage used as research evidence."""

    source_id: EvidenceSourceId
    source_type: EvidenceSourceType
    title: str
    publisher: str
    retrieved_at: datetime
    published_on: date | None = None
    url: str | None = None
    external_id: str | None = None
    filing_form: str | None = None
    raw_file_path: str | None = None
    sha256: str | None = None
    language: str = "en"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceCitation:
    """A location within an evidence source supporting a research fact."""

    source_id: EvidenceSourceId
    supporting_excerpt: str | None = None
    location: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchMetadata:
    """Metadata describing the research dataset."""

    as_of_date: date
    currency: str
    source: str


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    """Descriptive profile information for a company."""

    ticker: str
    name: str
    sector: str
    industry: str
    description: str


@dataclass(frozen=True, slots=True)
class AnnualFinancial:
    """Financial results for one fiscal year."""

    fiscal_year: int
    revenue: int
    operating_income: int
    net_income: int
    cash_and_equivalents: int
    total_debt: int
    operating_cash_flow: int
    capital_expenditures: int


@dataclass(frozen=True, slots=True)
class CompanyResearchData:
    """Complete normalized research input for one company."""

    metadata: ResearchMetadata
    company: CompanyProfile
    annual_financials: tuple[AnnualFinancial, ...]
