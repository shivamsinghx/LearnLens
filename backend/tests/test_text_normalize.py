from app.utils.text_normalize import (
    has_meaningful_text,
    meaningful_character_count,
    normalize_page_text,
)


def test_normalize_collapses_excessive_whitespace_and_blank_lines():
    raw = "Hello   world\n\n\n\nNext   paragraph\t\there  \n\n\n"
    assert normalize_page_text(raw) == "Hello world\n\nNext paragraph here"


def test_normalize_preserves_single_paragraph_break():
    raw = "Line one\n\nLine two"
    assert normalize_page_text(raw) == "Line one\n\nLine two"


def test_meaningful_text_detection():
    assert meaningful_character_count("!!!") == 0
    assert has_meaningful_text(["", "   ", "\n"]) is False
    assert has_meaningful_text(["DBMS notes on page fourteen about joins."]) is True
