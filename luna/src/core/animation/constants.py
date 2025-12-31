from __future__ import annotations

import unicodedata

UNICODE_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2002": " ",
    "\u2003": " ",
}


def sanitize_frame(frame: str) -> str:
    normalized = unicodedata.normalize("NFKC", frame)

    for old, new in UNICODE_REPLACEMENTS.items():
        normalized = normalized.replace(old, new)

    return normalized
