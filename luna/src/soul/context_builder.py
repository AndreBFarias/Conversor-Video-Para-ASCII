from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.data_memory.cross_entity_memory import get_cross_entity_memory
from src.data_memory.proactive_recall import get_proactive_recall
from src.data_memory.smart_memory import get_entity_smart_memory
from src.soul.emotional_state import get_emotional_manager

logger = get_logger(__name__)


@dataclass
class ContextBudget:
    total_tokens: int = 4000
    system_prompt: int = 1000
    memory: int = 1000
    conversation: int = 1500
    user_input: int = 500


@dataclass
class BuiltContext:
    system_prompt: str
    memory_context: str
    conversation_history: str
    user_input: str
    proactive_recall: str | None
    emotional_context: str | None
    total_estimated_tokens: int


class ContextBuilder:
    def __init__(self, entity_id: str, budget: ContextBudget | None = None):
        self.entity_id = entity_id
        self.budget = budget or ContextBudget()
        self.memory = get_entity_smart_memory(entity_id)
        self.cross_memory = get_cross_entity_memory()
        self.proactive = get_proactive_recall(entity_id)

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _truncate_to_budget(self, text: str, max_tokens: int) -> str:
        estimated = self._estimate_tokens(text)
        if estimated <= max_tokens:
            return text

        max_chars = max_tokens * 4
        return text[:max_chars] + "..."

    def _get_system_prompt(self) -> str:
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader(self.entity_id)
        return loader.get_soul_prompt()

    def _get_memory_context(self, user_input: str) -> str:
        relevant = self.memory.retrieve(user_input, max_chars=self.budget.memory * 4)

        shared = self.cross_memory.get_shared_memories("user_info")
        shared_context = ""
        if shared:
            shared_items = [m.get("content", "") for m in shared[:3]]
            shared_context = "\n[INFO COMPARTILHADA]: " + " | ".join(shared_items)

        return relevant + shared_context

    def _get_conversation_history(self, history: list[dict]) -> str:
        if not history:
            return ""

        formatted = []
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _get_proactive_recall(self, user_input: str, context: str) -> str | None:
        recall_data = self.proactive.find_relevant_memory(user_input, context)
        if recall_data:
            return self.proactive.format_recall_prompt(recall_data)
        return None

    def _get_emotional_context(self) -> str:
        try:
            emotional_mgr = get_emotional_manager(self.entity_id)
            return emotional_mgr.get_mood_context()
        except Exception as e:
            logger.debug(f"Erro ao obter contexto emocional: {e}")
            return ""

    def build(self, user_input: str, conversation_history: list[dict] = None) -> BuiltContext:
        system_prompt = self._get_system_prompt()
        system_prompt = self._truncate_to_budget(system_prompt, self.budget.system_prompt)

        memory_context = self._get_memory_context(user_input)
        memory_context = self._truncate_to_budget(memory_context, self.budget.memory)

        conv_history = self._get_conversation_history(conversation_history or [])
        conv_history = self._truncate_to_budget(conv_history, self.budget.conversation)

        proactive = self._get_proactive_recall(user_input, conv_history)
        emotional = self._get_emotional_context()

        user_input_truncated = self._truncate_to_budget(user_input, self.budget.user_input)

        total_tokens = sum(
            [
                self._estimate_tokens(system_prompt),
                self._estimate_tokens(memory_context),
                self._estimate_tokens(conv_history),
                self._estimate_tokens(user_input_truncated),
                self._estimate_tokens(proactive or ""),
                self._estimate_tokens(emotional or ""),
            ]
        )

        return BuiltContext(
            system_prompt=system_prompt,
            memory_context=memory_context,
            conversation_history=conv_history,
            user_input=user_input_truncated,
            proactive_recall=proactive,
            emotional_context=emotional,
            total_estimated_tokens=total_tokens,
        )

    def build_prompt(self, user_input: str, conversation_history: list[dict] = None) -> str:
        ctx = self.build(user_input, conversation_history)

        parts = [ctx.system_prompt]

        if ctx.emotional_context:
            parts.append(f"\n{ctx.emotional_context}")

        if ctx.memory_context:
            parts.append(f"\n[MEMORIAS RELEVANTES]\n{ctx.memory_context}")

        if ctx.proactive_recall:
            parts.append(f"\n{ctx.proactive_recall}")

        if ctx.conversation_history:
            parts.append(f"\n[HISTORICO]\n{ctx.conversation_history}")

        parts.append(f"\n[USUARIO]\n{ctx.user_input}")

        return "\n".join(parts)


_context_builders: dict[str, ContextBuilder] = {}


def get_context_builder(entity_id: str) -> ContextBuilder:
    if entity_id not in _context_builders:
        _context_builders[entity_id] = ContextBuilder(entity_id)
    return _context_builders[entity_id]
