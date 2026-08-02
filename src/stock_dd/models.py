"""Domain models for stock due-dilligence research data."""

from dataclasses import dataclass
from datetime import date
from typing import NewType

CompanyId = NewType("CompanyId", str)


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


@dataclass(frozen=True, slots=True)
class ResearchMetadata:
    """Metadata describing the research dataset."""

    as_of_date: date
    currency: str
    source: str


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    """Description profile information for a company."""

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
    """Complete normalized reserach input for one company."""

    metadata: ResearchMetadata
    company: CompanyProfile
    annual_financials: tuple[AnnualFinancial, ...]
