from __future__ import annotations

import re


class TextSanitizer:
    RE_RICH_TAGS_SIMPLE = re.compile(r"\[/?[bi]\]")
    RE_RICH_TAGS_ARGS = re.compile(r"\[/?[bi]\s+[^\]]+\]")
    RE_RICH_COLORS = re.compile(r"\[/?#[a-fA-F0-9]{6}\]")
    RE_RICH_NAMED = re.compile(r"\[/?[a-z_]+\]")
    RE_MARKDOWN_EMPHASIS = re.compile(r"[*_]{1,3}")
    RE_INLINE_CODE = re.compile(r"`[^`]*`")
    RE_URLS = re.compile(r"http[s]?://\S+")
    RE_PUNCTUATION_WORDS = re.compile(r"\b(Ponto|Virgula|Exclamacao|Interrogacao)\b", re.IGNORECASE)

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return ""

        text = cls.RE_RICH_TAGS_SIMPLE.sub("", text)
        text = cls.RE_RICH_TAGS_ARGS.sub("", text)
        text = cls.RE_RICH_COLORS.sub("", text)
        text = cls.RE_RICH_NAMED.sub("", text)
        text = cls.RE_MARKDOWN_EMPHASIS.sub("", text)
        text = cls.RE_INLINE_CODE.sub("", text)
        text = cls.RE_URLS.sub("link", text)
        text = cls.RE_PUNCTUATION_WORDS.sub("", text)
        text = " ".join(text.split())

        return text


def sanitize_text(text: str) -> str:
    return TextSanitizer.sanitize(text)
