import logging
import queue
import re
import time

from src.core.profiler import get_pipeline_logger

from .constants import RE_ACTION, RE_CODE_BLOCK

logger = logging.getLogger(__name__)
plog = get_pipeline_logger()


class CoordinatorThread:
    def __init__(self, threading_manager, app):
        self.manager = threading_manager
        self.app = app
        self._app_mounted = True

        logger.info("CoordinatorThread configurado")

    def _safe_call_from_thread(self, callback, *args, **kwargs):
        if self.manager.shutdown_event.is_set() or not self._app_mounted:
            logger.debug("Shutdown em andamento, ignorando call_from_thread")
            return False
        try:
            self.app.call_from_thread(callback, *args, **kwargs)
            return True
        except Exception as e:
            if "mount" in str(e).lower() or "shutdown" in str(e).lower():
                self._app_mounted = False
                logger.debug(f"App desmontado, ignorando chamadas subsequentes: {e}")
            else:
                logger.debug(f"Erro em call_from_thread: {e}")
            return False

    def _extract_actions(self, text: str) -> tuple:
        actions = RE_ACTION.findall(text)
        clean_text = RE_ACTION.sub("", text).strip()
        clean_text = re.sub(r"\s{2,}", " ", clean_text)
        clean_text = re.sub(r"\n\s*\n", "\n", clean_text)
        return clean_text, actions

    def run(self):
        logger.info("Coordinator thread rodando...")

        while not self.manager.shutdown_event.is_set():
            try:
                response = self.manager.response_queue.get(timeout=0.3)

                if response is None:
                    logger.debug("Sentinel recebido, finalizando CoordinatorThread")
                    break

                if self.manager.interrupt_event.is_set():
                    logger.debug("Resposta descartada (interrupcao)")
                    continue

                animacao_nome = response.animacao
                for entity_prefix in ["Luna_", "Juno_", "Eris_", "Lars_"]:
                    animacao_nome = animacao_nome.replace(entity_prefix, "")
                animacao_nome = animacao_nome.replace(".txt", "")
                logger.info(f"[COORD] Processando resposta: animacao={animacao_nome}")

                logger.debug(f"[COORD] log_terminal: {response.log_terminal[:100]}...")
                clean_text, actions = self._extract_actions(response.log_terminal)

                for action in actions:
                    self._safe_call_from_thread(self.app.add_chat_entry, "kernel", f"[{action}]")

                parts = self._parse_markdown(clean_text)

                text_parts = []
                for type_, content, lang in parts:
                    if type_ == "text":
                        text_parts.append((type_, content, lang))
                    elif type_ == "code":
                        if text_parts:
                            self._safe_call_from_thread(self.app.add_chat_entry, "luna", parts=text_parts)
                            text_parts = []
                        self._safe_call_from_thread(self.app.add_chat_entry, "code", parts=[(type_, content, lang)])

                if text_parts:
                    logger.info(f"[COORD] Adicionando {len(text_parts)} partes ao chat")
                    self._safe_call_from_thread(self.app.add_chat_entry, "luna", parts=text_parts)
                else:
                    logger.warning("[COORD] Nenhuma parte de texto para adicionar ao chat")

                if response.fala_tts and getattr(self.app, "em_chamada", False):
                    from src.soul.threading_manager import TTSChunk

                    tts_chunk = TTSChunk(
                        audio_data=response.fala_tts.encode("utf-8"),
                        chunk_index=0,
                        total_chunks=1,
                    )
                    tts_chunk.metatags = response.tts_config
                    tts_chunk.text = response.fala_tts

                    try:
                        self.manager.tts_queue.put(tts_chunk, timeout=1.0)
                    except queue.Full:
                        logger.warning("TTS queue cheia")

                if response.metadata.get("comando_visao", False):
                    logger.info("[COORD] comando_visao=true detectado, disparando visao...")
                    self._handle_vision_request(response.fala_tts)

                current_sentiment = animacao_nome

                async def _finish_and_animate():
                    import asyncio

                    from src.ui.banner import run_processing_static

                    await run_processing_static(self.app, on=False)

                    try:
                        emotion_label = self.app.query_one("#emotion-label")
                        if hasattr(emotion_label, "stop_chaos_mode"):
                            emotion_label.stop_chaos_mode(current_sentiment)
                    except Exception as e:
                        logger.debug(f"Erro ao parar chaos mode: {e}")

                    self.app.run_animation(current_sentiment)

                    await asyncio.sleep(0.5)

                    self.app.app_state = "IDLE"
                    try:
                        lbl = self.app.query_one("#status-label")
                        if hasattr(lbl, "set_text"):
                            lbl.set_text("", animate=False)
                        else:
                            lbl.update("")
                        lbl.add_class("status-hidden")
                        lbl.remove_class("status-visible")
                    except Exception as e:
                        logger.debug(f"Erro ao atualizar status label: {e}")

                self._safe_call_from_thread(
                    lambda: self.app.run_worker(_finish_and_animate(), exclusive=False, thread=False)
                )

                plog.end_interaction(response.fala_tts[:50] if response.fala_tts else "")

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro em coordinator thread: {e}", exc_info=True)

        logger.info("Coordinator thread finalizado")

    def _handle_vision_request(self, initial_response: str):
        import threading as th

        def vision_worker():
            try:
                if not hasattr(self.app, "visao") or not self.app.visao:
                    logger.warning("[COORD] Visao nao disponivel")
                    return

                async def _run_fullscreen():
                    from src.ui.banner import run_fullscreen_piscando

                    await run_fullscreen_piscando(self.app, duration=2.5)

                if self.manager.shutdown_event.is_set() or not self._app_mounted:
                    return
                try:
                    self.app.call_from_thread(
                        lambda: self.app.run_worker(_run_fullscreen(), exclusive=False, thread=False)
                    )
                except Exception as e:
                    logger.debug(f"Erro ao iniciar fullscreen: {e}")
                    return

                time.sleep(0.3)

                descricao = self.app.visao.olhar_agora()

                if descricao and "erro" not in descricao.lower():
                    from src.soul.threading_manager import TranscriptionResult

                    silent_request = TranscriptionResult(
                        text=f"Descreva o que você viu: {descricao}",
                        timestamp=time.time(),
                        metadata={"visual_context": descricao, "silent": True, "already_in_chat": True},
                    )

                    try:
                        self.manager.transcription_queue.put(silent_request, timeout=1.0)
                        logger.info(f"[COORD] Visao enfileirada: {descricao[:50]}...")
                    except queue.Full:
                        logger.warning("[COORD] Fila de transcricao cheia")
                        if not self.manager.shutdown_event.is_set() and self._app_mounted:
                            try:
                                self.app.call_from_thread(self.app.add_chat_entry, "luna", descricao)
                            except Exception as e:
                                logger.debug(f"Erro ao adicionar visao ao chat: {e}")
                else:
                    logger.warning(f"[COORD] Visao falhou: {descricao}")

            except Exception as e:
                logger.error(f"[COORD] Erro ao processar visao: {e}", exc_info=True)

        thread = th.Thread(target=vision_worker, daemon=True, name="vision-handler")
        thread.start()

    def _parse_markdown(self, text: str) -> list:
        text = text.replace("\\n", "\n")

        parts = []
        last_idx = 0
        matches = list(RE_CODE_BLOCK.finditer(text))

        for match in matches:
            pre_text = text[last_idx : match.start()].strip()
            if pre_text:
                parts.append(("text", pre_text, None))

            lang = match.group(1) or "text"
            code = match.group(2).strip()
            parts.append(("code", code, lang))
            last_idx = match.end()

        remaining = text[last_idx:].strip()
        if remaining:
            parts.append(("text", remaining, None))

        return parts
