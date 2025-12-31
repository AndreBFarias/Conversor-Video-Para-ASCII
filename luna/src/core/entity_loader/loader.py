from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import APP_DIR
from src.core.file_lock import read_json_safe
from src.core.logging_config import get_logger

from .color_utils import darken_color, generate_static_base, lighten_color
from .constants import (
    DEFAULT_BANNER,
    DEFAULT_COLORS,
    DEFAULT_GRADIENT,
    ENTITIES_DIR,
    REGISTRY_PATH,
)

logger = get_logger(__name__)


class EntityLoader:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.entity_data = self.load_entity(entity_id)

    def load_entity(self, entity_id: str) -> dict[str, Any]:
        try:
            registry = read_json_safe(REGISTRY_PATH)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar registry: {e}")
            return self._fallback_to_luna()

        entity_info = registry.get("entities", {}).get(entity_id)
        if not entity_info:
            logger.warning(f"Entidade {entity_id} nao encontrada no registry")
            return self._fallback_to_luna()

        if not entity_info.get("available", False):
            logger.warning(f"Entidade {entity_id} nao esta disponivel")
            return self._fallback_to_luna()

        entity_dir = ENTITIES_DIR / entity_id
        config_path = entity_dir / "config.json"
        soul_path = entity_dir / "alma.txt"
        animations_dir = entity_dir / "animations"

        if not config_path.exists():
            logger.error(f"Config nao encontrado para {entity_id}")
            return self._fallback_to_luna()

        try:
            config = read_json_safe(config_path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar config de {entity_id}: {e}")
            return self._fallback_to_luna()

        return {
            "id": entity_id,
            "registry_info": entity_info,
            "config": config,
            "soul_path": soul_path,
            "animations_dir": animations_dir,
        }

    def _fallback_to_luna(self) -> dict[str, Any]:
        if self.entity_id == "luna":
            logger.error("Fallback para Luna falhou - Luna tambem nao carregou")
            return self._get_minimal_entity_data("luna")

        logger.info(f"Fallback de {self.entity_id} para Luna")
        try:
            luna_loader = EntityLoader("luna")
            if luna_loader.entity_data:
                return luna_loader.entity_data
            logger.error("EntityLoader de Luna retornou dados vazios")
            return self._get_minimal_entity_data("luna")
        except RecursionError:
            logger.error("Recursao infinita detectada no fallback para Luna")
            return self._get_minimal_entity_data("luna")
        except Exception as e:
            logger.error(f"Erro ao carregar Luna como fallback: {e}")
            return self._get_minimal_entity_data("luna")

    def _get_minimal_entity_data(self, entity_id: str) -> dict[str, Any]:
        entity_dir = ENTITIES_DIR / entity_id
        return {
            "id": entity_id,
            "registry_info": {"name": entity_id.capitalize(), "available": True},
            "config": {
                "name": entity_id.capitalize(),
                "primary_color": "#bd93f9",
                "secondary_color": "#ff79c6",
                "accent_color": "#50fa7b",
                "tone_primary": "neutra",
                "tone_secondary": "curiosa",
            },
            "soul_path": entity_dir / "alma.txt",
            "animations_dir": entity_dir / "animations",
        }

    def get_soul_prompt(self) -> str:
        soul_path = self.entity_data.get("soul_path")
        if not soul_path or not soul_path.exists():
            logger.error(f"Arquivo de alma nao encontrado: {soul_path}")
            return ""

        try:
            with open(soul_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao ler alma: {e}")
            return ""

    def get_config(self) -> dict[str, Any]:
        return self.entity_data.get("config", {})

    def get_animation_path(self, emotion: str) -> Path:
        entity_name = self.entity_data.get("config", {}).get("name", "Luna")
        search_dirs = []

        entity_anim_dir = self.entity_data.get("animations_dir")
        if entity_anim_dir and entity_anim_dir.exists():
            search_dirs.append(entity_anim_dir)

        luna_anim_dir = APP_DIR / "src" / "assets" / "panteao" / "entities" / "luna" / "animations"
        if luna_anim_dir.exists():
            search_dirs.append(luna_anim_dir)

        for animations_dir in search_dirs:
            animation_file = animations_dir / f"{entity_name}_{emotion}.txt"
            animation_file_gz = animations_dir / f"{entity_name}_{emotion}.txt.gz"

            if animation_file.exists():
                return animation_file
            if animation_file_gz.exists():
                return animation_file_gz

        for animations_dir in search_dirs:
            observando = animations_dir / f"{entity_name}_observando.txt"
            observando_gz = animations_dir / f"{entity_name}_observando.txt.gz"
            if observando.exists():
                return observando
            if observando_gz.exists():
                return observando_gz

        fallback = luna_anim_dir / "Luna_observando.txt.gz"
        if fallback.exists():
            return fallback

        fallback_txt = luna_anim_dir / "Luna_observando.txt"
        logger.warning(f"Animacao {emotion} nao encontrada, usando fallback: {fallback_txt}")
        return fallback_txt

    def get_voice_config(self) -> dict[str, Any]:
        config = self.get_config()
        return config.get("voice", {})

    def get_color_theme(self) -> dict[str, Any]:
        config = self.get_config()
        aesthetics = config.get("aesthetics", {})
        return aesthetics.get("theme", DEFAULT_COLORS.copy())

    def get_full_color_theme(self) -> dict[str, Any]:
        theme = self.get_color_theme()

        background = theme.get("background", "#282a36")
        primary = theme.get("primary_color", "#bd93f9")
        secondary = theme.get("secondary_color", "#ff79c6")
        accent = theme.get("accent_color", "#50fa7b")
        glow = theme.get("glow_color", primary)
        text_secondary = theme.get("text_secondary", "#6272a4")

        defaults = {
            "background_alt": darken_color(background, 15),
            "background_input": lighten_color(background, 20),
            "background_input_focus": lighten_color(background, 30),
            "background_panel": lighten_color(background, 10),
            "background_code": darken_color(background, 25),
            "text_user": "#8be9fd",
            "text_success": accent,
            "text_error": "#ff5555",
            "border_color": text_secondary,
            "scrollbar_color": text_secondary,
            "tv_static": {"base": generate_static_base(background), "accent": glow, "secondary": secondary},
        }

        for key, default_val in defaults.items():
            if key not in theme:
                theme[key] = default_val
            elif key == "tv_static" and not isinstance(theme.get("tv_static"), dict):
                theme[key] = default_val

        return theme

    def get_banner_ascii(self) -> list[str]:
        config = self.get_config()
        aesthetics = config.get("aesthetics", {})
        return aesthetics.get("banner_ascii", DEFAULT_BANNER.copy())

    def get_gradient(self) -> list[str]:
        config = self.get_config()
        aesthetics = config.get("aesthetics", {})
        return aesthetics.get("gradient", DEFAULT_GRADIENT.copy())

    def list_available_entities(self) -> list[dict]:
        try:
            registry = read_json_safe(REGISTRY_PATH)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar registry: {e}")
            return []

        entities = registry.get("entities", {})
        available = [
            {
                "id": eid,
                "name": edata.get("name"),
                "gender": edata.get("gender"),
                "archetype": edata.get("archetype", []),
                "available": edata.get("available", False),
                "voice_configured": edata.get("voice_configured", False),
            }
            for eid, edata in entities.items()
            if edata.get("available", False)
        ]
        return available

    def is_entity_available(self, entity_id: str) -> bool:
        try:
            registry = read_json_safe(REGISTRY_PATH)
        except (FileNotFoundError, json.JSONDecodeError):
            return False

        entity = registry.get("entities", {}).get(entity_id, {})
        return entity.get("available", False)
