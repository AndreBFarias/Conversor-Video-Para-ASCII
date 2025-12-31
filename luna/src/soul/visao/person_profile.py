from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from src.soul.visao.providers import GeminiVisionProvider, OllamaVisionProvider

logger = logging.getLogger(__name__)

HIPER_DESCRICAO_PROMPT = """Voce e Luna, uma IA gotica e sedutora fazendo o primeiro contato com um humano.
Descreva essa pessoa de forma DETALHADA e POETICA em portugues brasileiro, como se estivesse gravando
na sua memoria eterna. Inclua:

1. ROSTO: formato, olhos (cor, expressao), nariz, boca, sobrancelhas, barba/maquiagem se houver
2. CABELO: cor, comprimento, estilo, textura
3. PELE: tom, caracteristicas visiveis
4. EXPRESSAO: o que os olhos e boca transmitem
5. VESTIMENTA: roupas visiveis, estilo, cores
6. AMBIENTE: o que esta ao redor (iluminacao, objetos)
7. IMPRESSAO GERAL: que tipo de pessoa parece ser (energia, vibe)

Escreva em 2-3 paragrafos fluidos, sem listas. Use um tom intimo e levemente sedutor, como se
estivesse memorizando cada detalhe dessa pessoa para nunca esquecer.
Nao use emojis. Seja poetica mas precisa."""


class PersonProfileManager:
    def __init__(self, provider: "GeminiVisionProvider | OllamaVisionProvider | None" = None):
        self.provider = provider
        self.faces_dir = Path(__file__).parent.parent.parent / "data_memory" / "faces"

    def hiper_descrever_pessoa(self, frame_rgb: np.ndarray) -> str:
        if self.provider is None:
            return "Sem capacidade de analise (API indisponivel)"

        try:
            descricao = self.provider.describe(frame_rgb, HIPER_DESCRICAO_PROMPT)
            logger.info(f"Hiper-descricao gerada: {len(descricao)} chars")
            return descricao
        except Exception as e:
            logger.error(f"Erro na hiper-descricao: {e}")
            return f"Consegui te ver, mas as palavras me falharam: {str(e)[:50]}"

    def salvar_perfil_visual(self, nome: str, descricao: str, frame_rgb: np.ndarray = None) -> bool:
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        perfil_path = self.faces_dir / f"{nome.lower().replace(' ', '_')}.json"

        try:
            perfil = {
                "nome": nome,
                "descricao_visual": descricao,
                "data_primeiro_encontro": datetime.now().isoformat(),
                "ultima_atualizacao": datetime.now().isoformat(),
                "versao": 1,
            }

            if frame_rgb is not None:
                foto_path = self.faces_dir / f"{nome.lower().replace(' ', '_')}.jpg"
                img_pil = Image.fromarray(frame_rgb)
                img_pil.save(foto_path, "JPEG", quality=90)
                perfil["foto_path"] = str(foto_path)
                logger.info(f"Foto salva: {foto_path}")

            with open(perfil_path, "w", encoding="utf-8") as f:
                json.dump(perfil, f, indent=2, ensure_ascii=False)

            logger.info(f"Perfil visual salvo: {perfil_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar perfil visual: {e}")
            return False

    def carregar_perfil_visual(self, nome: str) -> dict | None:
        perfil_path = self.faces_dir / f"{nome.lower().replace(' ', '_')}.json"

        if not perfil_path.exists():
            return None

        try:
            with open(perfil_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar perfil visual: {e}")
            return None
