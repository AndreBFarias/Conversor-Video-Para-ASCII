from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ui.elements import ONBOARDING_HIDEABLE, get_selector

if TYPE_CHECKING:
    from src.soul.onboarding.core import OnboardingProcess

logger = logging.getLogger(__name__)


def reveal_element(process: OnboardingProcess, element_id: str):
    try:
        if process.static_overlay:
            process.static_overlay.reveal_element(element_id)
        else:
            selector = get_selector(element_id)
            element = process.app.query_one(selector)
            if element:
                element.remove_class("onboarding-hidden")
                element.add_class("onboarding-revealed")

        process.revealed_elements.add(element_id)
        logger.debug(f"Elemento revelado: {element_id}")
    except Exception as e:
        logger.debug(f"Nao foi possivel revelar {element_id}: {e}")


def hide_all_for_onboarding(process: OnboardingProcess):
    elements_to_hide = [
        "toggle_voice_call",
        "olhar",
        "nova_conversa",
        "ver_historico",
        "editar_alma",
        "canone",
        "quit",
        "attach_file",
    ]
    for elem_id in elements_to_hide:
        try:
            selector = get_selector(elem_id)
            element = process.app.query_one(selector)
            if element:
                element.add_class("onboarding-hidden")
        except Exception as e:
            logger.debug(f"Erro ao esconder elemento {elem_id}: {e}")


def reveal_all(process: OnboardingProcess):
    process.app.reveal_menu()
    process.app.reveal_capabilities()
    for elem_id in ONBOARDING_HIDEABLE:
        try:
            selector = get_selector(elem_id)
            element = process.app.query_one(selector)
            if element:
                element.remove_class("onboarding-hidden")
                element.remove_class("onboarding-revealed")
        except Exception as e:
            logger.debug(f"Erro ao revelar elemento {elem_id}: {e}")


def reload_ui_for_entity(process: OnboardingProcess, entity_id: str):
    logger.info(f"Recarregando UI para entidade: {entity_id}")
    try:
        from src.ui.banner import BannerGlitchWidget
        from src.ui.glitch_button import update_glitch_colors_for_entity
        from src.ui.status_decrypt import StatusDecryptWidget, get_entity_status_text

        banner = process.app.query_one("#welcome-pane", BannerGlitchWidget)
        if banner:
            banner.reload_for_entity(entity_id)
            logger.info(f"Banner atualizado para {entity_id}")

        if hasattr(process.app, "animation_controller"):
            process.app.animation_controller.reload_for_entity(entity_id)
            logger.info(f"Animacoes recarregadas para {entity_id}")

        try:
            emotion_label = process.app.query_one("#emotion-label", StatusDecryptWidget)
            if emotion_label:
                new_status = get_entity_status_text("observando")
                emotion_label.set_text(new_status, sentiment="observando", animate=False)
                logger.info(f"Status atualizado para {entity_id}")
        except Exception as e:
            logger.debug(f"Nao foi possivel atualizar status: {e}")

        update_glitch_colors_for_entity(entity_id)

        from config import ENTITIES_DIR

        css_path = ENTITIES_DIR / entity_id / f"templo_de_{entity_id}.css"
        if css_path.exists():
            try:
                css_content = css_path.read_text(encoding="utf-8")
                process.app.stylesheet.add_source(css_content, path=str(css_path), is_default_css=False)
                process.app.stylesheet.reparse()
                logger.info(f"CSS recarregado de {css_path}")
            except Exception as css_err:
                logger.error(f"Erro ao recarregar CSS: {css_err}")
        else:
            logger.warning(f"CSS nao encontrado: {css_path}")

        apply_entity_styles_inline(process, entity_id)

    except Exception as e:
        logger.error(f"Erro ao recarregar UI para {entity_id}: {e}")


def apply_entity_styles_inline(process: OnboardingProcess, entity_id: str):
    try:
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader(entity_id)
        theme = loader.get_full_color_theme()
        if not theme:
            logger.warning(f"Tema nao encontrado para {entity_id}")
            return

        background = theme.get("background", "#282a36")
        border_color = theme.get("border_color", theme.get("text_secondary", "#6272a4"))
        primary = theme.get("primary_color", "#bd93f9")

        elements_with_border = ["#ascii-container", "#menu-pane", "#chat-area", "#input-container"]

        for selector in elements_with_border:
            try:
                element = process.app.query_one(selector)
                element.styles.background = background
                element.styles.border = ("heavy", border_color)
            except Exception as e:
                logger.debug(f"Nao foi possivel aplicar estilo em {selector}: {e}")

        elements_with_background = ["#right-pane", "#welcome-pane", "#chat-list", "#status-area"]

        for selector in elements_with_background:
            try:
                element = process.app.query_one(selector)
                element.styles.background = background
            except Exception as e:
                logger.debug(f"Nao foi possivel aplicar background em {selector}: {e}")

        process.app.screen.styles.background = background
        process.app.refresh(layout=True)
        logger.info(f"Estilos inline aplicados para {entity_id}: bg={background}, border={border_color}")

    except Exception as e:
        logger.error(f"Erro ao aplicar estilos inline: {e}")
