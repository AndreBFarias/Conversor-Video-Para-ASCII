from __future__ import annotations

import logging

from src.core.entity_loader import ENTITIES_DIR, EntityLoader, get_active_entity

from .constants import DRACULA_FALLBACK, UNIVERSAL_CSS_PATH
from .css_generator import generate_css_overrides
from .utils import hex_to_rgba

logger = logging.getLogger(__name__)


class ThemeManager:
    _universal_template: str | None = None

    def __init__(self, entity_id: str | None = None):
        self.entity_id = entity_id or get_active_entity()
        self.entity_loader = EntityLoader(self.entity_id)
        self.theme = self.load_theme()
        self._css_cache: str | None = None

    def load_theme(self) -> dict:
        try:
            theme = self.entity_loader.get_full_color_theme()
            if not theme:
                logger.warning(f"Tema nao encontrado para {self.entity_id}, usando Dracula")
                return DRACULA_FALLBACK.copy()
            return theme
        except Exception as e:
            logger.error(f"Erro ao carregar tema: {e}")
            return DRACULA_FALLBACK.copy()

    def reload_for_entity(self, entity_id: str) -> None:
        self.entity_id = entity_id
        self.entity_loader = EntityLoader(entity_id)
        self.theme = self.load_theme()
        self._css_cache = None
        logger.info(f"Tema recarregado para entidade: {entity_id}")

    def get_color(self, key: str) -> str:
        return self.theme.get(key, DRACULA_FALLBACK.get(key, "#ffffff"))

    def load_css_from_file(self) -> str | None:
        css_path = ENTITIES_DIR / self.entity_id / "theme.css"
        if css_path.exists():
            try:
                css_content = css_path.read_text(encoding="utf-8")
                logger.info(f"CSS carregado de arquivo: {css_path}")
                return css_content
            except Exception as e:
                logger.error(f"Erro ao carregar CSS de {css_path}: {e}")
                return None
        return None

    @classmethod
    def load_universal_template(cls) -> str:
        if cls._universal_template is not None:
            return cls._universal_template

        if not UNIVERSAL_CSS_PATH.exists():
            logger.error(f"Template universal nao encontrado: {UNIVERSAL_CSS_PATH}")
            return ""

        try:
            cls._universal_template = UNIVERSAL_CSS_PATH.read_text(encoding="utf-8")
            logger.info(f"Template universal carregado: {UNIVERSAL_CSS_PATH}")
            return cls._universal_template
        except Exception as e:
            logger.error(f"Erro ao carregar template universal: {e}")
            return ""

    def generate_css_from_universal(self) -> str:
        template = self.load_universal_template()
        if not template:
            logger.warning("Template universal vazio, usando CSS gerado")
            return self._generate_css_overrides()

        placeholders = {
            "primary_color": self.get_color("primary_color"),
            "secondary_color": self.get_color("secondary_color"),
            "accent_color": self.get_color("accent_color"),
            "accent_secondary": self.get_color("secondary_color"),
            "background": self.get_color("background"),
            "background_alt": self.get_color("background_alt"),
            "background_input": self.get_color("background_input"),
            "background_input_focus": self.get_color("background_input_focus"),
            "background_panel": self.get_color("background_panel"),
            "background_code": self.get_color("background_code"),
            "glow_color": self.get_color("glow_color"),
            "text_primary": self.get_color("text_primary"),
            "text_secondary": self.get_color("text_secondary"),
            "text_user": self.get_color("text_user"),
            "text_success": self.get_color("text_success"),
            "text_error": self.get_color("text_error"),
            "border_color": self.get_color("border_color"),
            "scrollbar_color": self.get_color("scrollbar_color"),
        }

        css = template
        for key, value in placeholders.items():
            css = css.replace(f"{{{key}}}", value)

        entity_name = self.entity_loader.get_config().get("name", self.entity_id.capitalize())
        css = css.replace("Universal Theme Template", f"Templo de {entity_name}")

        return css

    def _generate_css_overrides(self) -> str:
        return generate_css_overrides(
            entity_id=self.entity_id,
            primary=self.get_color("primary_color"),
            secondary=self.get_color("secondary_color"),
            accent=self.get_color("accent_color"),
            background=self.get_color("background"),
            glow=self.get_color("glow_color"),
            text_primary=self.get_color("text_primary"),
            text_secondary=self.get_color("text_secondary"),
        )

    def apply_theme(self, app) -> None:
        try:
            css_from_universal = self.generate_css_from_universal()
            if css_from_universal:
                self._css_cache = css_from_universal
                app.stylesheet.add_source(css_from_universal)
                logger.info(f"Tema {self.entity_id} aplicado via template universal")
            else:
                css_overrides = self._generate_css_overrides()
                self._css_cache = css_overrides
                app.stylesheet.add_source(css_overrides)
                logger.info(f"Tema {self.entity_id} aplicado via CSS gerado dinamicamente")
        except Exception as e:
            logger.error(f"Erro ao aplicar tema: {e}")

    def get_cached_css(self) -> str | None:
        return self._css_cache
