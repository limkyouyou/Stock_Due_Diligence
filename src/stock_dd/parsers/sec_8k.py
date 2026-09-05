"""Deterministic structural parsing of SEC form 8-K filings."""

import re
from dataclasses import dataclass
from enum import StrEnum
from html.parser import HTMLParser

_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "dd",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "ul",
    }
)

_SKIP_TAGS = frozenset(
    {
        "script",
        "style",
        "noscript",
    }
)

_CELL_TAGS = frozenset(
    {
        "td",
        "th",
    }
)

_ROW_BLOCK_TAGS = frozenset(
    {
        "hr",
        "p",
    }
)

_ITEM_HEADING_PATTERN = re.compile(
    r"^item\s*(?P<item_code>\d+\.\d{2})(?!\d)",
    re.IGNORECASE,
)

_PAGE_MARKER_PATTERN = re.compile(r"^(?:\d+|-\d+-)$")

_NAVIGATION_ARTIFACT_PATTERN = re.compile(
    r"^TABLE\s+OF\s+CONTENTS$",
    re.IGNORECASE,
)

_SECTION_HEADING_PATTERN = re.compile(
    r"^SECTION\s+\d+\b",
    re.IGNORECASE,
)

_STANDALONE_SUBSECTION_PATTERN = re.compile(
    r"^\([a-z]\)$",
    re.IGNORECASE,
)

_TRAILING_PAGE_MARKER_PATTERN = re.compile(r"\s+(?:\d{1,3}|-\d{1,3}-)$")

_HTML_STRUCTURE_PATTERN = re.compile(
    r"<\s*(?:div|p|tr|td|th|br|h[1-6]|li|section|article)\b",
    re.IGNORECASE,
)

_TEXT_PAYLOAD_PATTERN = re.compile(
    r"<TEXT>\s*(?P<payload>.*?)\s*</TEXT>",
    re.IGNORECASE | re.DOTALL,
)

_BLANK_LINE_PATTERN = re.compile(r"\n[ \t]*\n+")

_FORM_8K_ITEM_CODES = frozenset(
    {
        "1.01",
        "1.02",
        "1.03",
        "1.04",
        "1.05",
        "2.01",
        "2.02",
        "2.03",
        "2.04",
        "2.05",
        "2.06",
        "3.01",
        "3.02",
        "3.03",
        "4.01",
        "4.02",
        "5.01",
        "5.02",
        "5.03",
        "5.04",
        "5.05",
        "5.06",
        "5.07",
        "5.08",
        "6.01",
        "6.02",
        "6.03",
        "6.04",
        "6.05",
        "6.06",
        "7.01",
        "8.01",
        "9.01",
    }
)


def _normalize_whitespace(value: str) -> str:
    """Collapse repeated whitespace into single spaces."""

    return " ".join(value.split())


@dataclass(frozen=True, slots=True, kw_only=True)
class SEC8KLogicalBlock:
    """One temporary ordered text block derived from filing content."""

    index: int
    text: str

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index must not be negative.")

        if not self.text.strip():
            raise ValueError("text must not be empty.")

    @property
    def block_id(self) -> str:
        """Return the temporary evidence address for this parse."""

        return f"B{self.index:04d}"


@dataclass(frozen=True, slots=True, kw_only=True)
class SEC8KItemSection:
    """One structurally identified Form 8-K Item section."""

    item_code: str
    blocks: tuple[SEC8KLogicalBlock, ...]

    def __post_init__(self) -> None:
        if not self.item_code.strip():
            raise ValueError("item_code must not be empty.")

        if not self.blocks:
            raise ValueError("blocks must not be empty.")

    @property
    def text(self) -> str:
        """Return the section as newline-separated text."""

        return "\n".join(block.text for block in self.blocks)


class SEC8KTerminationReason(StrEnum):
    """How structural Item parsing reached the filing boundary."""

    SIGNATURE_HEADING = "signature_heading"
    END_OF_FILE = "end_of_file"


@dataclass(frozen=True, slots=True, kw_only=True)
class SEC8KParseResult:
    """Structural result produced from one Form 8-K document."""

    sections: tuple[SEC8KItemSection, ...]
    unrecognized_item_codes: tuple[str, ...]
    termination_reason: SEC8KTerminationReason


