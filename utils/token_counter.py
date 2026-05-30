"""
token_counter.py – Lightweight token estimation utilities.

Uses a simple character-based heuristic (chars / 4) that approximates the
GPT-3/4 tokeniser for English text.  No external dependency required.
"""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate the number of LLM tokens in *text*.

    Heuristic: ~4 characters per token (GPT-family average for English).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def count_words(text: str) -> int:
    """Return a simple whitespace-split word count."""
    return len(text.split()) if text else 0


def count_chars(text: str) -> int:
    """Return the total character count (including whitespace)."""
    return len(text)


def format_stat(value: int) -> str:
    """Format an integer stat with comma thousands separators."""
    return f"{value:,}"
