import re
from datetime import datetime, timedelta

from src.core.logging_config import get_logger
from src.data_memory.smart_memory import get_entity_smart_memory

logger = get_logger(__name__)

TRIGGER_PATTERNS = [
    (r"\b(lembr[ao]|lembra)\b", "memory_trigger"),
    (r"\b(última vez|da outra vez|antes)\b", "temporal_trigger"),
    (r"\b(você disse|eu disse|falamos|conversamos)\b", "conversation_trigger"),
    (r"\b(sempre|nunca|toda vez)\b", "pattern_trigger"),
    (r"\b(por que|porque|como assim)\b", "explanation_trigger"),
]


class ProactiveRecall:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.memory = get_entity_smart_memory(entity_id)
        self.last_recall: datetime | None = None
        self.recall_cooldown = timedelta(minutes=5)

    def detect_triggers(self, user_input: str) -> list[tuple[str, str]]:
        triggers = []
        for pattern, trigger_type in TRIGGER_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                triggers.append((pattern, trigger_type))
        return triggers

    def should_recall(self) -> bool:
        if self.last_recall is None:
            return True
        return datetime.now() - self.last_recall > self.recall_cooldown

    def find_relevant_memory(self, user_input: str, conversation_context: str = "") -> dict | None:
        if not self.should_recall():
            return None

        triggers = self.detect_triggers(user_input)
        if not triggers:
            return None

        combined_query = f"{user_input} {conversation_context}"

        self.memory._ensure_loaded()

        if not self.memory._store or not hasattr(self.memory._store, "memories"):
            return None

        memories = self.memory._store.memories
        if not memories:
            return None

        old_memories = [m for m in memories if self._is_old_enough(m.get("timestamp", ""), days=1)]

        if not old_memories:
            return None

        import numpy as np

        from src.data_memory.embeddings import get_embedding

        query_emb = get_embedding(combined_query)
        query_norm = np.linalg.norm(query_emb)
        if query_norm > 0:
            query_emb = query_emb / query_norm

        best_match = None
        best_score = 0.5

        for mem in old_memories:
            content = mem.get("text", "")
            mem_emb = get_embedding(content)
            mem_norm = np.linalg.norm(mem_emb)
            if mem_norm > 0:
                mem_emb = mem_emb / mem_norm

            score = float(np.dot(query_emb, mem_emb))

            if score > best_score:
                best_score = score
                best_match = mem

        if best_match:
            self.last_recall = datetime.now()
            return {
                "memory": best_match,
                "score": best_score,
                "trigger_type": triggers[0][1] if triggers else "unknown",
            }

        return None

    def _is_old_enough(self, timestamp: str, days: int) -> bool:
        try:
            clean_ts = timestamp.replace("Z", "").replace("+00:00", "")
            mem_time = datetime.fromisoformat(clean_ts[:19])
            return (datetime.now() - mem_time).days >= days
        except (ValueError, TypeError):
            return False

    def format_recall_prompt(self, recall_data: dict) -> str:
        if not recall_data:
            return ""

        memory = recall_data.get("memory", {})
        content = memory.get("text", "")
        timestamp = memory.get("timestamp", "")

        try:
            clean_ts = timestamp.replace("Z", "").replace("+00:00", "")
            mem_time = datetime.fromisoformat(clean_ts[:19])
            age_days = (datetime.now() - mem_time).days

            if age_days == 1:
                time_ref = "ontem"
            elif age_days < 7:
                time_ref = f"ha {age_days} dias"
            elif age_days < 30:
                weeks = age_days // 7
                time_ref = f"ha {weeks} semana{'s' if weeks > 1 else ''}"
            else:
                time_ref = "ha algum tempo"
        except (ValueError, TypeError):
            time_ref = "antes"

        content_preview = content[:150] + "..." if len(content) > 150 else content
        return f"[MEMORIA RELEVANTE ({time_ref}): {content_preview}]"

    def reset_cooldown(self):
        self.last_recall = None


_recall_instances: dict[str, ProactiveRecall] = {}


def get_proactive_recall(entity_id: str) -> ProactiveRecall:
    if entity_id not in _recall_instances:
        _recall_instances[entity_id] = ProactiveRecall(entity_id)
    return _recall_instances[entity_id]
