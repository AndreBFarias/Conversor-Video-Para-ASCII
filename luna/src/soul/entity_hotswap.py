from datetime import datetime
from pathlib import Path

from config import APP_DIR
from src.core.entity_loader import EntityLoader
from src.core.file_lock import update_json_safe
from src.core.logging_config import get_logger
from src.data_memory.cross_entity_memory import get_cross_entity_memory

logger = get_logger(__name__)

PROFILE_PATH = APP_DIR / "src" / "data_memory" / "user" / "profile.json"


class EntityHotSwap:
    def __init__(self):
        self.current_entity: str | None = None
        self.cross_memory = get_cross_entity_memory()
        self._loaders: dict[str, EntityLoader] = {}
        self._conversation_buffer: list[dict] = []
        self._swap_history: list[dict] = []

    def _get_loader(self, entity_id: str) -> EntityLoader:
        if entity_id not in self._loaders:
            self._loaders[entity_id] = EntityLoader(entity_id)
        return self._loaders[entity_id]

    def initialize(self, entity_id: str):
        self.current_entity = entity_id
        self._get_loader(entity_id)
        logger.info(f"Entity initialized: {entity_id}")

    @property
    def entity_dir(self) -> Path | None:
        if not self.current_entity:
            return None
        loader = self._get_loader(self.current_entity)
        return loader.entity_data.get("animations_dir", None)

    @property
    def config(self) -> dict | None:
        if not self.current_entity:
            return None
        loader = self._get_loader(self.current_entity)
        return loader.get_config()

    def can_swap_to(self, target_entity: str) -> dict:
        loader = self._get_loader(target_entity)
        entity_dir = loader.entity_data.get("animations_dir")

        checks = {
            "entity_exists": entity_dir is not None and entity_dir.parent.exists(),
            "soul_exists": loader.get_soul_prompt() is not None and len(loader.get_soul_prompt()) > 0,
            "config_valid": loader.get_config() is not None,
        }

        can_swap = all(checks.values())

        return {"can_swap": can_swap, "checks": checks, "target": target_entity}

    def swap(self, target_entity: str, reason: str = "user_request", preserve_conversation: bool = True) -> dict:
        if self.current_entity == target_entity:
            return {"success": True, "message": "Already on this entity"}

        check = self.can_swap_to(target_entity)
        if not check["can_swap"]:
            return {"success": False, "error": "Target entity not ready", "checks": check["checks"]}

        from_entity = self.current_entity

        self.cross_memory.record_entity_switch(from_entity or "none", target_entity, reason)

        if from_entity and preserve_conversation:
            self._save_conversation_state(from_entity)

        self.current_entity = target_entity

        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        update_json_safe(PROFILE_PATH, {"active_entity": target_entity})

        self._swap_history.append(
            {"from": from_entity, "to": target_entity, "reason": reason, "timestamp": datetime.now().isoformat()}
        )

        logger.info(f"Entity swapped: {from_entity} -> {target_entity}")

        return {"success": True, "from": from_entity, "to": target_entity, "timestamp": datetime.now().isoformat()}

    def _save_conversation_state(self, entity_id: str):
        pass

    def get_transition_prompt(self, from_entity: str, to_entity: str) -> str:
        from_loader = self._get_loader(from_entity)
        to_loader = self._get_loader(to_entity)

        from_name = from_loader.get_config().get("name", from_entity.capitalize())
        to_name = to_loader.get_config().get("name", to_entity.capitalize())

        return f"[{from_name} se despede enquanto {to_name} assume o controle...]"

    def get_current_loader(self) -> EntityLoader | None:
        if self.current_entity:
            return self._get_loader(self.current_entity)
        return None

    def get_swap_history(self) -> list[dict]:
        return self._swap_history.copy()

    def preload_entity(self, entity_id: str):
        try:
            self._get_loader(entity_id)
            logger.debug(f"Entity {entity_id} preloaded")
        except Exception as e:
            logger.warning(f"Failed to preload {entity_id}: {e}")


_hotswap_instance: EntityHotSwap | None = None


def get_entity_hotswap() -> EntityHotSwap:
    global _hotswap_instance
    if _hotswap_instance is None:
        _hotswap_instance = EntityHotSwap()
    return _hotswap_instance


def reset_hotswap():
    global _hotswap_instance
    _hotswap_instance = None
