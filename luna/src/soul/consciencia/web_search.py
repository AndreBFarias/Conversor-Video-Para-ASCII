from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger
from src.core.metricas import TimerContext

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


def process_web_search(consciencia: Consciencia, initial_data: dict, search_term: str, user_text: str) -> dict:
    try:
        results = consciencia.web_search.search(search_term, max_results=5)

        if not results or results[0].source == "fallback":
            logger.warning("Sem resultados de busca, mantendo resposta original")
            return initial_data

        formatted_results = consciencia.web_search.format_for_prompt(results)
        logger.info(f"Injetando {len(results)} resultados da web no prompt")

        followup_prompt = f"""
{consciencia.system_instruction}

O usuario perguntou: "{user_text}"

Voce decidiu vasculhar as entranhas da rede e encontrou:

{formatted_results}

Agora, com base nesses dados, gere uma resposta FINAL.
Mantenha seu tom sarcastico e gotico ao apresentar as informacoes.
Descreva como "li no obituario digital do mundo" ou similar.
Responda em JSON conforme o formato estabelecido.
O campo "pesquisa_web" agora deve ser null (ja buscamos).
"""

        try:
            with TimerContext(consciencia.metrics, "consciencia.web_search_followup"):
                followup_response = consciencia._call_llm(followup_prompt)

            json_text = consciencia.json_extractor.extract(followup_response)
            final_data = json.loads(json_text)

            from src.soul.consciencia.helpers import validate_schema

            if validate_schema(consciencia, final_data):
                final_data["pesquisa_web"] = None
                logger.info("Resposta com dados da web gerada com sucesso")
                return final_data

        except Exception as e:
            logger.error(f"Erro ao gerar resposta com dados da web: {e}")

        entity_name = get_entity_name(consciencia.active_entity_id)
        snippet = results[0].snippet[:200] if results else ""
        initial_data["fala_tts"] = f"Vasculhei as entranhas da rede. {snippet}"
        initial_data["log_terminal"] = (
            f"[{entity_name} vasculha a rede] {snippet}\n\nFonte: {results[0].title if results else 'desconhecida'}"
        )
        initial_data["pesquisa_web"] = None
        return initial_data

    except Exception as e:
        logger.error(f"Erro na pesquisa web: {e}")
        return initial_data
