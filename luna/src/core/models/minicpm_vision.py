import base64
import logging
from dataclasses import dataclass
from pathlib import Path

import config
from src.core.ollama_client import OllamaClient, get_ollama_client

logger = logging.getLogger(__name__)


VISION_SYSTEM_PROMPT = """Voce e Luna, uma observadora digital com visao aguçada.
Descreva o que ve de forma direta e tecnica.
Use portugues brasileiro.
Seja especifica sobre objetos, pessoas, cores e acoes visiveis.
Nao invente detalhes que nao estao claramente visiveis."""


@dataclass
class VisionResponse:
    description: str
    objects: list[str]
    people_count: int
    has_text: bool
    detected_text: str | None = None
    raw_response: str | None = None
    error: str | None = None


class MiniCPMVision:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.5,
    ):
        self.model = model or config.VISION_LOCAL.get("model", "minicpm-v")
        self.temperature = temperature
        self._client: OllamaClient | None = None

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._client = get_ollama_client()
        return self._client

    def _encode_image(self, image_data: bytes) -> str:
        return base64.b64encode(image_data).decode("utf-8")

    def _parse_description(self, text: str) -> VisionResponse:
        text_lower = text.lower()

        objects = []
        common_objects = [
            "pessoa",
            "pessoas",
            "rosto",
            "computador",
            "tela",
            "monitor",
            "mesa",
            "cadeira",
            "janela",
            "porta",
            "livro",
            "celular",
            "teclado",
            "mouse",
            "copo",
            "garrafa",
            "planta",
            "quadro",
            "luz",
            "lampada",
            "camera",
            "microfone",
            "fone",
        ]
        for obj in common_objects:
            if obj in text_lower:
                objects.append(obj)

        people_count = 0
        if "pessoa" in text_lower or "alguem" in text_lower or "homem" in text_lower or "mulher" in text_lower:
            people_count = 1
        if "pessoas" in text_lower or "duas" in text_lower or "varios" in text_lower:
            people_count = 2
        if any(word in text_lower for word in ["grupo", "muitas", "varios"]):
            people_count = 3

        has_text = any(word in text_lower for word in ["texto", "escrito", "letras", "palavras", "titulo", "legenda"])

        return VisionResponse(
            description=text,
            objects=objects,
            people_count=people_count,
            has_text=has_text,
            raw_response=text,
        )

    async def describe(
        self,
        image_base64: str,
        prompt: str | None = None,
    ) -> VisionResponse:
        client = self._get_client()

        if prompt is None:
            prompt = (
                "Descreva detalhadamente o que voce ve nesta imagem. Inclua objetos, pessoas, cores e acoes visiveis."
            )

        response = await client.vision(
            prompt=prompt,
            image_base64=image_base64,
            temperature=self.temperature,
        )

        if response.error:
            return VisionResponse(
                description="",
                objects=[],
                people_count=0,
                has_text=False,
                error=response.error,
            )

        return self._parse_description(response.text)

    async def describe_from_file(
        self,
        image_path: str,
        prompt: str | None = None,
    ) -> VisionResponse:
        try:
            path = Path(image_path)
            if not path.exists():
                return VisionResponse(
                    description="",
                    objects=[],
                    people_count=0,
                    has_text=False,
                    error=f"Arquivo nao encontrado: {image_path}",
                )

            with open(path, "rb") as f:
                image_data = f.read()

            image_base64 = self._encode_image(image_data)
            return await self.describe(image_base64, prompt)

        except Exception as e:
            logger.error(f"Erro ao ler imagem: {e}")
            return VisionResponse(
                description="",
                objects=[],
                people_count=0,
                has_text=False,
                error=str(e),
            )

    async def describe_from_bytes(
        self,
        image_bytes: bytes,
        prompt: str | None = None,
    ) -> VisionResponse:
        try:
            image_base64 = self._encode_image(image_bytes)
            return await self.describe(image_base64, prompt)
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return VisionResponse(
                description="",
                objects=[],
                people_count=0,
                has_text=False,
                error=str(e),
            )

    async def detect_changes(
        self,
        current_image: str,
        previous_description: str,
    ) -> tuple[bool, str]:
        prompt = f"""Compare a imagem atual com esta descricao anterior:

Descricao anterior: {previous_description}

O que mudou? Responda de forma breve:
- Se nao mudou nada significativo, diga "SEM MUDANCAS"
- Se mudou, descreva apenas as mudancas"""

        response = await self.describe(current_image, prompt)

        if response.error:
            return False, f"Erro: {response.error}"

        text_lower = response.description.lower()
        if "sem mudanca" in text_lower or "nao mudou" in text_lower or "mesma" in text_lower:
            return False, "Sem mudancas significativas"

        return True, response.description

    async def identify_person(
        self,
        image_base64: str,
        known_names: list[str] | None = None,
    ) -> dict:
        prompt = "Descreva a pessoa na imagem: idade aproximada, genero, caracteristicas faciais, expressao, o que esta vestindo."

        if known_names:
            prompt += f"\n\nSe reconhecer alguma dessas pessoas, identifique: {', '.join(known_names)}"

        response = await self.describe(image_base64, prompt)

        if response.error:
            return {"error": response.error}

        return {
            "description": response.description,
            "people_detected": response.people_count > 0,
        }

    async def read_text(self, image_base64: str) -> str:
        prompt = "Leia e transcreva todo o texto visivel nesta imagem. Se nao houver texto, diga 'SEM TEXTO'."

        response = await self.describe(image_base64, prompt)

        if response.error:
            return f"[Erro: {response.error}]"

        if "sem texto" in response.description.lower():
            return ""

        return response.description

    async def analyze_screen(self, image_base64: str) -> dict:
        prompt = """Analise esta captura de tela. Identifique:
1. Qual aplicativo ou site esta aberto
2. Elementos principais da interface
3. Qualquer texto importante visivel
4. Estado geral (carregando, erro, normal)

Seja breve e direto."""

        response = await self.describe(image_base64, prompt)

        if response.error:
            return {"error": response.error}

        return {
            "analysis": response.description,
            "has_text": response.has_text,
        }

    async def is_available(self) -> bool:
        client = self._get_client()
        if not await client.check_health():
            return False
        return await client.model_exists(self.model)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


_instance: MiniCPMVision | None = None


def get_minicpm_vision() -> MiniCPMVision:
    global _instance
    if _instance is None:
        _instance = MiniCPMVision()
    return _instance


async def quick_describe(image_path: str) -> str:
    vision = get_minicpm_vision()
    response = await vision.describe_from_file(image_path)
    if response.error:
        return f"[Erro: {response.error}]"
    return response.description
