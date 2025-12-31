from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import config

if TYPE_CHECKING:
    from src.soul.onboarding.core import OnboardingProcess

logger = logging.getLogger(__name__)

USER_DIR = config.APP_DIR / "src" / "data_memory" / "user"
PROFILE_PATH = USER_DIR / "profile.json"
EVENTS_DIR = config.APP_DIR / "src" / "data_memory" / "events"
FACES_DIR = config.APP_DIR / "src" / "data_memory" / "faces"


def ensure_directories():
    os.makedirs(USER_DIR, exist_ok=True)
    os.makedirs(EVENTS_DIR, exist_ok=True)
    os.makedirs(FACES_DIR, exist_ok=True)


def verify_first_run() -> bool:
    if not os.path.exists(PROFILE_PATH):
        return True
    try:
        with open(PROFILE_PATH) as f:
            data = json.load(f)
            return not data.get("onboarding_completo", False)
    except (OSError, json.JSONDecodeError):
        return True


def reset_profile(personalidade):
    if os.path.exists(PROFILE_PATH):
        try:
            os.remove(PROFILE_PATH)
            logger.info("Perfil anterior removido para novo onboarding")
        except Exception as e:
            logger.error(f"Erro ao remover perfil: {e}")
    personalidade.resetar_todas()


def save_profile_update(updates: dict[str, Any]):
    try:
        current = {}
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH) as f:
                current = json.load(f)

        for k, v in updates.items():
            if isinstance(v, dict) and k in current and isinstance(current[k], dict):
                current[k].update(v)
            else:
                current[k] = v

        with open(PROFILE_PATH, "w") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving profile: {e}")


def get_profile_preference(key: str, default=None):
    try:
        if PROFILE_PATH.exists():
            with open(PROFILE_PATH, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("preferencias", {}).get(key, default)
    except Exception as e:
        logger.debug(f"Erro ao ler preferencia {key}: {e}")
    return default


def get_name() -> str:
    try:
        with open(PROFILE_PATH) as f:
            return json.load(f).get("nome", "Viajante")
    except (OSError, json.JSONDecodeError):
        return "Viajante"


def log_event(event_type: str, payload: Any):
    try:
        filename = EVENTS_DIR / f"{datetime.now().timestamp()}_{event_type}.json"
        data = {"timestamp": datetime.now().isoformat(), "type": event_type, "payload": payload}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error logging event: {e}")
