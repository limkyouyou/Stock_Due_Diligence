"""Typed identifiers used by Stock DD domain models."""

from typing import NewType

CompanyId = NewType("CompanyId", str)
EvidenceSourceId = NewType("EvidenceSourceId", str)
ExecutiveId = NewType("ExecutiveId", str)
ExecutiveRoleId = NewType("ExecutiveRoleId", str)
CareerPositionId = NewType("CareerPositionId", str)
CandidateEvidenceId = NewType("CandidateEvidenceId", str)
CompanyEventId = NewType("CompanyEventId", str)
