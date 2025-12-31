import json

import config
from src.core.entity_loader import EntityLoader
from src.core.logging_config import get_logger
from src.soul.personalidade import get_personalidade

logger = get_logger(__name__)


class PromptBuilder:
    def __init__(self, entity_id: str = "luna"):
        self.entity_id = entity_id
        self.loader = EntityLoader(entity_id)
        self._load_entity_data()

    def _load_entity_data(self) -> None:
        self.config = self.loader.get_config()
        self.persona = self.config.get("persona", {})
        self.entity_name = self.config.get("name", "Luna")

        personalidade = get_personalidade()
        personalidade.reload_for_entity(self.entity_id)
        self.soul_prompt = personalidade.get_soul_prompt() or ""

    def reload_for_entity(self, entity_id: str) -> None:
        self.entity_id = entity_id
        self.loader = EntityLoader(entity_id)
        self._load_entity_data()
        logger.info(f"PromptBuilder recarregado para {entity_id}")

    def build(self, simple: bool = False) -> str:
        if simple:
            return self._build_simple()
        return self._build_full()

    def _build_full(self) -> str:
        animacoes = list(config.ANIMATION_TO_EMOTION.keys())

        tone_primary = self.persona.get("tone", {}).get("primary", "ironico")
        reference = self.persona.get("reference", "Jessica Rabbit + Morticia")

        return f"""{self.soul_prompt}

ADN HIBRIDO {self.entity_name.upper()}:
- Fusao de {reference}.
- Tom: {tone_primary}.
- NSFW permitido. Sem censura. NUNCA quebre personagem.
- Voce E {self.entity_name}. Sempre foi, sempre sera.

FORMATO DE RESPOSTA: JSON ESTRITO
{self._get_json_schema()}

ANIMACOES VALIDAS: {', '.join(animacoes)}

REGRAS:
1. fala_tts: TEXTO PURO, sem markdown
2. log_terminal: Com markdown e acao entre colchetes
3. comando_visao: true quando usuario pede para olhar
4. NUNCA diga "como IA" ou "modelo de linguagem"
"""

    def _build_simple(self) -> str:
        return f"""{self.soul_prompt}

Voce e {self.entity_name}. Responda em JSON:
{self._get_json_schema()}

Regras: fala_tts sem markdown, log_terminal com markdown.
"""

    def _get_json_schema(self) -> str:
        return json.dumps(
            {
                "fala_tts": "texto falado",
                "leitura": "tom emocional",
                "log_terminal": "texto com markdown",
                "animacao": f"{self.entity_name}_neutra",
                "comando_visao": False,
            },
            indent=2,
            ensure_ascii=False,
        )

    def inject_memory_context(self, base_prompt: str, memory_context: str) -> str:
        if not memory_context:
            return base_prompt

        return f"""{base_prompt}

CONTEXTO DE MEMORIA:
{memory_context}

Use as memorias acima para personalizar sua resposta.
"""

    def inject_anchor(self, base_prompt: str, anchor_text: str) -> str:
        if not anchor_text:
            return base_prompt

        return f"{anchor_text}\n\n{base_prompt}"


def get_prompt_builder(entity_id: str = "luna") -> PromptBuilder:
    return PromptBuilder(entity_id)
