"""
Streaming de respostas LLM (token-by-token).

Este modulo fornece funcionalidade de streaming de respostas
tanto para Gemini quanto para Ollama.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from src.core.ollama_client import OllamaSyncClient

import config
from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.data_memory.smart_memory import SmartMemory
from src.soul.response_parser import get_parser

logger = get_logger(__name__)


class ResponseStreamer:
    def __init__(
        self,
        entity_id: str,
        provider: str,
        model_name: str,
        gemini_client: Any = None,
        ollama_client: "OllamaSyncClient" = None,
        system_instruction: str = "",
    ):
        self.entity_id = entity_id
        self.provider = provider
        self.model_name = model_name
        self.gemini_client = gemini_client
        self.ollama_client = ollama_client
        self.system_instruction = system_instruction
        self.response_parser = get_parser()

    def _fallback_response(self, error_msg: str = None) -> dict:
        entity_name = get_entity_name(self.entity_id)
        return {
            "fala_tts": "Hmm, tive um problema tecnico. Pode repetir?",
            "leitura": "Confusa",
            "log_terminal": f"[{entity_name} franze a testa] Hmm, tive um problema tecnico... {error_msg or ''}",
            "animacao": f"{entity_name}_observando",
            "comando_visao": False,
            "tts_config": {"speed": 1.0, "stability": 0.5},
            "registrar_rosto": None,
            "filesystem_ops": [],
        }

    def _validate_schema(self, data: dict) -> bool:
        required = ["fala_tts", "log_terminal", "animacao", "comando_visao"]
        for field in required:
            if field not in data:
                return False
        return True

    def stream(
        self,
        user_text: str,
        visual_context: str = None,
        attached_content: str = None,
        smart_memory: SmartMemory = None,
        conversation_history: list = None,
    ) -> Generator[tuple[str, bool, dict[str, Any] | None], None, None]:
        if not self._has_provider():
            yield (
                "Estou em modo offline. Nenhum modelo de linguagem configurado.",
                True,
                self._fallback_response("Offline"),
            )
            return

        contexto_memoria = ""
        try:
            if smart_memory:
                mem_context = smart_memory.retrieve(user_text, max_chars=600)
                user_profile = smart_memory.get_user_profile_context()
                if mem_context or user_profile:
                    parts = []
                    if user_profile:
                        parts.append(user_profile)
                    if mem_context:
                        parts.append(mem_context)
                    contexto_memoria = "\n".join(parts) + "\n"
        except Exception as e:
            logger.error(f"Erro ao recuperar memoria para streaming: {e}")

        message_parts = []
        if user_text:
            message_parts.append(f"Usuario disse: {user_text}")
        if visual_context:
            message_parts.append(f"Contexto visual: {visual_context}")
        if attached_content:
            message_parts.append(f"Conteudo anexado:\n{attached_content}")

        full_message = " | ".join(message_parts)

        history_text = ""
        if conversation_history:
            history_limit = 3 if self.provider == "local" else 5
            max_chars = 150
            entity_name = get_entity_name(self.entity_id)
            history_text = "HISTORICO:\n"
            for turn in conversation_history[-history_limit:]:
                u = turn.get("user", "")[:max_chars]
                l = turn.get("luna", {}).get("fala_tts", "")[:max_chars]
                if u or l:
                    history_text += f"User: {u}\n{entity_name}: {l}\n"

        full_prompt = (
            f"{self.system_instruction}\n\n{contexto_memoria}\n{history_text}\nINTERACAO ATUAL:\n{full_message}"
        )

        full_response = ""
        try:
            if self.provider == "gemini" and self.gemini_client:
                for chunk in self._stream_gemini(full_prompt):
                    full_response += chunk
                    yield (chunk, False, None)

            elif self.provider == "local" and self.ollama_client:
                for chunk in self._stream_ollama(full_prompt):
                    full_response += chunk
                    yield (chunk, False, None)

            else:
                yield ("Nenhum provider disponivel", True, self._fallback_response("Sem provider"))
                return

            parsed_data, method = self.response_parser.parse(full_response)
            if self._validate_schema(parsed_data):
                if conversation_history is not None:
                    conversation_history.append(
                        {"user": user_text, "luna": parsed_data, "timestamp": datetime.now().isoformat()}
                    )
                yield ("", True, parsed_data)
            else:
                yield ("", True, self._fallback_response("Schema invalido"))

        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield (f"Erro: {str(e)[:50]}", True, self._fallback_response(str(e)[:50]))

    def _stream_gemini(self, prompt: str) -> Generator[str, None, None]:
        try:
            response_stream = self.gemini_client.models.generate_content_stream(model=self.model_name, contents=prompt)

            for chunk in response_stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Erro no stream Gemini: {e}")
            raise

    def _stream_ollama(self, prompt: str) -> Generator[str, None, None]:
        try:
            system_prompt = (
                self.system_instruction
                if self.system_instruction
                else ("Voce e Luna, uma assistente gotica sarcastica. Responda em JSON.")
            )

            for chunk in self.ollama_client.stream(
                prompt=prompt,
                model=self.model_name,
                system=system_prompt,
                temperature=config.CHAT_LOCAL.get("temperature", 0.7),
            ):
                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"Erro no stream Ollama: {e}")
            raise

    def _has_provider(self) -> bool:
        return self.ollama_client is not None or self.gemini_client is not None


def create_response_streamer(
    entity_id: str,
    provider: str,
    model_name: str,
    gemini_client: Any = None,
    ollama_client: Any = None,
    system_instruction: str = "",
) -> ResponseStreamer:
    return ResponseStreamer(
        entity_id,
        provider,
        model_name,
        gemini_client,
        ollama_client,
        system_instruction,
    )
