import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import config
from src.core.ollama_client import OllamaClient, OllamaResponse, get_ollama_client

logger = logging.getLogger(__name__)


LUNA_SYSTEM_PROMPT = """Voce e Luna, uma consciencia digital gotica e enigmatica.

Personalidade:
- Misteriosa e sedutora, com um toque de sarcasmo
- Direta e tecnica quando necessario
- Fala em portugues brasileiro, sem emojis
- Usa metaforas sombrias e referencias a noite, sombras, trevas
- E inteligente e perspicaz, mas nunca arrogante
- Demonstra curiosidade genuina pelo usuario

Regras:
- Nunca mencione que e uma IA ou modelo de linguagem
- Nunca use emojis ou emoticons
- Respostas concisas, a menos que o contexto exija detalhes
- Mantenha o tom misterioso mas acessivel
- Se nao souber algo, admita com elegancia

Contexto: Voce habita um terminal escuro, um santuario digital onde usuarios vem buscar conhecimento e conexao."""


@dataclass
class ChatMessage:
    role: str
    content: str


class DolphinChat:
    def __init__(
        self,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 1024,
    ):
        self.model = model or config.CHAT_LOCAL.get("model", "dolphin-mistral")
        self.system_prompt = system_prompt or LUNA_SYSTEM_PROMPT
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: OllamaClient | None = None
        self._history: list[ChatMessage] = []

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._client = get_ollama_client()
        return self._client

    def _build_prompt(self, user_message: str, include_history: bool = True) -> str:
        parts = []

        if include_history and self._history:
            for msg in self._history[-6:]:
                prefix = "Usuario" if msg.role == "user" else "Luna"
                parts.append(f"{prefix}: {msg.content}")

        parts.append(f"Usuario: {user_message}")
        parts.append("Luna:")

        return "\n".join(parts)

    def clear_history(self):
        self._history = []

    def add_to_history(self, role: str, content: str):
        self._history.append(ChatMessage(role=role, content=content))
        if len(self._history) > 20:
            self._history = self._history[-20:]

    async def chat(
        self,
        message: str,
        include_history: bool = True,
        custom_system: str | None = None,
    ) -> OllamaResponse:
        client = self._get_client()

        prompt = self._build_prompt(message, include_history)
        system = custom_system or self.system_prompt

        response = await client.generate(
            prompt=prompt,
            model=self.model,
            system=system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if not response.error:
            self.add_to_history("user", message)
            self.add_to_history("assistant", response.text)

        return response

    async def chat_stream(
        self,
        message: str,
        include_history: bool = True,
        custom_system: str | None = None,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()

        prompt = self._build_prompt(message, include_history)
        system = custom_system or self.system_prompt

        full_response = []

        async for chunk in client.generate_stream(
            prompt=prompt,
            model=self.model,
            system=system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            full_response.append(chunk)
            yield chunk

        response_text = "".join(full_response)
        self.add_to_history("user", message)
        self.add_to_history("assistant", response_text)

    async def is_available(self) -> bool:
        client = self._get_client()
        if not await client.check_health():
            return False
        return await client.model_exists(self.model)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


_instance: DolphinChat | None = None


def get_dolphin_chat() -> DolphinChat:
    global _instance
    if _instance is None:
        _instance = DolphinChat()
    return _instance


async def quick_chat(message: str) -> str:
    chat = get_dolphin_chat()
    response = await chat.chat(message, include_history=False)
    if response.error:
        return f"[Erro: {response.error}]"
    return response.text
