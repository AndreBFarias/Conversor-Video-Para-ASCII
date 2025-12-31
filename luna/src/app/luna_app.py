"""
TemploDaAlma - Aplicacao principal Textual.

Classe principal que orquestra toda a interface do Luna:
- Composicao de widgets (banner, chat, input)
- Gerenciamento de estado (AppMode)
- Handlers de eventos (teclado, mouse, voz)
- Integracao com Consciencia, Boca e Visao

Classes principais:
    TemploDaAlma: App Textual principal

Mixins utilizados:
    - MenuActionsMixin: Acoes de menu
    - VoiceActionsMixin: Acoes de voz
    - VisionActionsMixin: Acoes de visao
    - ClipboardActionsMixin: Acoes de clipboard

Dependencias:
    - src.controllers: UIController, AudioController, ThreadingController
    - src.soul: Consciencia, Boca, Visao
    - src.ui: Widgets e screens
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from typing import TYPE_CHECKING, Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

import config
from src.controllers import AudioController, ThreadingController, UIController
from src.core import AnimationController, FileAttachmentHandler, SessionManager
from src.core.event_logger import get_event_logger
from src.soul import VOICE_AVAILABLE, Boca, Consciencia, OuvidoSussurrante, Visao, get_metrics
from src.soul.onboarding import OnboardingProcess
from src.soul.threading_manager import TranscriptionResult
from src.ui import ChatMessage, MultilineInput
from src.ui.audio_visualizer import AudioVisualizer
from src.ui.banner import BannerGlitchWidget, ProgressiveStaticBackground
from src.ui.glitch_button import GlitchButton
from src.ui.status_decrypt import StatusDecryptWidget, get_entity_status_text

if TYPE_CHECKING:
    from src.core.di import ServiceContainer

from .actions import (
    ClipboardActionsMixin,
    MenuActionsMixin,
    VisionActionsMixin,
    VoiceActionsMixin,
)
from .event_handlers import EventHandlerMixin
from .lifecycle import LifecycleMixin
from .state_manager import StateManager
from .threading_setup import ThreadingSetupMixin
from .ui_helpers import UIHelpersMixin

logger = logging.getLogger(__name__)


def _get_entity_css_path():
    from src.core.entity_loader import get_active_entity

    entity_id = get_active_entity()
    css_path = config.ENTITIES_DIR / entity_id / f"templo_de_{entity_id}.css"
    if css_path.exists():
        return css_path
    return config.ENTITIES_DIR / "luna" / "templo_de_luna.css"


class TemploDaAlma(
    EventHandlerMixin,
    LifecycleMixin,
    UIHelpersMixin,
    ThreadingSetupMixin,
    MenuActionsMixin,
    VoiceActionsMixin,
    VisionActionsMixin,
    ClipboardActionsMixin,
    App,
):
    CSS_PATH = _get_entity_css_path()
    TITLE = "Templo da Alma"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("escape", "voltar", "Voltar"),
        ("ctrl+q", "quit", "Sair"),
        ("ctrl+t", "nova_conversa", "Nova Conversa"),
        ("ctrl+n", "nova_conversa", "Nova Conversa"),
        ("f5", "nova_conversa", "Nova Conversa"),
        ("ctrl+h", "ver_historico", "Historico"),
        ("ctrl+e", "editar_alma", "Editar Alma"),
        ("ctrl+c", "copy", "Copiar"),
        ("ctrl+v", "paste", "Colar"),
        ("ctrl+a", "select_all", "Selecionar Tudo"),
        ("left", "focus_previous", "Anterior"),
        ("right", "focus_next", "Proximo"),
        ("up", "focus_previous", "Anterior"),
        ("down", "focus_next", "Proximo"),
    ]

    app_state = reactive("IDLE")
    em_chamada = reactive(False)

    def __init__(
        self,
        container: ServiceContainer | None = None,
        consciencia: Any = None,
        boca: Any = None,
        visao: Any = None,
        ouvido: Any = None,
    ):
        super().__init__()
        self._container = container
        self.state = StateManager()

        self.animation_controller = self._create_animation_controller()
        self.session_manager = self._create_session_manager()
        self.file_handler = FileAttachmentHandler(self)

        self.ui_controller = UIController(self)
        self.threading_controller = ThreadingController(self)
        self.audio_controller = AudioController(self)

        self.last_rendered_frame = ""
        self._ultimo_embedding_desconhecido = None
        self.olhar_timer = None
        self.is_looping_olhar = False
        self.is_speaking = False
        self._last_esc_time = 0
        self._esc_double_threshold = 0.5

        logger.info("Inicializando modulos centrais...")
        self.consciencia = consciencia if consciencia is not None else self._create_consciencia()
        self.boca = boca if boca is not None else self._create_boca()
        self.visao = visao if visao is not None else self._create_visao()
        self.ouvido = ouvido if ouvido is not None else self._create_ouvido()
        logger.info("Modulos centrais inicializados.")

        self.metrics = get_metrics()
        logger.info("Sistema de metricas ativo")

        self.onboarding = OnboardingProcess(self)
        self.static_background = ProgressiveStaticBackground(self)
        self.skip_onboarding = False
        self.daemon = None
        self.desktop_integration = None

    def _get_factory(self, factory_name: str) -> Any | None:
        if self._container is None:
            return None
        try:
            return self._container.try_resolve(factory_name)
        except Exception:
            return None

    def _create_consciencia(self) -> Consciencia:
        factory = self._get_factory("consciencia_factory")
        if factory:
            return factory(self)
        return Consciencia(self)

    def _create_boca(self) -> Boca:
        factory = self._get_factory("boca_factory")
        if factory:
            return factory()
        return Boca()

    def _create_visao(self) -> Visao:
        factory = self._get_factory("visao_factory")
        if factory:
            return factory()
        return Visao()

    def _create_ouvido(self) -> OuvidoSussurrante | None:
        factory = self._get_factory("ouvido_factory")
        if factory:
            result = factory()
            if result:
                logger.info("Modulo de audicao inicializado via DI.")
            return result

        if VOICE_AVAILABLE:
            try:
                logger.info("Inicializando modulo de audicao (OuvidoSussurrante)...")
                ouvido = OuvidoSussurrante()
                logger.info("Modulo de audicao inicializado com sucesso.")
                return ouvido
            except Exception as e:
                logger.error(f"Erro fatal ao inicializar OuvidoSussurrante: {e}", exc_info=True)
                return None
        else:
            logger.warning("Modulo de audicao (Whisper) nao disponivel. Funcionalidade de voz desabilitada.")
            return None

    def _create_animation_controller(self) -> AnimationController:
        factory = self._get_factory("animation_controller_factory")
        if factory:
            return factory(self)
        return AnimationController(self)

    def _create_session_manager(self) -> SessionManager:
        factory = self._get_factory("session_manager_factory")
        if factory:
            return factory(self)
        return SessionManager(self)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="ascii-container"):
                yield BannerGlitchWidget(id="welcome-pane")
                yield AudioVisualizer(id="audio-visualizer", classes="hidden")

                with Horizontal(id="status-area"):
                    yield StatusDecryptWidget(initial_text="", id="status-label", classes="status-hidden")
                    yield StatusDecryptWidget(initial_text=get_entity_status_text(), id="emotion-label")

                yield Static("", id="ascii-pane")
            with Vertical(id="right-pane"):
                with Horizontal(id="menu-pane"):
                    yield GlitchButton("Confissao", id="nova_conversa", classes="menu-button")
                    yield GlitchButton("Relicario", id="ver_historico", classes="menu-button")
                    yield GlitchButton("Custodia", id="editar_alma", classes="menu-button")
                    yield GlitchButton("Ver", id="olhar", classes="menu-button")
                    yield GlitchButton("Canone", id="canone", classes="menu-button")
                    yield GlitchButton("Requiem", id="quit", classes="menu-button")
                with Vertical(id="chat-area"):
                    yield VerticalScroll(id="chat-list")
                with Horizontal(id="input-container"):
                    yield GlitchButton("+", id="attach_file")
                    yield GlitchButton("Voz", id="toggle_voice_call", variant="default", disabled=not self.ouvido)
                    yield MultilineInput(placeholder="Sua proxima fala...", id="main_input")

    @property
    def conversation_history(self):
        return self.session_manager.conversation_history

    @conversation_history.setter
    def conversation_history(self, value):
        self.session_manager.conversation_history = value

    @property
    def current_session_id(self):
        return self.session_manager.current_session_id

    @current_session_id.setter
    def current_session_id(self, value):
        self.session_manager.current_session_id = value

    @property
    def attached_file_content(self):
        return self.file_handler.attached_file_content

    @attached_file_content.setter
    def attached_file_content(self, value):
        self.file_handler.attached_file_content = value

    @property
    def attached_file_path(self):
        return self.file_handler.attached_file_path

    @attached_file_path.setter
    def attached_file_path(self, value):
        self.file_handler.attached_file_path = value

    @property
    def attached_root_dir(self):
        return self.file_handler.attached_root_dir

    @attached_root_dir.setter
    def attached_root_dir(self, value):
        self.file_handler.attached_root_dir = value

    @property
    def is_animating(self):
        return self.animation_controller.is_animating

    @is_animating.setter
    def is_animating(self, value):
        self.animation_controller.is_animating = value

    @property
    def animations(self):
        return self.animation_controller.animations

    def run_animation(self, sentiment: str) -> None:
        self.animation_controller.run_animation(sentiment)

    def submit_interaction(
        self,
        text: str,
        visual_context: str = None,
        attached_content: str = None,
        silent: bool = False,
        already_in_chat: bool = False,
        forced_animation: str = None,
    ) -> None:
        evt_logger = get_event_logger()
        evt_logger.input(
            "interaction",
            "submit",
            text_len=len(text),
            details={
                "has_visual": visual_context is not None,
                "has_attachment": attached_content is not None,
                "silent": silent,
            },
        )

        if not hasattr(self, "threading_manager"):
            evt_logger.error("interaction", "submit", "threading_manager_nao_inicializado")
            logger.error("Threading manager nao inicializado")
            return

        result = TranscriptionResult(
            text=text,
            confidence=1.0,
            timestamp=time.time(),
            metadata={
                "visual_context": visual_context,
                "attached_content": attached_content,
                "silent": silent,
                "already_in_chat": already_in_chat,
                "forced_animation": forced_animation,
            },
        )

        try:
            self.threading_manager.transcription_queue.put(result, timeout=1.0)
            logger.info("Interacao enviada para processamento.")
        except Exception as e:
            logger.error(f"Erro ao enviar interacao: {e}")
            self.add_chat_entry("kernel", "Erro: Sistema sobrecarregado.")

    def _update_ascii_pane(self, content) -> None:
        self.query_one("#ascii-pane").update(content)
        if isinstance(content, Text):
            self.last_rendered_frame = content.plain
        else:
            self.last_rendered_frame = str(content)

    def add_chat_entry(self, role: str, content: str = "", parts: list = None, restore: bool = False) -> None:
        if not parts and content:
            parts = [("text", content, None)]

        if not parts:
            return

        if not restore and role in ["user", "luna"]:
            self.conversation_history.append({"role": role, "parts": parts})
            self.session_manager.on_message_added(role)

        try:
            chat_list = self.query_one("#chat-list")
            if not chat_list.is_attached:
                logger.warning("chat-list nao esta montado, agendando para depois")
                self.call_later(self.add_chat_entry, role, content, parts, restore)
                return

            user_name = self.get_user_name() if role == "user" else None
            msg = ChatMessage(role, parts, user_name=user_name)
            if threading.get_ident() == self._thread_id:
                self.call_later(chat_list.mount, msg)
                self.call_later(chat_list.scroll_end, animate=False)
            else:
                self.call_from_thread(chat_list.mount, msg)
                self.call_from_thread(chat_list.scroll_end, animate=False)
        except Exception as e:
            logger.warning(f"Erro ao adicionar chat entry, reagendando: {e}")
            self.call_later(self.add_chat_entry, role, content, parts, restore)

    def _parse_markdown(self, text: str) -> list:
        parts = []
        regex = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        last_idx = 0
        matches = list(regex.finditer(text))

        logger.debug(f"_parse_markdown: Encontrou {len(matches)} blocos de codigo no texto")

        for match in matches:
            pre_text = text[last_idx : match.start()].strip()
            if pre_text:
                parts.append(("text", pre_text, None))

            lang = match.group(1) or "text"
            code = match.group(2).strip()
            logger.debug(f"Bloco de codigo detectado: lang={lang}, tamanho={len(code)} chars")
            parts.append(("code", code, lang))
            last_idx = match.end()

        remaining = text[last_idx:].strip()
        if remaining:
            parts.append(("text", remaining, None))

        logger.debug(f"_parse_markdown: Total de {len(parts)} partes (texto + codigo)")
        return parts

    async def falar(self, texto: str) -> None:
        self.add_chat_entry("luna", texto)
        if self.boca:
            self.is_speaking = True
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.boca.falar, texto)
            finally:
                self.is_speaking = False
            await asyncio.sleep(1.0)
