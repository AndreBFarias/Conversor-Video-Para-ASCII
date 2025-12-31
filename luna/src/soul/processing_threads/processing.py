import logging
import queue
import time
from concurrent.futures import Future, ThreadPoolExecutor

from src.core.entity_loader import get_active_entity, get_entity_name
from src.core.event_logger import get_event_logger
from src.core.profiler import get_pipeline_logger, get_profiler
from src.soul.threading_manager import LunaResponse, ProcessingRequest

from .helpers import sanitize_log

logger = logging.getLogger(__name__)
profiler = get_profiler()
plog = get_pipeline_logger()


class ProcessingThread:
    def __init__(self, threading_manager, consciencia):
        self.manager = threading_manager
        self.consciencia = consciencia
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="gemini")
        self._pending_request: Future | None = None
        self._executor_shutdown = False

        logger.info("ProcessingThread configurado com ThreadPoolExecutor")

    def run(self):
        logger.info("Processing thread rodando (modo paralelo)...")

        while not self.manager.shutdown_event.is_set():
            if self._pending_request and self._pending_request.done():
                try:
                    json_response, request = self._pending_request.result()

                    if json_response and not self.manager.interrupt_event.is_set():
                        entity_name = get_entity_name(get_active_entity())
                        default_anim = f"{entity_name}_observando"
                        response = LunaResponse(
                            fala_tts=json_response.get("fala_tts", ""),
                            log_terminal=json_response.get("log_terminal", ""),
                            animacao=json_response.get("animacao", default_anim),
                            tts_config=json_response.get("tts_config", {}),
                            metadata={
                                "filesystem_ops": json_response.get("filesystem_ops", []),
                                "registrar_rosto": json_response.get("registrar_rosto"),
                                "comando_visao": json_response.get("comando_visao", False),
                            },
                        )

                        try:
                            self.manager.response_queue.put(response, timeout=1.0)
                            logger.info(f"Resposta enfileirada (animacao: {response.animacao})")
                        except queue.Full:
                            logger.warning("Response queue cheia, resposta descartada")
                    elif not json_response:
                        logger.warning("Consciencia retornou None")

                except Exception as e:
                    logger.error(f"Erro ao processar resposta: {e}")
                finally:
                    self._pending_request = None

            try:
                transcription = self.manager.transcription_queue.get(timeout=0.1)

                if transcription is None:
                    logger.debug("Sentinel recebido, finalizando ProcessingThread")
                    break

                if self.manager.interrupt_event.is_set():
                    logger.debug("Processamento cancelado (interrupcao ativa)")
                    continue

                if self.manager.app and hasattr(self.manager.app, "onboarding"):
                    onboarding = self.manager.app.onboarding
                    if onboarding and getattr(onboarding, "is_running", False):
                        if onboarding.input_future and not onboarding.input_future.done():
                            logger.info(f"[ONBOARDING] Interceptando transcricao: '{sanitize_log(transcription.text)}'")
                            self.manager.app.call_from_thread(
                                self.manager.app.add_chat_entry, "user", transcription.text
                            )
                            onboarding.handle_text_input(transcription.text)
                            continue
                        else:
                            logger.debug("[ONBOARDING] Ativo mas sem input_future, ignorando transcricao")
                            continue

                logger.info(f"Processando: '{sanitize_log(transcription.text)}'")
                plog.new_interaction(transcription.text)

                md = getattr(transcription, "metadata", {}) or {}
                is_silent = md.get("silent", False)
                already_in_chat = md.get("already_in_chat", False)

                if self.manager.app and not is_silent and not already_in_chat:
                    try:
                        self.manager.app.call_from_thread(self.manager.app.add_chat_entry, "user", transcription.text)
                    except Exception as e:
                        logger.debug(f"Erro ao adicionar transcricao ao chat: {e}")

                request = ProcessingRequest(
                    user_text=transcription.text,
                    visual_context=md.get("visual_context"),
                    attached_content=md.get("attached_content"),
                    forced_animation=md.get("forced_animation"),
                    timestamp=transcription.timestamp,
                )

                try:
                    self.manager.processing_queue.put(request, timeout=0.5)
                except queue.Full:
                    logger.warning("Processing queue cheia")

                if self._pending_request is None or self._pending_request.done():
                    if self.manager.shutdown_event.is_set() or self._executor_shutdown:
                        logger.debug("Shutdown em andamento, ignorando nova requisicao")
                        continue
                    try:
                        self._pending_request = self._executor.submit(self._process_request, request)
                        logger.debug("Requisicao submetida ao pool")
                    except RuntimeError as e:
                        logger.debug(f"Executor fechado, ignorando requisicao: {e}")
                        self._executor_shutdown = True
                        continue
                else:
                    logger.warning("Processamento anterior em andamento, aguardando conclusao...")
                    try:
                        self._pending_request.result(timeout=10.0)
                    except TimeoutError:
                        logger.warning("Timeout aguardando request anterior, descartando nova")
                        continue
                    except Exception as e:
                        logger.debug(f"Request anterior falhou: {e}")
                    if self.manager.shutdown_event.is_set() or self._executor_shutdown:
                        logger.debug("Shutdown em andamento, ignorando nova requisicao")
                        continue
                    try:
                        self._pending_request = self._executor.submit(self._process_request, request)
                    except RuntimeError as e:
                        logger.debug(f"Executor fechado, ignorando requisicao: {e}")
                        self._executor_shutdown = True
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro em processing thread: {e}", exc_info=True)

        self._executor_shutdown = True
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            logger.debug(f"Erro ao fechar executor: {e}")
        logger.info("Processing thread finalizado")

    def _process_request(self, request: ProcessingRequest):
        if self.manager.shutdown_event.is_set():
            logger.debug("Shutdown detectado em _process_request, abortando")
            return None, request
        try:
            with profiler.span("llm.process", {"input_len": len(request.user_text)}):
                start_time = time.time()
                plog.new_interaction()
                plog.log_stage("llm", f"input: '{request.user_text[:50]}...'")

                json_response = self.consciencia.process_interaction(
                    request.user_text,
                    request.visual_context,
                    request.attached_content,
                    forced_animation=request.forced_animation,
                )

                elapsed = time.time() - start_time

                evt_logger = get_event_logger()
                if json_response:
                    output_len = len(json_response.get("fala_tts", ""))
                    plog.log_stage("llm", "response ready", duration_ms=elapsed * 1000, output_len=output_len)
                    evt_logger.llm(
                        "generate",
                        self.consciencia.provider,
                        success=True,
                        duration_ms=elapsed * 1000,
                        details={"output_len": output_len},
                    )
                else:
                    plog.log_stage("llm", "FAILED", duration_ms=elapsed * 1000)
                    evt_logger.llm("generate", self.consciencia.provider, success=False, duration_ms=elapsed * 1000)

                return json_response, request

        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            evt_logger = get_event_logger()
            evt_logger.llm("generate", "unknown", success=False, error_msg=str(e)[:50])
            return None, request
