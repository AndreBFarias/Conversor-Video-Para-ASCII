from __future__ import annotations

from .constants import CATEGORY_KEYWORDS, MemoryCategory


class MemoryCategorizer:
    def detect_category(self, text: str) -> MemoryCategory:
        text_lower = text.lower()

        scores = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[cat] = score

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return MemoryCategory.CONTEXT

    def generate_summary(self, text: str, max_len: int = 80) -> str:
        text = text.strip()
        text = text.replace("Usuario disse: ", "").replace("Luna respondeu: ", "")

        if len(text) <= max_len:
            return text

        words = text.split()
        summary = []
        current_len = 0

        for word in words:
            if current_len + len(word) + 1 > max_len - 3:
                break
            summary.append(word)
            current_len += len(word) + 1

        return " ".join(summary) + "..."
