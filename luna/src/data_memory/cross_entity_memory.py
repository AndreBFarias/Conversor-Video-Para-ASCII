from datetime import datetime

import config
from src.core.file_lock import read_json_safe, write_json_safe
from src.core.logging_config import get_logger

logger = get_logger(__name__)

SHARED_MEMORY_PATH = config.APP_DIR / "src" / "data_memory" / "shared_memories.json"
SHAREABLE_CATEGORIES = ["user_info", "preference", "fact"]


class CrossEntityMemory:
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        if not SHARED_MEMORY_PATH.exists():
            SHARED_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            write_json_safe(SHARED_MEMORY_PATH, {"memories": [], "entity_switches": [], "user_profile_cache": {}})

    def share_memory(self, memory: dict, source_entity: str) -> bool:
        category = memory.get("category", "")
        if category not in SHAREABLE_CATEGORIES:
            return False

        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            data = {"memories": [], "entity_switches": [], "user_profile_cache": {}}

        shared_entry = {
            "content": memory.get("content", memory.get("text", "")),
            "category": category,
            "source_entity": source_entity,
            "original_timestamp": memory.get("timestamp", ""),
            "shared_at": datetime.now().isoformat(),
        }

        for existing in data["memories"]:
            if existing.get("content") == shared_entry["content"]:
                return False

        data["memories"].append(shared_entry)

        if len(data["memories"]) > 100:
            data["memories"] = data["memories"][-100:]

        write_json_safe(SHARED_MEMORY_PATH, data)
        logger.info(f"Memory shared from {source_entity}: {category}")
        return True

    def get_shared_memories(self, category: str | None = None) -> list[dict]:
        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            return []

        memories = data.get("memories", [])

        if category:
            memories = [m for m in memories if m.get("category") == category]

        return memories

    def record_entity_switch(self, from_entity: str, to_entity: str, reason: str = ""):
        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            data = {"memories": [], "entity_switches": [], "user_profile_cache": {}}

        switch_record = {
            "from": from_entity,
            "to": to_entity,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
        }

        data["entity_switches"].append(switch_record)

        if len(data["entity_switches"]) > 50:
            data["entity_switches"] = data["entity_switches"][-50:]

        write_json_safe(SHARED_MEMORY_PATH, data)
        logger.info(f"Entity switch recorded: {from_entity} -> {to_entity}")

    def get_entity_history(self) -> list[dict]:
        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            return []
        return data.get("entity_switches", [])

    def update_user_profile_cache(self, key: str, value):
        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            data = {"memories": [], "entity_switches": [], "user_profile_cache": {}}

        data["user_profile_cache"][key] = {"value": value, "updated_at": datetime.now().isoformat()}
        write_json_safe(SHARED_MEMORY_PATH, data)

    def get_user_profile_cache(self) -> dict:
        data = read_json_safe(SHARED_MEMORY_PATH)
        if data is None:
            return {}
        return data.get("user_profile_cache", {})

    def get_context_for_entity(self, entity_id: str) -> str:
        shared = self.get_shared_memories("user_info")
        if not shared:
            return ""

        lines = ["[INFO COMPARTILHADA]"]
        for mem in shared[:5]:
            content = mem.get("content", "")[:100]
            source = mem.get("source_entity", "unknown")
            lines.append(f"- {content} (via {source})")

        return "\n".join(lines)


_instance = None


def get_cross_entity_memory() -> CrossEntityMemory:
    global _instance
    if _instance is None:
        _instance = CrossEntityMemory()
    return _instance
