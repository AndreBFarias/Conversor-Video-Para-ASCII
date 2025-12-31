# 1

import logging
import threading

from src.core.entity_loader import EntityLoader, get_active_entity
from src.ui.status_decrypt import StatusDecryptWidget

logger = logging.getLogger(__name__)

GENDER_FORMS = {
    "observando": ("observando", "observando"),
    "curiosa": ("curiosa", "curioso"),
    "curiosidade": ("curiosa", "curioso"),
    "sarcastica": ("sarcastica", "sarcastico"),
    "feliz": ("feliz", "feliz"),
    "irritada": ("irritada", "irritado"),
    "triste": ("triste", "triste"),
    "apaixonada": ("apaixonada", "apaixonado"),
    "flertando": ("flertando", "flertando"),
    "neutra": ("neutra", "neutro"),
    "piscando": ("piscando", "piscando"),
    "sensualizando": ("sensualizando", "sensualizando"),
    "obssecada": ("obssecada", "obssecado"),
}


# 2
class EmotionLabelManager:
    def __init__(self, app):
        self.app = app
        self._current_sentiment = "observando"
        self._widget: StatusDecryptWidget | None = None

    def get_widget(self) -> StatusDecryptWidget | None:
        if self._widget is None:
            try:
                self._widget = self.app.query_one("#emotion-label", StatusDecryptWidget)
            except Exception as e:
                logger.debug(f"Erro ao obter widget emotion-label: {e}")
        return self._widget

    # 3
    def update_sentiment(self, sentiment: str, animate: bool = True) -> None:
        if sentiment == self._current_sentiment:
            return

        self._current_sentiment = sentiment
        display_text = self._format_sentiment_text(sentiment)

        widget = self.get_widget()
        if widget and hasattr(widget, "set_text"):
            self._safe_update(widget, display_text, sentiment, animate)
        else:
            self._fallback_update(display_text)

    def _format_sentiment_text(self, sentiment: str) -> str:
        entity_id = get_active_entity()
        entity_loader = EntityLoader(entity_id)
        config = entity_loader.get_config()
        entity_name = config.get("name", entity_id.capitalize())
        gender = config.get("gender", "feminine")

        emotion = sentiment
        for prefix in ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]:
            if sentiment.startswith(f"{prefix}_"):
                emotion = sentiment[len(prefix) + 1 :]
                break

        emotion_base = emotion.lower().replace(" ", "_")
        if emotion_base in GENDER_FORMS:
            fem, masc = GENDER_FORMS[emotion_base]
            emotion_display = masc if gender == "masculine" else fem
        else:
            emotion_display = emotion.replace("_", " ")

        return f"{entity_name} está {emotion_display}"

    def _safe_update(self, widget: StatusDecryptWidget, text: str, sentiment: str, animate: bool) -> None:
        if hasattr(self.app, "_thread_id") and threading.get_ident() != self.app._thread_id:
            self.app.call_from_thread(widget.set_text, text, sentiment, animate)
        else:
            widget.set_text(text, sentiment, animate)

    def _fallback_update(self, text: str) -> None:
        try:
            label = self.app.query_one("#emotion-label")
            formatted = f"[{text}]"

            if hasattr(self.app, "_thread_id") and threading.get_ident() != self.app._thread_id:
                self.app.call_from_thread(label.update, formatted)
            else:
                label.update(formatted)
        except Exception as e:
            logger.debug(f"Fallback update falhou: {e}")


# 4
def patch_animation_controller(animation_controller, app):
    emotion_manager = EmotionLabelManager(app)
    animation_controller._emotion_manager = emotion_manager

    original_run_animation = animation_controller.run_animation

    def patched_run_animation(sentiment: str):
        emotion_manager.update_sentiment(sentiment, animate=True)
        return original_run_animation(sentiment)

    animation_controller.run_animation = patched_run_animation
    logger.info("AnimationController patcheado com EmotionLabelManager")

    return emotion_manager


# "Conhece-te a ti mesmo."
# — Oraculo de Delfos
