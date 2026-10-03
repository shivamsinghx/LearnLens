"""Conservative normalization for extracted PDF page text."""

from __future__ import annotations

import re

_HORIZONTAL_SPACE = re.compile(r"[ \t\f\v]+")
_ALNUM = re.compile(r"[0-9A-Za-z]")


def normalize_page_text(text: str) -> str:
    """Clean page text without aggressively rewriting content.

    - Normalize newlines
    - Trim trailing whitespace on each line
    - Collapse runs of horizontal whitespace to a single space
    - Collapse repeated blank lines to a single blank line
    - Preserve paragraph breaks (a single blank line between blocks)
    """
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_HORIZONTAL_SPACE.sub(" ", line).rstrip() for line in normalized.split("\n")]

    collapsed: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run == 1:
                collapsed.append("")
            continue
        blank_run = 0
        collapsed.append(line)

    return "\n".join(collapsed).strip()


def meaningful_character_count(text: str) -> int:
    """Count alphanumeric characters used to judge extractable content."""
    return len(_ALNUM.findall(text))


def has_meaningful_text(pages_text: list[str], *, minimum_chars: int = 20) -> bool:
    """Return True when the document has enough extractable text to be useful."""
    total = sum(meaningful_character_count(page) for page in pages_text)
    return total >= minimum_chars
