"""Tests for deterministic SEC Form 8-K structural parsing."""

import pytest

from stock_dd.parsers import (
    SEC8KFilingParser,
    SEC8KItemSection,
    SEC8KLogicalBlock,
    SEC8KParseResult,
)


def _parse(
    html: str,
) -> SEC8KParseResult:
    return SEC8KFilingParser().parse(html.encode())


def test_parse_extracts_multiple_items_and_stops_at_signature() -> None:
    result = _parse(
        """
        <p>cover</p>
        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>Item 9.01 Financial Statements and Exhibits</p>
        <p>(d) Exhibits</p>
        <p>99.1 Press release.</p>
        <p>SIGNATURES</p>
        <p>
          Pursuant to the requirements of the Securities
          Exchange Act of 1934, the registrant has duly
          caused this report to be signed on its behalf
          by the undersigned hereunto duly authorized.
        </p>
        """
    )

    assert [section.item_code for section in result.sections] == [
        "5.02",
        "9.01",
    ]

    assert result.sections[0].text == "Item 5.02 Departure of Directors\nJohn resigned."

    assert (
        result.sections[1].text
        == "Item 9.01 Financial Statements and Exhibits\n(d) Exhibits\n99.1 Press release."
    )


def test_parse_keeps_same_item_subsection_in_one_section() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors</p>
        <p>(b)</p>
        <p>John retired.</p>
        <p>
          Item 5.02(c) Appointment of Certain Officers
        </p>
        <p>Jane was appointed CFO.</p>
        <p>
          Item 9.01 Financial Statements and Exhibits
        </p>
        <p>99.1 Press release.</p>
        """
    )

    assert len(result.sections) == 2

    section = result.sections[0]

    assert section.item_code == "5.02"
    assert "Item 5.02(c)" in section.text
    assert "Jane was appointed CFO." in section.text


def test_parse_accepts_no_space_after_item_code() -> None:
    result = _parse(
        """
        <p>
          Item 5.02Departure of Directors or Principal Officers
        </p>
        <p>Joseph Gebbia was appointed to the Board.</p>
        <p>
          Item 9.01Financial Statements and Exhibits.
        </p>
        <p>99.1 Blog Post.</p>
        """
    )

    assert [section.item_code for section in result.sections] == [
        "5.02",
        "9.01",
    ]


def test_parse_accepts_parenthesized_item_heading() -> None:
    result = _parse(
        """
        <p>
          Item 5.02(d) Departure of Directors
          or Certain Officers
        </p>
        <p>Linda Bammann was elected as a director.</p>
        <p>
          Item 5.03 Amendments to Articles
          of Incorporation or Bylaws
        </p>
        <p>The bylaws were amended.</p>
        """
    )

    assert [section.item_code for section in result.sections] == [
        "5.02",
        "5.03",
    ]


def test_parse_stops_at_spaced_signature_heading() -> None:
    result = _parse(
        """
        <p>Item 5.02 Compensatory Arrangements</p>
        <p>
          The committee adopted an incentive program.
        </p>
        <p>S I G N A T U R E</p>
        <p>BB&amp;T CORPORATION</p>
        """
    )

    assert len(result.sections) == 1
    assert result.sections[0].text.endswith(
        "The committee adopted an incentive program."
    )
    assert "BB&T CORPORATION" not in result.sections[0].text


def test_parse_uses_signature_boilerplate_as_fallback() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors</p>
        <p>A director resigned.</p>
        <p>
          Under the requirements of the Securities Exchange
          Act of 1934, the registrant has caused this report
          to be signed on its behalf by the authorized
          undersigned.
        </p>
        <p>PFIZER INC.</p>
        """
    )

    assert len(result.sections) == 1
    assert "PFIZER INC." not in result.sections[0].text


def test_parse_does_not_treat_narrative_item_reference_as_heading() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors</p>
        <p>
          As previously disclosed under Item 9.01,
          an exhibit was filed.
        </p>
        <p>The officer resigned.</p>
        <p>SIGNATURE</p>
        """
    )

    assert len(result.sections) == 1
    assert result.sections[0].item_code == "5.02"
    assert "Item 9.01" in result.sections[0].text


def test_parse_discards_non_substantive_toc_item_runs() -> None:
    result = _parse(
        """
        <p>TABLE OF CONTENTS</p>
        <p>Item 5.02 Departure of Directors</p>
        <p>Item 9.01 Financial Statements and Exhibits</p>
        <p>2</p>

        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>Item 9.01 Financial Statements and Exhibits</p>
        <p>99.1 Press release.</p>
        <p>SIGNATURES</p>
        """
    )

    assert [section.item_code for section in result.sections] == [
        "5.02",
        "9.01",
    ]

    assert result.sections[0].blocks[0].block_id == "B0004"


def test_parse_preserves_table_row_as_one_logical_block() -> None:
    result = _parse(
        """
        <p>
          Item 9.01 Financial Statements and Exhibits
        </p>
        <table>
          <tr>
            <td>99.1</td>
            <td>Press Release</td>
          </tr>
        </table>
        <p>SIGNATURE</p>
        """
    )

    assert (
        result.sections[0].text
        == "Item 9.01 Financial Statements and Exhibits\n99.1 Press Release"
    )


def test_parse_ignores_non_content_html() -> None:
    result = _parse(
        """
        <style>
          Item 9.01 Fake style content
        </style>
        <script>
          Item 8.01 Fake script content
        </script>

        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>SIGNATURE</p>
        """
    )

    assert [section.item_code for section in result.sections] == ["5.02"]


def test_parse_rejects_empty_content() -> None:
    parser = SEC8KFilingParser()

    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        parser.parse(b"")


def test_parse_does_not_stop_at_toc_signature_entry() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors 3</p>
        <p>
          Item 9.01 Financial Statements and Exhibits 3
        </p>
        <p>SIGNATURES 4</p>
        <p>Table of Contents</p>

        <p>Item 5.02 Departure of Directors</p>
        <p>David Clark resigned.</p>

        <p>
          Item 9.01 Financial Statements and Exhibits
        </p>
        <p>99.1 Press release.</p>
        <p>SIGNATURES</p>
        """
    )

    assert [
        (
            section.item_code,
            section.blocks[0].block_id,
            section.blocks[-1].block_id,
        )
        for section in result.sections
    ] == [
        (
            "5.02",
            "B0004",
            "B0005",
        ),
        (
            "9.01",
            "B0006",
            "B0007",
        ),
    ]


