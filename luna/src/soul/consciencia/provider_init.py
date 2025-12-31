from __future__ import annotations

from typing import TYPE_CHECKING

from google import genai

import config
from src.core.logging_config import get_logger
from src.core.ollama_client import OllamaSyncClient
from src.data_memory.memory_tier_manager import get_tier_manager
from src.data_memory.short_term_memory import get_short_term_memory
from src.data_memory.smart_memory import get_entity_smart_memory
from src.soul.context_builder import get_context_builder
from src.soul.conversation_state import get_conversation_state_machine
from src.soul.entity_hotswap import get_entity_hotswap
from src.soul.json_extractor import get_json_extractor
from src.soul.llm_caller import create_llm_caller
from src.soul.model_helpers import get_user_profile, is_small_model
from src.soul.personalidade import get_personalidade
from src.soul.personality_anchor import get_personality_anchor
from src.soul.personality_guard import get_personality_guard
from src.soul.providers import UniversalLLM, get_universal_llm
from src.soul.response_pipeline import get_response_pipeline
from src.soul.response_streamer import create_response_streamer
from src.soul.system_instructions import get_instruction_builder

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def init_provider(consciencia: Consciencia) -> None:
    consciencia.provider = config.CHAT_PROVIDER
    consciencia.gemini_client = None
    consciencia.ollama_client = None
    consciencia.model_name = None

    soul_prompt = consciencia.cognition.soul_prompt

    if consciencia.provider == "local":
        consciencia.ollama_client = OllamaSyncClient()
        consciencia.model_name = config.CHAT_LOCAL["model"]

        consciencia.instruction_builder = get_instruction_builder(consciencia.active_entity_id, soul_prompt, "local")
        consciencia.system_instruction = consciencia.instruction_builder.build()

        if consciencia.ollama_client.check_health():
            logger.info(f"Ollama [{consciencia.model_name}] inicializado com sucesso")
        else:
            logger.warning("Ollama nao disponivel - tentando fallback para Gemini")
            if config.GOOGLE_API_KEY:
                consciencia.provider = "gemini"
                consciencia.gemini_client = genai.Client(api_key=config.GOOGLE_API_KEY)
                consciencia.model_name = config.GEMINI_CONFIG["MODEL_NAME"]
                consciencia.instruction_builder = get_instruction_builder(
                    consciencia.active_entity_id, soul_prompt, "gemini"
                )
                consciencia.system_instruction = consciencia.instruction_builder.build()
                logger.info(f"Fallback: {consciencia.model_name} ativado")
            else:
                logger.error("Nenhum provider disponivel - modo offline")

    elif consciencia.provider == "gemini" and config.GOOGLE_API_KEY:
        consciencia.gemini_client = genai.Client(api_key=config.GOOGLE_API_KEY)
        consciencia.model_name = config.GEMINI_CONFIG["MODEL_NAME"]

        consciencia.instruction_builder = get_instruction_builder(consciencia.active_entity_id, soul_prompt, "gemini")
        consciencia.system_instruction = consciencia.instruction_builder.build()
        logger.info(f"Gemini [{consciencia.model_name}] inicializado (novo SDK)")

        from src.soul.api_optimizer import APIOptimizer

        consciencia.api_optimizer = APIOptimizer(
            consciencia, consciencia.rate_limiter, consciencia.semantic_cache, consciencia.deduplicator
        )
        logger.info("API Optimizer ativado")
    else:
        logger.warning(f"Provider '{consciencia.provider}' nao configurado - modo offline")
        consciencia.system_instruction = ""

    consciencia.llm_caller = create_llm_caller(
        consciencia.provider,
        consciencia.model_name,
        consciencia.gemini_client,
        consciencia.ollama_client,
        consciencia.app,
    )
    consciencia.llm_caller.set_system_instruction(consciencia.system_instruction)
    if hasattr(consciencia, "instruction_builder"):
        consciencia.llm_caller.set_instruction_builders(
            simple_builder=consciencia.instruction_builder.build_simple,
            ultra_compact_builder=consciencia.instruction_builder.build_ultra_compact,
        )

    consciencia.response_streamer = create_response_streamer(
        consciencia.active_entity_id,
        consciencia.provider,
        consciencia.model_name,
        consciencia.gemini_client,
        consciencia.ollama_client,
        consciencia.system_instruction,
    )


