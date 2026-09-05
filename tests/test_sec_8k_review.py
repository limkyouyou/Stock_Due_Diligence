"""Tests for SEC Form 8-K structural review assessment."""

from stock_dd.parsers import (
    SEC8KItemSection,
    SEC8KLogicalBlock,
    SEC8KParseResult,
    SEC8KTerminationReason,
    assess_sec_8k_structure,
)


def _parse_result(
    *item_codes: str,
) -> SEC8KParseResult:
    sections = tuple(
        SEC8KItemSection(
            item_code=item_code,
            blocks=(
                SEC8KLogicalBlock(
                    index=index, text=f"Item {item_code} Example disclosure"
                ),
            ),
        )
        for index, item_code in enumerate(item_codes)
    )

    return SEC8KParseResult(
        sections=sections,
        unrecognized_item_codes=(),
        termination_reason=SEC8KTerminationReason.SIGNATURE_HEADING,
    )


def test_assessment_does_not_require_review_when_all_items_parse() -> None:
    parse_result = _parse_result("5.02", "9.01")

    assessment = assess_sec_8k_structure(
        expected_item_codes=("5.02", "9.01"),
        parse_result=parse_result,
    )

    assert assessment.expected_item_codes == ("5.02", "9.01")

    assert assessment.parsed_item_codes == ("5.02", "9.01")

    assert assessment.missing_item_codes == ()

    assert not assessment.requires_review


def test_assessment_requires_review_when_expected_item_is_missing() -> None:
    parse_result = _parse_result(
        "5.02",
    )

    assessment = assess_sec_8k_structure(
        expected_item_codes=("5.02", "8.01", "9.01"),
        parse_result=parse_result,
    )

    assert assessment.parsed_item_codes == ("5.02",)

    assert assessment.missing_item_codes == ("8.01", "9.01")

    assert assessment.requires_review


def test_assessment_requires_review_when_no_item_parse() -> None:
    parse_result = _parse_result()

    assessment = assess_sec_8k_structure(
        expected_item_codes=("5.02",),
        parse_result=parse_result,
    )

    assert assessment.parsed_item_codes == ()

    assert assessment.missing_item_codes == ("5.02",)

    assert assessment.requires_review


def test_assessment_requires_review_when_no_items_parse_and_none_expected() -> None:
    parse_result = _parse_result()

    assessment = assess_sec_8k_structure(
        expected_item_codes=(),
        parse_result=parse_result,
    )

    assert assessment.expected_item_codes == ()
    assert assessment.parsed_item_codes == ()
    assert assessment.missing_item_codes == ()

    assert assessment.requires_review


def test_assessment_does_not_require_review_when_items_parse_and_none_expected() -> (
    None
):
    parse_result = _parse_result("8.01")

    assessment = assess_sec_8k_structure(
        expected_item_codes=(),
        parse_result=parse_result,
    )

    assert assessment.parsed_item_codes == ("8.01",)

    assert assessment.missing_item_codes == ()

    assert not assessment.requires_review


def test_assessment_is_not_specific_to_item_502() -> None:
    parse_result = _parse_result("1.01", "8.01")

    assessment = assess_sec_8k_structure(
        expected_item_codes=("1.01", "2.02", "8.01"),
        parse_result=parse_result,
    )

    assert assessment.missing_item_codes == ("2.02",)

    assert assessment.requires_review


def test_assessment_normalizes_expected_item_codes() -> None:
    parse_result = _parse_result("5.02", "9.01")

    assessment = assess_sec_8k_structure(
        expected_item_codes=(" 5.02 ", "", "5.02", "  ", "9.01"),
        parse_result=parse_result,
    )

    assert assessment.expected_item_codes == ("5.02", "9.01")

    assert assessment.missing_item_codes == ()

    assert not assessment.requires_review


def test_assessment_de_duplicates_parsed_item_codes() -> None:
    parse_result = _parse_result("5.02", "5.02", "9.01")

    assessment = assess_sec_8k_structure(
        expected_item_codes=("5.02", "9.01"),
        parse_result=parse_result,
    )

    assert assessment.parsed_item_codes == ("5.02", "9.01")

    assert assessment.missing_item_codes == ()

    assert not assessment.requires_review
