"""Domain models for stock due-dilligence research data."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ResearchMetadata:
    """Metadata describing the research dataset."""

    as_of_date: date
    currency: str
    source: str


@dataclass(frozen=True, slots=True)
class Company:
    """Basic identifying informationi about a company."""

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
    company: Company
    annual_financials: tuple[AnnualFinancial, ...]