def init_components(consciencia: Consciencia) -> None:
    from src.soul.consciencia.llm_bridge import call_llm, on_llm_fallback

    consciencia.context_builder = get_context_builder(consciencia.active_entity_id)
    consciencia.response_pipeline = get_response_pipeline(consciencia.active_entity_id)
    consciencia.entity_hotswap = get_entity_hotswap()
    consciencia.personality_guard = get_personality_guard(consciencia.active_entity_id)
    consciencia.personality_anchor = get_personality_anchor(consciencia.active_entity_id)
    consciencia.short_term_memory = get_short_term_memory(consciencia.active_entity_id)
    consciencia.memory_tier_manager = get_tier_manager(consciencia.active_entity_id)
    consciencia.state_machine = get_conversation_state_machine()
    consciencia._interaction_count = 0

    consciencia._universal_llm: UniversalLLM | None = None
    consciencia._use_universal_llm = config.CHAT_PROVIDER in ("local", "gemini")
    if consciencia._use_universal_llm:
        try:
            consciencia._universal_llm = get_universal_llm()
            consciencia._universal_llm.set_on_fallback(lambda f, t: on_llm_fallback(consciencia, f, t))
            logger.info(f"UniversalLLM ativado: {consciencia._universal_llm.get_model_name()}")
        except Exception as e:
            logger.warning(f"Falha ao inicializar UniversalLLM: {e}")
            consciencia._universal_llm = None

    consciencia.entity_hotswap.initialize(consciencia.active_entity_id)
    consciencia.response_pipeline.set_llm_caller(lambda p: call_llm(consciencia, p))

    logger.info(f"Pipeline components initialized for {consciencia.active_entity_id}")


def reload_for_entity(consciencia: Consciencia, entity_id: str) -> None:
    logger.info(f"Recarregando consciencia para entidade: {entity_id}")
    consciencia.active_entity_id = entity_id
    consciencia.smart_memory = get_entity_smart_memory(entity_id)
    consciencia.json_extractor = get_json_extractor(entity_id)

    if consciencia.provider == "local":
        old_model = consciencia.model_name
        consciencia.model_name = config.CHAT_LOCAL["model"]
        if old_model != consciencia.model_name:
            logger.info(f"Modelo de chat atualizado: {old_model} -> {consciencia.model_name}")
            consciencia.llm_caller.use_simple_prompt = is_small_model(consciencia.model_name)
            consciencia.llm_caller.json_failures = 0

    consciencia.cognition.init_soul_prompt()
    soul_prompt = consciencia.cognition.soul_prompt

    if soul_prompt:
        logger.info(f"Soul prompt recarregado para entidade: {entity_id}")
    else:
        logger.warning(f"Soul prompt vazio para entidade: {entity_id}")

    consciencia.instruction_builder = get_instruction_builder(entity_id, soul_prompt, consciencia.provider)
    consciencia.system_instruction = consciencia.instruction_builder.build()
    consciencia.llm_caller.set_system_instruction(consciencia.system_instruction)
    consciencia.llm_caller.set_instruction_builders(
        simple_builder=consciencia.instruction_builder.build_simple,
        ultra_compact_builder=consciencia.instruction_builder.build_ultra_compact,
    )

    consciencia.personality_anchor = get_personality_anchor(entity_id)
    consciencia.short_term_memory = get_short_term_memory(entity_id)
    consciencia.memory_tier_manager = get_tier_manager(entity_id)
    logger.info(f"Consciencia recarregada para {entity_id}")
