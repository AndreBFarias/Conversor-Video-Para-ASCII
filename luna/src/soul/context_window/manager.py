from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.core.logging_config import get_logger

from .config import ContextWindowConfig, get_context_config, get_model_profile
from .progressive_summary import ProgressiveSummary

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


@dataclass
class ContextUsage:
    system_prompt_tokens: int = 0
    memory_tokens: int = 0
    conversation_tokens: int = 0
    user_input_tokens: int = 0
    summary_tokens: int = 0
    emotional_tokens: int = 0
    proactive_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return (
            self.system_prompt_tokens
            + self.memory_tokens
            + self.conversation_tokens
            + self.user_input_tokens
            + self.summary_tokens
            + self.emotional_tokens
            + self.proactive_tokens
        )


@dataclass
class ContextBuildResult:
    system_prompt: str
    memory_context: str
    conversation_history: str
    user_input: str
    summary_context: str
    emotional_context: str
    proactive_context: str
    usage: ContextUsage
    was_compressed: bool = False


class ContextWindowManager:
    def __init__(
        self,
        entity_id: str,
        model_name: str,
        llm_client: Any | None = None,
    ) -> None:
        self.entity_id = entity_id
        self.model_name = model_name

        self._config = get_context_config(model_name)
        self._summary = ProgressiveSummary(self._config, llm_client)

        self._conversation_history: list[dict] = []
        self._last_usage = ContextUsage()

        logger.info(f"ContextWindowManager inicializado: {model_name}, " f"context={self._config.total_budget} tokens")

    @property
    def config(self) -> ContextWindowConfig:
        return self._config

    @property
    def max_turns(self) -> int:
        return self._config.history_limits.max_turns

    @property
    def max_chars_per_turn(self) -> int:
        return self._config.history_limits.max_chars_per_turn

    @property
    def memory_max_chars(self) -> int:
        return self._config.memory_max_chars

    def add_turn(self, role: str, content: str) -> None:
        self._conversation_history.append(
            {
                "role": role,
                "content": content,
            }
        )

    def get_history(self, limit: int | None = None) -> list[dict]:
        if limit is None:
            limit = self.max_turns

        return self._conversation_history[-limit:]

    def clear_history(self) -> None:
        self._conversation_history.clear()
        self._summary.clear()

    def _estimate_tokens(self, text: str) -> int:
        return self._config.model_profile.estimate_tokens(text)

    def _truncate(self, text: str, max_tokens: int) -> str:
        estimated = self._estimate_tokens(text)
        if estimated <= max_tokens:
            return text

        chars_per_token = 1 / self._config.model_profile.tokens_per_char
        max_chars = int(max_tokens * chars_per_token)
        return text[:max_chars] + "..."

    def check_and_compress(self) -> bool:
        current_tokens = self._estimate_history_tokens()

        if not self._summary.should_compress(current_tokens):
            return False

        self._conversation_history, result = self._summary.compress(self._conversation_history)

        if result:
            logger.info(f"Historico comprimido: {result.tokens_saved} tokens economizados")
            return True

        return False

    def _estimate_history_tokens(self) -> int:
        total = 0
        for msg in self._conversation_history:
            content = msg.get("content", "")
            total += self._estimate_tokens(content)
        return total

    def build_context(
        self,
        system_prompt: str,
        memory_context: str,
        user_input: str,
        emotional_context: str = "",
        proactive_context: str = "",
    ) -> ContextBuildResult:
        was_compressed = self.check_and_compress()

        truncated_system = self._truncate(
            system_prompt,
            self._config.system_prompt_budget,
        )

        truncated_memory = self._truncate(
            memory_context,
            self._config.memory_budget,
        )

        history_parts = []
        for msg in self.get_history():
            role = msg.get("role", "user")
            content = msg.get("content", "")[: self.max_chars_per_turn]
            history_parts.append(f"{role}: {content}")

        conversation_str = "\n".join(history_parts)
        truncated_conversation = self._truncate(
            conversation_str,
            self._config.conversation_budget,
        )

        truncated_input = self._truncate(
            user_input,
            self._config.user_input_budget,
        )

        summary_context = self._summary.get_summary_context()

        usage = ContextUsage(
            system_prompt_tokens=self._estimate_tokens(truncated_system),
            memory_tokens=self._estimate_tokens(truncated_memory),
            conversation_tokens=self._estimate_tokens(truncated_conversation),
            user_input_tokens=self._estimate_tokens(truncated_input),
            summary_tokens=self._estimate_tokens(summary_context),
            emotional_tokens=self._estimate_tokens(emotional_context),
            proactive_tokens=self._estimate_tokens(proactive_context),
        )

        self._last_usage = usage

        return ContextBuildResult(
            system_prompt=truncated_system,
            memory_context=truncated_memory,
            conversation_history=truncated_conversation,
            user_input=truncated_input,
            summary_context=summary_context,
            emotional_context=emotional_context,
            proactive_context=proactive_context,
            usage=usage,
            was_compressed=was_compressed,
        )

    def build_prompt(
        self,
        system_prompt: str,
        memory_context: str,
        user_input: str,
        emotional_context: str = "",
        proactive_context: str = "",
    ) -> str:
        ctx = self.build_context(
            system_prompt=system_prompt,
            memory_context=memory_context,
            user_input=user_input,
            emotional_context=emotional_context,
            proactive_context=proactive_context,
        )

        parts = [ctx.system_prompt]

        if ctx.summary_context:
            parts.append(f"\n{ctx.summary_context}")

        if ctx.emotional_context:
            parts.append(f"\n{ctx.emotional_context}")

        if ctx.memory_context:
            parts.append(f"\n[MEMORIAS RELEVANTES]\n{ctx.memory_context}")

        if ctx.proactive_context:
            parts.append(f"\n{ctx.proactive_context}")

        if ctx.conversation_history:
            parts.append(f"\n[HISTORICO]\n{ctx.conversation_history}")

        parts.append(f"\n[USUARIO]\n{ctx.user_input}")

        return "\n".join(parts)

    def get_usage_stats(self) -> dict[str, Any]:
        total_budget = self._config.total_budget
        used = self._last_usage.total_tokens
        remaining = total_budget - used
        usage_pct = (used / total_budget) * 100 if total_budget > 0 else 0

        return {
            "model": self.model_name,
            "total_budget": total_budget,
            "used_tokens": used,
            "remaining_tokens": remaining,
            "usage_percentage": round(usage_pct, 1),
            "breakdown": {
                "system_prompt": self._last_usage.system_prompt_tokens,
                "memory": self._last_usage.memory_tokens,
                "conversation": self._last_usage.conversation_tokens,
                "user_input": self._last_usage.user_input_tokens,
                "summary": self._last_usage.summary_tokens,
                "emotional": self._last_usage.emotional_tokens,
                "proactive": self._last_usage.proactive_tokens,
            },
            "compression_stats": self._summary.get_stats(),
        }

    def get_limits(self) -> dict[str, int]:
        return {
            "max_turns": self.max_turns,
            "max_chars_per_turn": self.max_chars_per_turn,
            "memory_max_chars": self.memory_max_chars,
            "conversation_budget": self._config.conversation_budget,
            "memory_budget": self._config.memory_budget,
        }


_managers: dict[str, ContextWindowManager] = {}


def get_context_window_manager(
    entity_id: str,
    model_name: str,
    llm_client: Any | None = None,
) -> ContextWindowManager:
    key = f"{entity_id}:{model_name}"

    if key not in _managers:
        _managers[key] = ContextWindowManager(entity_id, model_name, llm_client)

    return _managers[key]
