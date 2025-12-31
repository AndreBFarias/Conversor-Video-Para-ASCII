from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def call_llm(consciencia: Consciencia, prompt: str) -> str:
    return consciencia.llm_caller.call(prompt)


def has_provider(consciencia: Consciencia) -> bool:
    return consciencia.llm_caller.has_provider()


def on_llm_fallback(consciencia: Consciencia, from_provider: str, to_provider: str) -> None:
    logger.warning(f"LLM Fallback: {from_provider} -> {to_provider}")
    consciencia.metrics.increment("llm_fallbacks")
    if consciencia.app and hasattr(consciencia.app, "add_chat_entry"):
        try:
            consciencia.app.call_from_thread(
                consciencia.app.add_chat_entry,
                "kernel",
                f"[Fallback: usando {to_provider}]",
            )
        except Exception:
            pass


def call_with_universal_llm(consciencia: Consciencia, prompt: str) -> str:
    if not consciencia._universal_llm:
        raise RuntimeError("UniversalLLM nao inicializado")

    response = consciencia._universal_llm.generate(
        prompt=prompt,
        system=consciencia.system_instruction,
        temperature=0.8,
        max_tokens=1024,
    )

    if response.fallback_used:
        logger.info(f"Resposta via fallback: {response.provider}")

    return response.text


def get_llm_status(consciencia: Consciencia) -> dict[str, Any]:
    if consciencia._universal_llm:
        return consciencia._universal_llm.get_status()
    return {
        "providers": [],
        "active": consciencia.provider,
        "model": consciencia.model_name,
    }


def stream_response(
    consciencia: Consciencia,
    user_text: str,
    visual_context: str | None = None,
    attached_content: str | None = None,
) -> Generator[tuple[str, bool, dict[str, Any] | None], None, None]:
    return consciencia.response_streamer.stream(
        user_text,
        visual_context,
        attached_content,
        consciencia.smart_memory,
        consciencia.conversation_history,
    )
