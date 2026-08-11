"""Persistence contracts for Stock DD MAS domain data."""

from stock_dd.repositories.company import CompanyRepository as CompanyRepository
from stock_dd.repositories.evidence import (
    CandidateEvidenceRepository as CandidateEvidenceRepository,
)
from stock_dd.repositories.evidence import (
    EvidenceSourceRepository as EvidenceSourceRepository,
)
from stock_dd.repositories.listing import (
    CompanyListingRepository as CompanyListingRepository,
)
