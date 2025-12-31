from __future__ import annotations

import json
import logging

import config

from .models import VisualAnalysis

logger = logging.getLogger(__name__)

PHOTO_ANALYSIS_PROMPT = """Analise esta foto de uma pessoa e extraia TODAS as informacoes possiveis.
Responda em JSON com esta estrutura EXATA:
{
    "genero_aparente": "masculino/feminino/androgino",
    "idade_estimada": "XX anos",
    "faixa_etaria": "crianca/adolescente/jovem adulto/adulto/meia idade/idoso",
    "caracteristicas_fisicas": {
        "cabelo": "cor, comprimento, estilo",
        "olhos": "cor, formato",
        "pele": "tom",
        "rosto": "formato, caracteristicas marcantes",
        "altura_aparente": "baixo/medio/alto",
        "constituicao": "magro/medio/robusto"
    },
    "estilo_vestimenta": "casual/formal/esportivo/alternativo/etc",
    "acessorios": ["lista", "de", "acessorios"],
    "expressao_facial": "sorrindo/serio/neutro/pensativo/etc",
    "cor_predominante": "cor principal da roupa",
    "descricao_completa": "Uma descricao detalhada de 2-3 frases sobre a aparencia geral da pessoa",
    "confianca": 0.0 a 1.0
}
Seja preciso e detalhado. Responda APENAS o JSON."""


class PhotoAnalyzer:
    async def analyze_with_gemini(self, image_base64: str) -> VisualAnalysis | None:
        try:
            from google import genai

            client = genai.Client(api_key=config.GOOGLE_API_KEY)

            response = client.models.generate_content(
                model=config.GEMINI_CONFIG.get("MODEL_NAME", "gemini-2.0-flash"),
                contents=[{"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}, PHOTO_ANALYSIS_PROMPT],
            )

            text = response.text.strip()

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text)

            return VisualAnalysis(
                genero_aparente=data.get("genero_aparente", "indeterminado"),
                idade_estimada=data.get("idade_estimada", "desconhecida"),
                faixa_etaria=data.get("faixa_etaria", "adulto"),
                caracteristicas_fisicas=data.get("caracteristicas_fisicas", {}),
                estilo_vestimenta=data.get("estilo_vestimenta", "casual"),
                acessorios=data.get("acessorios", []),
                expressao_facial=data.get("expressao_facial", "neutro"),
                cor_predominante=data.get("cor_predominante", ""),
                descricao_completa=data.get("descricao_completa", ""),
                confianca=float(data.get("confianca", 0.7)),
            )

        except Exception as e:
            logger.error(f"Erro ao analisar foto com Gemini: {e}")
            return None
