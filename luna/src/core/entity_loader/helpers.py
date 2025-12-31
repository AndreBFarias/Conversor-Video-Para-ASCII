from __future__ import annotations

from typing import Any

from src.core.file_lock import read_json_safe, update_json_safe
from src.core.logging_config import get_logger

from .constants import PROFILE_PATH
from .loader import EntityLoader

logger = get_logger(__name__)

_active_loader: EntityLoader | None = None


def get_active_entity() -> str:
    if not PROFILE_PATH.exists():
        logger.warning("Profile.json nao encontrado, usando luna como default")
        return "luna"

    try:
        profile = read_json_safe(PROFILE_PATH)
        return profile.get("active_entity", "luna")
    except Exception as e:
        logger.error(f"Erro ao ler profile.json: {e}")
        return "luna"


def set_active_entity(entity_id: str, reload_config: bool = True) -> bool:
    loader = EntityLoader(entity_id)
    if not loader.is_entity_available(entity_id):
        logger.error(f"Entidade {entity_id} nao esta disponivel")
        return False

    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        profile = read_json_safe(PROFILE_PATH) if PROFILE_PATH.exists() else {}
        old_entity = profile.get("active_entity")

        updates = {"active_entity": entity_id}
        if old_entity and old_entity != entity_id:
            updates["pending_entity_intro"] = entity_id
            logger.debug(f"Marcando intro pendente para: {entity_id}")

        update_json_safe(PROFILE_PATH, updates)

        if reload_config:
            import config

            entity_name = loader.get_config().get("name", entity_id.capitalize())
            config.reload_entity_config(entity_name)

        logger.info(f"Entidade ativa alterada para: {entity_id}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar active_entity: {e}")
        return False


def get_entity_phrases(entity_id: str) -> dict[str, Any]:
    loader = EntityLoader(entity_id)
    config = loader.get_config()
    return config.get("phrases", {})


def get_entity_name(entity_id: str) -> str:
    loader = EntityLoader(entity_id)
    config = loader.get_config()
    return config.get("name", entity_id.capitalize())


def get_active_loader() -> EntityLoader:
    global _active_loader
    entity_id = get_active_entity()
    if _active_loader is None or _active_loader.entity_id != entity_id:
        _active_loader = EntityLoader(entity_id)
    return _active_loader


def reload_active_loader() -> EntityLoader:
    global _active_loader
    entity_id = get_active_entity()
    _active_loader = EntityLoader(entity_id)
    return _active_loader
