from __future__ import annotations

from dataclasses import dataclass, field

from src.core.constants import MemoryConstants


@dataclass
class MemorySlice:
    id: str
    summary: str
    category: str
    relevance: float
    timestamp: str
    frequency: int = 1

    def to_compact(self) -> str:
        marker = "*" if self.frequency > 3 else ""
        return f"{marker}[{self.category[:4]}] {self.summary}"


@dataclass
class ContextWindow:
    query: str
    slices: list[MemorySlice] = field(default_factory=list)
    total_chars: int = 0
    max_chars: int = MemoryConstants.MAX_CONTEXT_CHARS

    def add(self, slice: MemorySlice) -> bool:
        slice_text = slice.to_compact()
        new_chars = len(slice_text) + 2
        if self.total_chars + new_chars > self.max_chars:
            return False
        self.slices.append(slice)
        self.total_chars += new_chars
        return True

    def render(self) -> str:
        if not self.slices:
            return ""
        lines = ["[MEM]"]
        for s in self.slices:
            lines.append(s.to_compact())
        return "\n".join(lines)
