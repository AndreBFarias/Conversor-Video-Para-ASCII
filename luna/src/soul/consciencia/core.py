from __future__ import annotations

import json
import threading
import traceback
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from src.app.luna_app import TemploDaAlma

import config
from src.core.entity_loader import get_active_entity, get_entity_name
from src.core.logging_config import get_logger
from src.core.metricas import TimerContext, get_api_tracker, get_metrics, perf_monitor
from src.core.router import detect_intent
from src.data_memory.smart_memory import get_entity_smart_memory, get_smart_memory
from src.soul.json_extractor import get_json_extractor
from src.soul.model_helpers import sanitize_for_log
from src.soul.reminders import create_reminder_from_text, is_reminder_request
from src.soul.response_parser import get_parser
from src.tools.web_search import get_web_search

logger = get_logger(__name__)


class Consciencia:
    def __init__(self, app: TemploDaAlma) -> None:
        from src.soul.api_optimizer import APIOptimizer
        from src.soul.rate_limiter import RequestDeduplicator, SmartRateLimiter
        from src.soul.semantic_cache import SemanticCache

        from src.soul.consciencia.provider_init import init_components, init_provider
        from src.soul.consciencia.services import (
            ActionDispatcher,
            CognitionEngine,
            MemoryController,
        )

        self.app = app
        self.conversation_history = []
        self.metrics = get_metrics()
        self.api_tracker = get_api_tracker()
        self.active_entity_id = get_active_entity()
        self.smart_memory = get_entity_smart_memory(self.active_entity_id)
        self.global_memory = get_smart_memory()
        self._compression_threshold = 15
        self._interaction_count = 0

        self.cognition = CognitionEngine(self)
        self.memory = MemoryController(self)
        self.actions = ActionDispatcher(self)

        self._memory_warmup_thread = threading.Thread(
            target=lambda: self.memory.warmup(), daemon=True, name="MemoryWarmup"
        )
        self._memory_warmup_thread.start()

        rate_cfg = config.RATE_LIMITER_CONFIG
        cache_cfg = config.CACHE_CONFIG
        self.rate_limiter = SmartRateLimiter(
            quota_limit=rate_cfg.get("QUOTA_LIMIT", 60),
            safety_margin=rate_cfg.get("SAFETY_MARGIN", 5),
        )
        self.semantic_cache = SemanticCache(
            similarity_threshold=cache_cfg.get("SIMILARITY_THRESHOLD", 0.85),
            max_size=cache_cfg.get("MAX_SIZE", 100),
            ttl_seconds=cache_cfg.get("TTL_SECONDS", 3600),
        )
        self.deduplicator = RequestDeduplicator(window_seconds=rate_cfg.get("WINDOW_SECONDS", 60))
        self.api_optimizer = None
        self.response_parser = get_parser()
        self.json_extractor = get_json_extractor(self.active_entity_id)
        self.web_search = get_web_search()

        self.cognition.init_soul_prompt()
        init_provider(self)
        init_components(self)

    def _call_llm(self, prompt: str) -> str:
        return self.cognition.call_llm(prompt)

    def _has_provider(self) -> bool:
        return self.cognition.has_provider()

    def reload_for_entity(self, entity_id: str) -> None:
        from src.soul.consciencia.provider_init import reload_for_entity

        reload_for_entity(self, entity_id)
        self.memory.reload_for_entity(entity_id)
        self.cognition.init_soul_prompt()
        self.json_extractor = get_json_extractor(entity_id)

    def get_llm_status(self) -> dict[str, Any]:
        return self.cognition.get_llm_status()

    def get_optimizer_stats(self) -> dict[str, Any]:
        if self.api_optimizer:
            return self.api_optimizer.get_optimization_stats()
        return {}

    def stream_response(
        self,
        user_text: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
    ) -> Generator[tuple[str, bool, dict[str, Any] | None], None, None]:
        return self.cognition.stream_response(user_text, visual_context, attached_content)

    @perf_monitor("consciencia.process_interaction")
    def process_interaction(
        self,
        user_text: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
        forced_animation: str | None = None,
    ) -> dict[str, Any]:
        from src.soul.consciencia.helpers import fallback_response, validate_schema

        if not user_text.strip() and not visual_context:
            return fallback_response(self, "Entrada vazia", forced_animation)

        if is_reminder_request(user_text):
            reminder = create_reminder_from_text(user_text, self.active_entity_id)
            if reminder:
                return self._handle_reminder(reminder)

        if not self._has_provider():
            return self._offline_response(forced_animation)

        self._interaction_count += 1
        has_code_context = attached_content is not None and "```" in str(attached_content)
        intent = detect_intent(user_text, has_image=visual_context is not None, has_code_context=has_code_context)
        logger.info(f"[ROUTER] Intent detectado: {intent.value}")

        target_model, original_model = self.cognition.get_model_for_intent(intent)
        if target_model != original_model:
            self.llm_caller.model_name = target_model

        if self.api_optimizer:
            result = self.api_optimizer.process_request(user_text, visual_context, attached_content)
            if result:
                if target_model != original_model:
                    self.llm_caller.model_name = original_model
                return result

        contexto_memoria = self.memory.build_context(user_text)
        full_prompt = self.cognition.build_full_prompt(user_text, visual_context, attached_content, contexto_memoria)

        try:
            logger.info(f"Processando: '{sanitize_for_log(user_text)}'...")

            with TimerContext(self.metrics, "consciencia.response_time"):
                response_text = self._call_llm(full_prompt)

            self.metrics.increment("consciencia.interactions_total")
            json_text = self.json_extractor.extract(response_text)
            data = json.loads(json_text)

            if not validate_schema(self, data):
                raise ValueError("Schema invalido")

            data = self._post_process(data, user_text, attached_content, forced_animation)

            if target_model != original_model:
                self.llm_caller.model_name = original_model

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Falha no parse JSON: {e}")
            if target_model != original_model:
                self.llm_caller.model_name = original_model
            return fallback_response(self, "Resposta mal formatada", forced_animation)
        except Exception as e:
            logger.error(f"Erro no process_interaction: {e}")
            traceback.print_exc()
            if target_model != original_model:
                self.llm_caller.model_name = original_model
            return fallback_response(self, str(e)[:50], forced_animation)

    def _post_process(
        self,
        data: dict,
        user_text: str,
        attached_content: str | None,
        forced_animation: str | None,
    ) -> dict:
        data = self.actions.dispatch(data, user_text)

        has_document = attached_content is not None and len(attached_content) > 100
        max_chars = config.DOC_RESPONSE_MAX_CHARS if has_document else config.RESPONSE_MAX_CHARS

        if len(data.get("log_terminal", "")) > max_chars:
            data["log_terminal"] = data["log_terminal"][:max_chars] + "\n\n[...truncado]"
            logger.info(f"Resposta truncada para {max_chars} chars")

        if forced_animation and forced_animation in config.ANIMATION_TO_EMOTION:
            logger.info(f"Forcando animacao via comando: {forced_animation}")
            data["animacao"] = forced_animation

        self.memory.save_interaction(user_text, data)
        self._update_history(user_text, data)
        self._update_personality_anchor(data)
        self.memory.update_tiers(user_text, data)

        if self.api_optimizer:
            self.api_optimizer.cache_response(user_text, data, None)

        return data

    def _update_history(self, user_text: str, data: dict) -> None:
        from src.soul.consciencia.helpers import compress_conversation

        self.conversation_history.append(
            {
                "user": user_text,
                "luna": data,
                "timestamp": datetime.now().isoformat(),
            }
        )
        compress_conversation(self)

        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    def _update_personality_anchor(self, data: dict) -> None:
        response_tts = data.get("fala_tts", "")
        drift_result = self.personality_anchor.check_response_drift(response_tts)
        if drift_result["drifted"]:
            logger.warning(f"Drift de personalidade: {drift_result['violations']}")

        self.personality_anchor.update_from_interaction()

    def _handle_reminder(self, reminder) -> dict[str, Any]:
        time_until = reminder.get_time_until()
        if time_until.total_seconds() < 3600:
            time_str = f"{int(time_until.total_seconds() / 60)} minutos"
        elif time_until.total_seconds() < 86400:
            time_str = f"{int(time_until.total_seconds() / 3600)} horas"
        else:
            time_str = f"{int(time_until.total_seconds() / 86400)} dias"

        entity_name = get_entity_name(self.active_entity_id)
        return {
            "fala_tts": f"Anotado. Te aviso em {time_str} sobre: {reminder.message}.",
            "leitura": "Tom confiante e ligeiramente dramatico",
            "log_terminal": f"Lembrete criado: **{reminder.message}** (em {time_str})",
            "animacao": f"{entity_name}_curiosa",
            "comando_visao": False,
            "tts_config": {"speed": 1.0, "stability": 0.5},
            "registrar_rosto": None,
            "filesystem_ops": [],
        }

    def _offline_response(self, forced_animation: str | None) -> dict[str, Any]:
        entity_name = get_entity_name(self.active_entity_id)
        default_anim = f"{entity_name}_observando"
        animacao = (
            forced_animation if forced_animation and forced_animation in config.ANIMATION_TO_EMOTION else default_anim
        )
        return {
            "fala_tts": "Estou em modo offline. Nenhum modelo de linguagem configurado.",
            "leitura": "Tom informativo",
            "log_terminal": f"[Modo Offline] Provider: {self.provider}. Configure GOOGLE_API_KEY ou inicie o Ollama.",
            "animacao": animacao,
            "comando_visao": False,
            "tts_config": {"speed": 1.0, "stability": 0.5},
            "registrar_rosto": None,
            "filesystem_ops": [],
        }
