import asyncio
import logging
import time
from typing import TYPE_CHECKING

from textual import work

from src.core.event_logger import get_event_logger
from src.soul.personalidade import get_personalidade
from src.ui.banner import run_fullscreen_piscando

if TYPE_CHECKING:
    from ..luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class VisionActionsMixin:
    async def action_olhar(self: "TemploDaAlma") -> None:
        evt_logger = get_event_logger()

        if not self.visao:
            evt_logger.vision("capture", success=False, error_msg="modulo_visao_indisponivel")
            logger.error("Modulo de visao nao disponivel.")
            self.add_chat_entry("kernel", "Modulo de visao nao disponivel.")
            return

        onboarding_active = hasattr(self, "onboarding") and getattr(self.onboarding, "is_running", False)

        if self.app_state != "IDLE" and not onboarding_active:
            evt_logger.vision("capture", success=False, error_msg="app_busy")
            logger.warning("App ocupado, ignorando captura de visao.")
            return

        if self.is_speaking or (
            hasattr(self, "threading_manager") and self.threading_manager.luna_speaking_event.is_set()
        ):
            self._interrupt_luna("botao ver")

        evt_logger.vision("capture_started", success=True)
        logger.info("Botao Ver clicado - capturando e processando imagem")
        self.add_chat_entry("kernel", "Abrindo os olhos...")
        self._perform_vision_capture()

    @work(exclusive=False, thread=False)
    async def _perform_vision_capture(self: "TemploDaAlma") -> None:
        self.app_state = "BUSY"

        try:
            capture_task = asyncio.get_event_loop().run_in_executor(None, self.visao.olhar_agora)

            await run_fullscreen_piscando(self, duration=2.5)

            descricao = await capture_task

            if descricao and "erro" not in descricao.lower():
                self.add_chat_entry("kernel", f"[Visao] {descricao}")
                self.submit_interaction("O que voce ve?", visual_context=descricao, silent=True, already_in_chat=True)
            elif descricao and "erro" in descricao.lower():
                logger.warning(f"Visao retornou erro: {descricao}")
                self.add_chat_entry("kernel", "Modelo de visao ocupado. Tente novamente.")
            else:
                self.add_chat_entry("kernel", "Nao consegui processar a imagem.")

        except Exception as e:
            logger.error(f"Erro na captura de visao: {e}", exc_info=True)
            self.add_chat_entry("kernel", f"Erro: {str(e)[:50]}")

        finally:
            self.app_state = "IDLE"
            await asyncio.sleep(0.1)
            try:
                self.animation_controller.run_animation("observando")
            except Exception as e:
                logger.error(f"Erro ao restaurar animacao: {e}")

    @work(exclusive=False, thread=True)
    def _perform_vision_task_single(self: "TemploDaAlma") -> None:
        if self.app_state != "IDLE":
            logger.debug("App ocupado, ignorando captura.")
            return

        self.app_state = "BUSY"

        try:
            logger.info("Luna tirando foto unica...")
            self.call_from_thread(self.animation_controller.run_fullscreen_animation, "piscando")

            time.sleep(0.3)

            houve_mudanca, motivo, descricao, pessoas = self.visao.olhar_inteligente()

            self.call_from_thread(self.animation_controller.end_fullscreen)

            if descricao:
                contexto_pessoas = ""
                if pessoas:
                    nomes = [p["nome"] for p in pessoas]
                    conhecidos = [n for n in nomes if n != "Desconhecido"]
                    if conhecidos:
                        contexto_pessoas = f"Pessoas: {', '.join(conhecidos)}. "

                visual_context = f"{contexto_pessoas}{descricao}"
                self.submit_interaction("O que voce ve?", visual_context=visual_context, silent=True)
            else:
                personalidade = get_personalidade()
                self.add_chat_entry("kernel", personalidade.obter_frase("sem_mudancas_visuais"))
                self.app_state = "IDLE"
                self.call_from_thread(self.run_animation, "observando")

        except Exception as e:
            logger.error(f"Erro na captura unica: {e}", exc_info=True)
            self.add_chat_entry("kernel", f"Erro ao olhar: {str(e)[:50]}")
            self.app_state = "IDLE"
            self.call_from_thread(self.animation_controller.end_fullscreen)
            self.call_from_thread(self.run_animation, "observando")

    def _olhar_loop_tick(self: "TemploDaAlma") -> None:
        if not self.is_looping_olhar:
            logger.debug("Loop de olhar foi cancelado, parando tick.")
            if self.olhar_timer:
                self.olhar_timer.stop()
                self.olhar_timer = None
            return

        if self.app_state != "IDLE":
            logger.debug("Pulando tick de olhar pois App esta BUSY.")
            return

        logger.info("Tick de olhar: Iniciando captura...")
        self._perform_vision_task()

    @work(exclusive=False, thread=True)
    def _perform_vision_task(self: "TemploDaAlma") -> None:
        if not self.is_looping_olhar:
            logger.debug("Loop cancelado antes de executar visao.")
            return

        if self.app_state != "IDLE":
            logger.debug("App ocupado, pulando captura de visao.")
            return

        self.app_state = "BUSY"

        try:
            logger.info("Luna piscando antes de capturar (FULLSCREEN)...")
            self.call_from_thread(self.animation_controller.run_fullscreen_animation, "piscando")

            time.sleep(0.3)

            houve_mudanca, motivo, descricao, pessoas = self.visao.olhar_inteligente()

            if not self.is_looping_olhar:
                self.app_state = "IDLE"
                self.call_from_thread(self.animation_controller.end_fullscreen)
                self.call_from_thread(self.run_animation, "observando")
                return

            if houve_mudanca:
                logger.info(f"Mudanca detectada: {motivo}")

                contexto_pessoas = ""
                if pessoas:
                    nomes = [p["nome"] for p in pessoas]
                    conhecidos = [n for n in nomes if n != "Desconhecido"]
                    desconhecidos = sum(1 for n in nomes if n == "Desconhecido")

                    if conhecidos:
                        contexto_pessoas = f"Pessoas conhecidas: {', '.join(conhecidos)}. "
                    if desconhecidos > 0:
                        contexto_pessoas += f"Rostos desconhecidos: {desconhecidos}. "

                if "rosto_desconhecido" in motivo:
                    self.add_chat_entry("kernel", "Rosto desconhecido detectado!")
                    prompt = "Ha alguem novo aqui. Voce pode perguntar quem e."
                    desconhecidos_lista = [p for p in pessoas if p.get("eh_novo")]
                    if desconhecidos_lista and "embedding" in desconhecidos_lista[0]:
                        self._ultimo_embedding_desconhecido = desconhecidos_lista[0]["embedding"]
                        logger.info("Embedding do rosto desconhecido salvo para registro futuro")
                elif "pessoa_entrou" in motivo:
                    pessoa = motivo.split(":")[1] if ":" in motivo else "alguem"
                    self.add_chat_entry("kernel", f"{pessoa} entrou na cena")
                    prompt = f"{pessoa} acabou de aparecer. Cumprimente."
                elif "pessoa_saiu" in motivo:
                    pessoa = motivo.split(":")[1] if ":" in motivo else "alguem"
                    self.add_chat_entry("kernel", f"{pessoa} saiu da cena")
                    prompt = f"{pessoa} saiu. Voce pode comentar."
                elif "mudanca_cenario" in motivo or "mudanca_visual" in motivo:
                    self.add_chat_entry("kernel", "Mudanca significativa na cena")
                    prompt = "O cenario mudou. O que voce ve agora?"
                else:
                    prompt = "O que voce ve?"

                visual_context = f"{contexto_pessoas}{descricao}"
                self.submit_interaction(prompt, visual_context=visual_context, silent=True)
            else:
                logger.debug("Frame capturado, sem mudancas significativas.")
                self.app_state = "IDLE"
                self.call_from_thread(self.animation_controller.end_fullscreen)
                self.call_from_thread(self.run_animation, "observando")

        except Exception as e:
            logger.error(f"Erro no loop de visao: {e}", exc_info=True)
            self.app_state = "IDLE"
            self.call_from_thread(self.animation_controller.end_fullscreen)
            self.call_from_thread(self.run_animation, "observando")
