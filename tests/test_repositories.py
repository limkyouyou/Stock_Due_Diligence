"""Test for Stock DD repository contracts."""

from stock_dd.models import CompanyId, CompanyIdentity
from stock_dd.repositories import CompanyRepository


class InMemoryCompanyRepository:
    """Small repository implementation used to test the contract."""

    def __init__(self) -> None:
        self._companies: dict[CompanyId, CompanyIdentity] = {}

    def save(self, company: CompanyIdentity) -> None:
        """Store a company by its internal identifer."""

        self._companies[company.company_id] = company

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        """Return a stored company by its internal identifier."""

        return self._companies.get(company_id)

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        """return the first stored company with the requested CIK."""

        return next(
            (company for company in self._companies.values() if company.cik == cik),
            None,
        )


def test_company_repository_protocol_accepts_compatble_implementation() -> None:
    respository = InMemoryCompanyRepository()

    assert isinstance(respository, CompanyRepository)


def test_company_repository_supports_idenity_lookup() -> None:
    respository: CompanyRepository = InMemoryCompanyRepository()
    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )

    respository.save(company)

    assert respository.get(company.company_id) == company
    assert respository.find_by_cik("0000320193") == company


def test_company_repository_returns_none_for_missing_company() -> None:
    repository: CompanyRepository = InMemoryCompanyRepository()

    assert repository.get(CompanyId("company-missing")) is None
    assert repository.find_by_cik("0000000000") is None
