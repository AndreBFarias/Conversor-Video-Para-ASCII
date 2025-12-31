from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from .config import ContextWindowConfig

logger = get_logger(__name__)


@dataclass
class SummaryResult:
    original_tokens: int
    compressed_tokens: int
    summary_text: str
    messages_summarized: int
    compression_ratio: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_summarized: bool = False
    summary_id: str | None = None


class ProgressiveSummary:
    def __init__(
        self,
        config: ContextWindowConfig,
        llm_summarizer: Any | None = None,
    ) -> None:
        self._config = config
        self._llm = llm_summarizer
        self._summaries: list[SummaryResult] = []
        self._current_summary: str = ""

    def should_compress(self, current_tokens: int) -> bool:
        threshold = self._config.summary_threshold
        return current_tokens >= threshold

    def get_compression_count(self, history: list[dict]) -> int:
        compress_pct = self._config.history_limits.summary_compress_pct
        count = int(len(history) * compress_pct)
        return max(count, 1)

    def compress(
        self,
        history: list[dict],
        force: bool = False,
    ) -> tuple[list[dict], SummaryResult | None]:
        if not history:
            return history, None

        current_tokens = self._estimate_history_tokens(history)

        if not force and not self.should_compress(current_tokens):
            return history, None

        compress_count = self.get_compression_count(history)
        to_compress = history[:compress_count]
        remaining = history[compress_count:]

        summary_text = self._generate_summary(to_compress)
        original_tokens = self._estimate_history_tokens(to_compress)
        compressed_tokens = self._estimate_tokens(summary_text)

        result = SummaryResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            summary_text=summary_text,
            messages_summarized=len(to_compress),
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 0,
        )

        self._summaries.append(result)
        self._current_summary = self._merge_summaries()

        logger.info(
            f"Compressao: {result.messages_summarized} msgs, "
            f"{result.tokens_saved} tokens economizados, "
            f"ratio {result.compression_ratio:.2f}"
        )

        return remaining, result

    def _generate_summary(self, messages: list[dict]) -> str:
        if self._llm is not None:
            return self._generate_llm_summary(messages)
        return self._generate_extractive_summary(messages)

    def _generate_llm_summary(self, messages: list[dict]) -> str:
        formatted = self._format_messages(messages)
        prompt = f"""Resuma esta conversa de forma concisa, mantendo informacoes importantes:

{formatted}

Resumo (maximo 150 palavras):"""

        try:
            response = self._llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"Erro ao gerar resumo via LLM: {e}")
            return self._generate_extractive_summary(messages)

    def _generate_extractive_summary(self, messages: list[dict]) -> str:
        if not messages:
            return ""

        key_points = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content:
                continue

            sentences = content.split(".")
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 10:
                    key_points.append(f"[{role}] {first_sentence}")

        if len(key_points) > 5:
            key_points = key_points[:2] + ["..."] + key_points[-2:]

        return " | ".join(key_points)

    def _format_messages(self, messages: list[dict]) -> str:
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _merge_summaries(self) -> str:
        if not self._summaries:
            return ""

        recent = self._summaries[-3:]
        texts = [s.summary_text for s in recent if s.summary_text]
        return " | ".join(texts)

    def _estimate_tokens(self, text: str) -> int:
        return self._config.model_profile.estimate_tokens(text)

    def _estimate_history_tokens(self, history: list[dict]) -> int:
        total = 0
        for msg in history:
            content = msg.get("content", "")
            total += self._estimate_tokens(content)
        return total

    def get_summary_context(self) -> str:
        if not self._current_summary:
            return ""
        return f"[RESUMO DA CONVERSA ANTERIOR]\n{self._current_summary}"

    def get_stats(self) -> dict[str, Any]:
        if not self._summaries:
            return {
                "total_compressions": 0,
                "total_tokens_saved": 0,
                "average_compression_ratio": 0,
            }

        total_saved = sum(s.tokens_saved for s in self._summaries)
        avg_ratio = sum(s.compression_ratio for s in self._summaries) / len(self._summaries)

        return {
            "total_compressions": len(self._summaries),
            "total_tokens_saved": total_saved,
            "average_compression_ratio": avg_ratio,
            "total_messages_summarized": sum(s.messages_summarized for s in self._summaries),
        }

    def clear(self) -> None:
        self._summaries.clear()
        self._current_summary = ""


_summary_instances: dict[str, ProgressiveSummary] = {}


def get_progressive_summary(
    entity_id: str,
    config: ContextWindowConfig,
    llm: Any | None = None,
) -> ProgressiveSummary:
    if entity_id not in _summary_instances:
        _summary_instances[entity_id] = ProgressiveSummary(config, llm)
    return _summary_instances[entity_id]