def test_parse_recognizes_item_9_01() -> None:
    result = _parse(
        """
        <p>
          Item 9.01 Financial Statements and Exhibits
        </p>
        <p>99.1 Press release.</p>
        """
    )

    assert [section.item_code for section in result.sections] == ["9.01"]


def test_unrecognized_item_does_not_end_recognized_section() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>
          Item 12.34 Not a current Form 8-K Item
        </p>
        <p>
          This remains in the structurally open
          Item 5.02 section.
        </p>
        <p>
          Item 9.01 Financial Statements and Exhibits
        </p>
        <p>99.1 Press release.</p>
        """
    )

    assert [section.item_code for section in result.sections] == ["5.02", "9.01"]

    assert "Item 12.34" in result.sections[0].text


def test_parse_reports_unrecognized_item_codes_once() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>Item 12.34 Future or invalid item.</p>
        <p>Item 12.34 Repeated.</p>
        """
    )

    assert result.unrecognized_item_codes == ("12.34",)


def test_parse_preserves_unnumbered_tail_material() -> None:
    result = _parse(
        """
        <p>Item 5.02 Departure of Certain Officers</p>
        <p>Jane Smith resigned as CFO.</p>

        <p>Forward-Looking Statements</p>
        <p>
          These statements involve risks and uncertainties.
        </p>

        <p>
          SECTION 9 - FINANCIAL STATEMENTS AND EXHIBITS
        </p>

        <p>SIGNATURE</p>
        """
    )

    assert len(result.sections) == 1

    section = result.sections[0]

    assert section.item_code == "5.02"
    assert "Forward-Looking Statements" in section.text
    assert "SECTION 9" in section.text


def test_parse_can_return_no_recognized_items() -> None:
    result = _parse(
        """
        <p>Cover page</p>
        <p>Some unrelated filing text.</p>
        <p>SIGNATURES</p>
        """
    )

    assert result.sections == ()
    assert result.unrecognized_item_codes == ()


def test_logical_block_validates_index() -> None:
    with pytest.raises(
        ValueError,
        match="index must not be negative",
    ):
        SEC8KLogicalBlock(
            index=-1,
            text="example",
        )


def test_logical_block_validates_text() -> None:
    with pytest.raises(
        ValueError,
        match="text must not be empty",
    ):
        SEC8KLogicalBlock(
            index=0,
            text="  ",
        )


def test_item_sectino_requires_item_code() -> None:
    block = SEC8KLogicalBlock(
        index=0,
        text="example",
    )

    with pytest.raises(
        ValueError,
        match="item_code must not be empty",
    ):
        SEC8KItemSection(
            item_code=" ",
            blocks=(block,),
        )


def test_item_section_requires_blocks() -> None:
    with pytest.raises(
        ValueError,
        match="blocks must not be empty",
    ):
        SEC8KItemSection(
            item_code="5.02",
            blocks=(),
        )


def test_parse_ignores_noscript_content() -> None:
    result = _parse(
        """
        <noscript>
          Item 9.01 Fake noscript content.
        </noscript>

        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>
        <p>SIGNATURE</p>
        """
    )

    assert [section.item_code for section in result.sections] == ["5.02"]


def test_parse_discards_toc_item_with_page_number_only() -> None:
    result = _parse(
        """
        <p>TABLE OF CONTENTS</p>

        <p>Item 5.02 Departure of Directors</p>
        <p>3</p>

        <p>Item 9.01 Financial Statements and Exhibits</p>
        <p>4</p>

        <p>Item 5.02 Departure of Directors</p>
        <p>John resigned.</p>

        <p>Item 9.01 Financial Statements and Exhibits</p>
        <p>99.1 Press release.</p>

        <p>SIGNATURES</p>
        """
    )

    assert [section.item_code for section in result.sections] == ["5.02", "9.01"]

    assert result.sections[0].text == "Item 5.02 Departure of Directors\nJohn resigned."
