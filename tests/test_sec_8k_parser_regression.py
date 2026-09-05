"""Regression tests against complete real SEC Form 8-K filings."""

from pathlib import Path

import pytest

from stock_dd.parsers import (
    SEC8KFilingParser,
    SEC8KItemSection,
    SEC8KParseResult,
    SEC8KTerminationReason,
)

FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures" / "sec_8k"

REAL_SEC_FIXTURES = (
    "amazon_0001018724-22-000015.htm",
    "apple_0001181431-12-038301.htm",
    "bbt_0000092230-15-000062.htm",
    "bristol_myers_squibb_0001567619-17-000402.htm",
    "cleco_0001089819-17-000026.htm",
    "keystar_0001493152-24-004441.htm",
    "netapp_0001193125-20-058901.htm",
    "usbc_0001074828-26-000071.htm",
    "cea_industries_inc_0001102624-14-000601.htm",
    "nv_energy_0000741508-12-000033.htm",
    "cannassist_0001021432-18-000205.txt",
)


def _parse_fixture(
    filename: str,
) -> SEC8KParseResult:
    content = (FIXTURE_DIRECTORY / filename).read_bytes()

    return SEC8KFilingParser().parse(content)


def _item_section(
    result: SEC8KParseResult,
    item_code: str,
) -> SEC8KItemSection:
    matching_sections = tuple(
        section for section in result.sections if section.item_code == item_code
    )

    assert len(matching_sections) == 1

    return matching_sections[0]


@pytest.mark.parametrize(
    "filename",
    REAL_SEC_FIXTURES,
)
def test_real_sec_filing_preserves_item_502(
    filename: str,
) -> None:
    result = _parse_fixture(filename)

    item_502 = tuple(
        section for section in result.sections if section.item_code == "5.02"
    )

    assert len(item_502) == 1


@pytest.mark.parametrize(
    "filename",
    REAL_SEC_FIXTURES,
)
def test_real_sec_filing_terminates_at_signature_heading(
    filename: str,
) -> None:
    result = _parse_fixture(filename)

    assert result.termination_reason == SEC8KTerminationReason.SIGNATURE_HEADING


def test_amazon_preserves_navigation_tail_after_item_502() -> None:
    result = _parse_fixture("amazon_0001018724-22-000015.htm")

    section = _item_section(result, "5.02")

    normalized = section.text.casefold()

    assert "david h. clark" in normalized
    assert "table of contents" in normalized


def test_keystar_preserves_irregular_section_9_tail() -> None:
    result = _parse_fixture("keystar_0001493152-24-004441.htm")

    section = _item_section(result, "5.02")

    assert "section 9" in section.text.casefold()


def test_usbc_preserves_forward_looking_tail() -> None:
    result = _parse_fixture("usbc_0001074828-26-000071.htm")

    section = _item_section(result, "5.02")

    assert "forward-looking statements" in section.text.casefold()


def test_netapp_preserves_exhibit_material_before_signature() -> None:
    result = _parse_fixture("netapp_0001193125-20-058901.htm")

    section = _item_section(result, "5.02")

    normalized = section.text.casefold()

    assert "exhibit no." in normalized
    assert "description" in normalized


def test_cleco_amendment_extracts_expected_items() -> None:
    result = _parse_fixture("cleco_0001089819-17-000026.htm")

    item_codes = tuple(section.item_code for section in result.sections)

    assert "5.02" in item_codes
    assert "9.01" in item_codes


def test_cea_legacy_table_layour_detects_real_boundaries() -> None:
    result = _parse_fixture("cea_industries_inc_0001102624-14-000601.htm")

    assert [section.item_code for section in result.sections] == ["5.02", "9.01"]

    item_502 = _item_section(result, "5.02")

    assert "item 9.01" not in item_502.text.casefold()

    assert result.termination_reason == SEC8KTerminationReason.SIGNATURE_HEADING


def test_nv_energy_skips_toc_items_and_preserves_real_item_502() -> None:
    result = _parse_fixture("nv_energy_0000741508-12-000033.htm")

    item_502 = _item_section(result, "5.02")

    normalized = item_502.text.casefold()

    assert "dilek l. samil" in normalized
    assert "jonathan s. halkyard" in normalized

    assert result.termination_reason == SEC8KTerminationReason.SIGNATURE_HEADING


def test_cannassist_plain_text_filing_detects_item_502() -> None:
    result = _parse_fixture("cannassist_0001021432-18-000205.txt")

    assert [section.item_code for section in result.sections] == ["3.02", "5.02"]

    item_502 = _item_section(result, "5.02")

    normalized = item_502.text.casefold()

    assert "james m. cassidy resigned" in normalized
    assert "mark palumbo was named president" in normalized

    assert result.termination_reason == SEC8KTerminationReason.SIGNATURE_HEADING
