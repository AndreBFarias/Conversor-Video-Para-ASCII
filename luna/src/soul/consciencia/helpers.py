from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

import config
from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.core.metricas import TimerContext
from src.core.router import Intent, get_model_for_intent
from src.soul.model_helpers import remove_emojis

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def validate_schema(consciencia: Consciencia, data: dict) -> bool:
    required = ["fala_tts", "log_terminal", "animacao", "comando_visao"]
    for field in required:
        if field not in data:
            logger.error(f"Campo obrigatorio ausente: {field}")
            return False

    if "fala_tts" in data:
        data["fala_tts"] = remove_emojis(data["fala_tts"])
    if "log_terminal" in data:
        data["log_terminal"] = remove_emojis(data["log_terminal"])
    if "leitura" in data:
        data["leitura"] = remove_emojis(data["leitura"])

    if data["animacao"] not in config.ANIMATION_TO_EMOTION:
        entity_name = get_entity_name(consciencia.active_entity_id)
        default_anim = f"{entity_name}_observando"
        logger.warning(f"Animacao invalida: {data['animacao']}, usando '{default_anim}'")
        data["animacao"] = default_anim

    if not isinstance(data["comando_visao"], bool):
        data["comando_visao"] = False

    return True


def fallback_response(consciencia: Consciencia, error_msg: str = None, forced_animation: str = None) -> dict:
    entity_name = get_entity_name(consciencia.active_entity_id)
    default_anim = f"{entity_name}_observando"
    animacao = (
        forced_animation if forced_animation and forced_animation in config.ANIMATION_TO_EMOTION else default_anim
    )
    return {
        "fala_tts": "Hmm, tive um problema tecnico. Pode repetir?",
        "leitura": "Confusa",
        "log_terminal": f"[{entity_name} franze a testa] Hmm, tive um problema tecnico... {error_msg or ''}",
        "animacao": animacao,
        "comando_visao": False,
        "tts_config": {"speed": 1.0, "stability": 0.5},
        "registrar_rosto": None,
        "filesystem_ops": [],
    }


def get_model_for_intent_routing(consciencia: Consciencia, intent: Intent) -> tuple:
    original_model = consciencia.model_name
    target_model = get_model_for_intent(intent)

    if intent == Intent.CODE and consciencia.provider == "local":
        code_model = config.CODE_LOCAL.get("model", "qwen2.5-coder:7b")
        if code_model != original_model:
            if consciencia.ollama_client:
                try:
                    installed = consciencia.ollama_client.list_models()
                    if any(code_model in m for m in installed):
                        logger.info(
                            f"[ROUTER] Intent CODE detectado, trocando modelo: {original_model} -> {code_model}"
                        )
                        return code_model, original_model
                    else:
                        logger.warning(f"[ROUTER] Modelo {code_model} nao instalado, usando {original_model}")
                except Exception as e:
                    logger.debug(f"[ROUTER] Erro ao verificar modelo: {e}")
    return original_model, original_model


def compress_conversation(consciencia: Consciencia) -> None:
    if len(consciencia.conversation_history) <= consciencia._compression_threshold:
        return

    if not consciencia._has_provider():
        consciencia.conversation_history = consciencia.conversation_history[-10:]
        logger.info("Historico truncado (modo offline)")
        return

    to_summarize = consciencia.conversation_history[:10]
    summary_parts = []
    for turn in to_summarize:
        u = turn.get("user", "")
        l = turn.get("luna", {}).get("fala_tts", "")
        if u:
            summary_parts.append(f"U: {u[:50]}")
        if l:
            summary_parts.append(f"L: {l[:50]}")

    summary_text = " | ".join(summary_parts)
    summary_prompt = f"Resuma a essencia destas interacoes como uma confissao sombria de uma linha: {summary_text}"

    try:
        if consciencia.provider == "local" and consciencia.ollama_client:
            response = consciencia.ollama_client.generate(
                prompt=summary_prompt, model=consciencia.model_name, max_tokens=256
            )
            summary_text_result = response.text if not response.error else ""
        else:
            summary_res = consciencia.gemini_client.models.generate_content(
                model=consciencia.model_name, contents=summary_prompt
            )
            summary_text_result = summary_res.text

        compressed_entry = {
            "user": "Sagrario",
            "luna": {"fala_tts": f"Lembro-me da nossa confissao: {summary_text_result[:200]}"},
            "timestamp": datetime.now().isoformat(),
        }
        consciencia.conversation_history = [compressed_entry] + consciencia.conversation_history[10:]
        logger.info(f"Historico compactado: {len(to_summarize)} entradas -> 1 resumo")
    except Exception as e:
        logger.warning(f"Falha ao compactar historico: {e}")
