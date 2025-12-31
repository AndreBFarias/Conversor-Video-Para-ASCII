from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import config
from src.core.logging_config import get_logger
from src.core.terminal_executor import parse_natural_command

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def post_process_response(
    consciencia: Consciencia,
    data: dict,
    user_text: str,
    attached_content: str | None,
    forced_animation: str | None,
) -> dict:
    from src.soul.consciencia.helpers import compress_conversation
    from src.soul.consciencia.memory import save_to_memory, update_memory_tiers
    from src.soul.consciencia.web_search import process_web_search

    pesquisa_web = data.get("pesquisa_web")
    if pesquisa_web and isinstance(pesquisa_web, str) and len(pesquisa_web) > 2:
        logger.info(f"Pesquisa web detectada: '{pesquisa_web}'")
        data = process_web_search(consciencia, data, pesquisa_web, user_text)

    has_document = attached_content is not None and len(attached_content) > 100
    max_chars = config.DOC_RESPONSE_MAX_CHARS if has_document else config.RESPONSE_MAX_CHARS

    if len(data.get("log_terminal", "")) > max_chars:
        data["log_terminal"] = data["log_terminal"][:max_chars] + "\n\n[...truncado]"
        logger.info(f"Resposta truncada para {max_chars} chars")

    data = execute_filesystem_ops(consciencia, data, user_text)

    if forced_animation and forced_animation in config.ANIMATION_TO_EMOTION:
        logger.info(f"Forcando animacao via comando: {forced_animation}")
        data["animacao"] = forced_animation

    save_to_memory(consciencia, user_text, data)
    update_history(consciencia, user_text, data)
    update_personality_anchor(consciencia, data)
    update_memory_tiers(consciencia, user_text, data)

    if consciencia.api_optimizer:
        consciencia.api_optimizer.cache_response(user_text, data, None)

    return data


def execute_filesystem_ops(consciencia: Consciencia, data: dict, user_text: str) -> dict:
    filesystem_ops = data.get("filesystem_ops", [])
    if filesystem_ops and isinstance(filesystem_ops, list):
        cmd_results = []
        for cmd in filesystem_ops[:5]:
            if isinstance(cmd, str) and cmd.strip():
                exit_code, stdout, stderr = consciencia.terminal_executor.execute(cmd, timeout=30)
                if exit_code == 0:
                    cmd_results.append(f"$ {cmd}\n{stdout[:200]}")
                else:
                    cmd_results.append(f"$ {cmd}\n[ERRO] {stderr[:100]}")
                logger.info(f"Terminal: {cmd} -> exit={exit_code}")

        if cmd_results:
            data["log_terminal"] += "\n\n--- TERMINAL ---\n" + "\n".join(cmd_results)

    natural_cmd = parse_natural_command(user_text)
    if natural_cmd and not filesystem_ops:
        exit_code, stdout, stderr = consciencia.terminal_executor.execute(natural_cmd, timeout=30)
        if exit_code == 0:
            data["log_terminal"] += f"\n\n--- TERMINAL ---\n$ {natural_cmd}\n{stdout[:300]}"
            logger.info(f"Comando natural executado: {natural_cmd}")
        else:
            data["log_terminal"] += f"\n\n--- TERMINAL ---\n$ {natural_cmd}\n[ERRO] {stderr[:150]}"

    return data


def update_history(consciencia: Consciencia, user_text: str, data: dict) -> None:
    from src.soul.consciencia.helpers import compress_conversation

    consciencia.conversation_history.append(
        {
            "user": user_text,
            "luna": data,
            "timestamp": datetime.now().isoformat(),
        }
    )
    compress_conversation(consciencia)

    if len(consciencia.conversation_history) > 50:
        consciencia.conversation_history = consciencia.conversation_history[-50:]


def update_personality_anchor(consciencia: Consciencia, data: dict) -> None:
    response_tts = data.get("fala_tts", "")
    drift_result = consciencia.personality_anchor.check_response_drift(response_tts)
    if drift_result["drifted"]:
        logger.warning(f"Drift de personalidade detectado: {drift_result['violations']}")

    consciencia.personality_anchor.update_from_interaction()
