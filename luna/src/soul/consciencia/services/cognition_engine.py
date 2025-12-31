from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

import config
from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.core.router import Intent

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


class CognitionEngine:
    def __init__(self, consciencia: Consciencia) -> None:
        self._consciencia = consciencia
        self._system_instruction: str = ""
        self._soul_prompt: str = ""

    @property
    def system_instruction(self) -> str:
        return self._system_instruction

    @property
    def soul_prompt(self) -> str:
        return self._soul_prompt

    def init_soul_prompt(self) -> None:
        entity_id = self._consciencia.active_entity_id
        entity_name = get_entity_name(entity_id)
        entity_dir = config.ENTITIES_DIR / entity_id

        alma_path = entity_dir / "alma.txt"
        try:
            if alma_path.exists():
                self._soul_prompt = alma_path.read_text(encoding="utf-8")
                logger.info(f"Alma de {entity_name} carregada ({len(self._soul_prompt)} chars)")
            else:
                self._soul_prompt = f"Voce e {entity_name}, assistente virtual."
                logger.warning(f"Arquivo alma.txt nao encontrado: {alma_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar alma: {e}")
            self._soul_prompt = f"Voce e {entity_name}, assistente virtual."

        self._system_instruction = self._soul_prompt

    def build_full_prompt(
        self,
        user_text: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
        memory_context: str = "",
    ) -> str:
        parts = []

        if self._soul_prompt:
            parts.append(self._soul_prompt)

        if memory_context:
            parts.append(f"\n[CONTEXTO DE MEMORIA]\n{memory_context}")

        if visual_context:
            parts.append(f"\n[VISAO ATUAL]\n{visual_context}")

        if attached_content:
            parts.append(f"\n[DOCUMENTO ANEXADO]\n{attached_content[:8000]}")

        parts.append(f"\n[USUARIO]\n{user_text}")

        return "\n".join(parts)

    def call_llm(self, prompt: str) -> str:
        return self._consciencia.llm_caller.call(prompt)

    def has_provider(self) -> bool:
        return self._consciencia.llm_caller.has_provider()

    def get_llm_status(self) -> dict[str, Any]:
        if self._consciencia._universal_llm:
            return self._consciencia._universal_llm.get_status()
        return {
            "providers": [],
            "active": self._consciencia.provider,
            "model": self._consciencia.model_name,
        }

    def stream_response(
        self,
        user_text: str,
        visual_context: str | None = None,
        attached_content: str | None = None,
    ) -> Generator[tuple[str, bool, dict[str, Any] | None], None, None]:
        return self._consciencia.response_streamer.stream(
            user_text,
            visual_context,
            attached_content,
            self._consciencia.smart_memory,
            self._consciencia.conversation_history,
        )

    def on_llm_fallback(self, from_provider: str, to_provider: str) -> None:
        logger.warning(f"LLM Fallback: {from_provider} -> {to_provider}")
        self._consciencia.metrics.increment("llm_fallbacks")
        if self._consciencia.app and hasattr(self._consciencia.app, "add_chat_entry"):
            try:
                self._consciencia.app.call_from_thread(
                    self._consciencia.app.add_chat_entry,
                    "kernel",
                    f"[Fallback: usando {to_provider}]",
                )
            except Exception:
                pass

    def call_with_universal_llm(self, prompt: str) -> str:
        if not self._consciencia._universal_llm:
            raise RuntimeError("UniversalLLM nao inicializado")

        response = self._consciencia._universal_llm.generate(
            prompt=prompt,
            system=self._system_instruction,
            temperature=0.8,
            max_tokens=1024,
        )

        if response.fallback_used:
            logger.info(f"Resposta via fallback: {response.provider}")

        return response.text

    def get_model_for_intent(self, intent: Intent) -> tuple[str, str]:
        original_model = self._consciencia.model_name
        routing_map = getattr(config, "INTENT_ROUTING", {}).get("model_routing", {})
        target_model = routing_map.get(intent.value, original_model)

        if target_model != original_model:
            logger.info(f"Roteando para modelo: {target_model} (intent: {intent.value})")

        return target_model, original_model
