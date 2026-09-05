"""Structural review assessment for parsed SEC Form 8-K filings."""

from dataclasses import dataclass

from stock_dd.parsers.sec_8k import SEC8KParseResult


@dataclass(frozen=True, slots=True, kw_only=True)
class SEC8KStructuralAssessment:
    """Compare SEC-reported Item codes with structurally parsed Items."""

    expected_item_codes: tuple[str, ...]
    parsed_item_codes: tuple[str, ...]
    missing_item_codes: tuple[str, ...]

    @property
    def requires_review(self) -> bool:
        """Return whether structural parsing requires human review."""

        return not self.parsed_item_codes or bool(self.missing_item_codes)


def assess_sec_8k_structure(
    *,
    expected_item_codes: tuple[str, ...],
    parse_result: SEC8KParseResult,
) -> SEC8KStructuralAssessment:
    """Assess whether an 8-K structural parse requires review."""

    normalized_expected = _unique_item_codes(expected_item_codes)

    parsed_item_codes = _unique_item_codes(
        tuple(section.item_code for section in parse_result.sections)
    )

    parsed_item_code_set = set(parsed_item_codes)

    missing_item_codes = tuple(
        item_code
        for item_code in normalized_expected
        if item_code not in parsed_item_code_set
    )

    return SEC8KStructuralAssessment(
        expected_item_codes=normalized_expected,
        parsed_item_codes=parsed_item_codes,
        missing_item_codes=missing_item_codes,
    )


def _unique_item_codes(
    item_codes: tuple[str, ...],
) -> tuple[str, ...]:
    """Normalize and de-duplicate Item codes while preseving order."""

    normalized: list[str] = []

    for item_code in item_codes:
        stripped = item_code.strip()

        if stripped and stripped not in normalized:
            normalized.append(stripped)

    return tuple(normalized)