class _LogicalBlockHTMLParser(HTMLParser):
    """Convert filing HTML into ordered human-readable blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.blocks: list[str] = []
        self._parts: list[str] = []
        self._skip_depth = 0
        self._row_depth = 0

    def _append_space(self) -> None:
        if self._parts and not self._parts[-1].endswith(
            (
                " ",
                "\n",
                "\t",
            )
        ):
            self._parts.append(" ")

    def _flush(self) -> None:
        text = _normalize_whitespace("".join(self._parts))

        self._parts.clear()

        if text:
            self.blocks.append(text)

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs

        normalized_tag = tag.casefold()

        if normalized_tag in _SKIP_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth:
            return

        if normalized_tag == "tr":
            self._flush()
            self._row_depth += 1
            return

        if self._row_depth and normalized_tag in _ROW_BLOCK_TAGS:
            self._flush()
            return

        if normalized_tag in _CELL_TAGS and self._row_depth:
            self._append_space()
            return

        if normalized_tag == "br":
            if self._row_depth:
                self._append_space()
            else:
                self._flush()

            return

        if normalized_tag in _BLOCK_TAGS and not self._row_depth:
            self._flush()

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        normalized_tag = tag.casefold()

        if normalized_tag in _SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1

            return

        if self._skip_depth:
            return

        if normalized_tag == "tr":
            if self._row_depth:
                self._row_depth -= 1

            if self._row_depth == 0:
                self._flush()

            return

        if self._row_depth and normalized_tag in _ROW_BLOCK_TAGS:
            self._flush()
            return

        if normalized_tag in _CELL_TAGS and self._row_depth:
            self._append_space()

            return

        if normalized_tag in _BLOCK_TAGS and not self._row_depth:
            self._flush()

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


class SEC8KFilingParser:
    """Parse the structural Item layout of one SEC Form 8-K."""

    def parse(
        self,
        content: bytes,
    ) -> SEC8KParseResult:
        """Parse filing bytes into recognized Item sections."""

        if not content:
            raise ValueError("content must not be empty.")

        blocks = self._to_logical_blocks(content)

        sections, termination_reason = self._extract_sections(blocks)

        return SEC8KParseResult(
            sections=sections,
            unrecognized_item_codes=self._find_unrecognized_item_codes(blocks),
            termination_reason=termination_reason,
        )

    @staticmethod
    def _to_logical_blocks(
        content: bytes,
    ) -> tuple[SEC8KLogicalBlock, ...]:

        decoded = content.decode(
            "utf-8",
            errors="replace",
        )

        if _HTML_STRUCTURE_PATTERN.search(decoded):
            parser = _LogicalBlockHTMLParser()

            parser.feed(decoded)
            parser.close()

            block_texts = parser.blocks

        else:
            payload_match = _TEXT_PAYLOAD_PATTERN.search(decoded)

            payload = (
                payload_match.group("payload") if payload_match is not None else decoded
            )

            normalized_newlines = payload.replace("\r\n", "\n").replace("\r", "\n")

            block_texts = [
                normalized
                for paragraph in _BLANK_LINE_PATTERN.split(normalized_newlines)
                if (normalized := _normalize_whitespace(paragraph))
            ]

        return tuple(
            SEC8KLogicalBlock(
                index=index,
                text=text,
            )
            for index, text in enumerate(block_texts)
        )

    @staticmethod
    def _candidate_item_code(
        block: SEC8KLogicalBlock,
    ) -> str | None:
        match = _ITEM_HEADING_PATTERN.match(block.text)

        if match is None:
            return None

        return match.group("item_code")

    @classmethod
    def _recognized_item_code(
        cls,
        block: SEC8KLogicalBlock,
    ) -> str | None:
        item_code = cls._candidate_item_code(block)

        if item_code not in _FORM_8K_ITEM_CODES:
            return None

        return item_code

    @classmethod
    def _find_unrecognized_item_codes(
        cls,
        blocks: tuple[SEC8KLogicalBlock, ...],
    ) -> tuple[str, ...]:
        unrecognized: list[str] = []

        for block in blocks:
            item_code = cls._candidate_item_code(block)

            if (
                item_code is None
                or item_code in _FORM_8K_ITEM_CODES
                or item_code in unrecognized
            ):
                continue

            unrecognized.append(item_code)

        return tuple(unrecognized)

    @staticmethod
    def _is_signature_heading(
        block: SEC8KLogicalBlock,
    ) -> bool:
        normalized = re.sub(
            r"[^a-z]",
            "",
            block.text.casefold(),
        )

        return normalized in (
            "signature",
            "signatures",
        )

    @classmethod
    def _is_substantive_body_block(
        cls,
        block: SEC8KLogicalBlock,
    ) -> bool:
        text = block.text.strip()

        if _PAGE_MARKER_PATTERN.fullmatch(text):
            return False

        if _NAVIGATION_ARTIFACT_PATTERN.fullmatch(text):
            return False

        if _SECTION_HEADING_PATTERN.match(text):
            return False

        if _STANDALONE_SUBSECTION_PATTERN.fullmatch(text):
            return False

        if cls._recognized_item_code(block) is not None:
            return False

        if cls._is_signature_heading(block):
            return False

        alphanumeric_text = re.sub(
            r"[^A-Za-z0-9]+",
            "",
            text,
        )

        return len(alphanumeric_text) >= 8

    @classmethod
    def _has_navigation_context(
        cls,
        all_blocks: tuple[SEC8KLogicalBlock, ...],
        start_index: int,
    ) -> bool:
        """Return whether an Item heading belongs to a TOC Item run."""

        index = start_index - 1

        while index >= 0:
            block = all_blocks[index]
            text = block.text.strip()

            if _NAVIGATION_ARTIFACT_PATTERN.fullmatch(text):
                return True

            if cls._recognized_item_code(block) is not None:
                index -= 1
                continue

            if _PAGE_MARKER_PATTERN.fullmatch(text):
                index -= 1
                continue

            return False

        return False

    @classmethod
    def _is_probably_toc_section(
        cls,
        all_blocks: tuple[SEC8KLogicalBlock, ...],
        start_index: int,
        end_index: int,
    ) -> bool:
        """Return whether an Item candidate is probable navigation."""

        section_blocks = all_blocks[start_index:end_index]

        if not section_blocks:
            return False

        body_blocks = section_blocks[1:]

        if any(cls._is_substantive_body_block(block) for block in body_blocks):
            return False

        heading = section_blocks[0].text.strip()

        if _TRAILING_PAGE_MARKER_PATTERN.search(heading):
            return True

        if cls._has_navigation_context(all_blocks, start_index):
            return True

        return any(
            _PAGE_MARKER_PATTERN.fullmatch(block.text.strip()) is not None
            for block in body_blocks
        )

    @classmethod
    def _append_section_unless_navigation(
        cls,
        sections: list[SEC8KItemSection],
        item_code: str,
        all_blocks: tuple[SEC8KLogicalBlock, ...],
        start_index: int,
        end_index: int,
    ) -> bool:
        section_blocks = all_blocks[start_index:end_index]

        if not section_blocks:
            return False

        if cls._is_probably_toc_section(
            all_blocks,
            start_index,
            end_index,
        ):
            return False

        sections.append(
            SEC8KItemSection(
                item_code=item_code,
                blocks=section_blocks,
            )
        )

        return True

    @classmethod
    def _extract_sections(
        cls,
        blocks: tuple[SEC8KLogicalBlock, ...],
    ) -> tuple[
        tuple[SEC8KItemSection, ...],
        SEC8KTerminationReason,
    ]:
        sections: list[SEC8KItemSection] = []

        current_item_code: str | None = None
        current_start_index: int | None = None

        for index, block in enumerate(blocks):
            if current_item_code is not None and cls._is_signature_heading(block):
                assert current_start_index is not None

                appended = cls._append_section_unless_navigation(
                    sections,
                    current_item_code,
                    blocks,
                    current_start_index,
                    index,
                )

                if appended or sections:
                    return (
                        tuple(sections),
                        SEC8KTerminationReason.SIGNATURE_HEADING,
                    )

                current_item_code = None
                current_start_index = None
                continue

            item_code = cls._recognized_item_code(block)

            if item_code is None:
                continue

            if current_item_code is None:
                current_item_code = item_code
                current_start_index = index
                continue

            if item_code == current_item_code:
                continue

            assert current_start_index is not None

            cls._append_section_unless_navigation(
                sections,
                current_item_code,
                blocks,
                current_start_index,
                index,
            )

            current_item_code = item_code
            current_start_index = index

        if current_item_code is not None:
            assert current_start_index is not None

            cls._append_section_unless_navigation(
                sections,
                current_item_code,
                blocks,
                current_start_index,
                len(blocks),
            )

        return (
            tuple(sections),
            SEC8KTerminationReason.END_OF_FILE,
        )
