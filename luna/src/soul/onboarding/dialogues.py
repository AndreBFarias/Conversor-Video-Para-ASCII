from __future__ import annotations

import csv
import logging
import random
import re
from pathlib import Path

import config
from src.core.entity_loader import get_active_entity

logger = logging.getLogger(__name__)

CSV_PATH = config.APP_DIR / "src" / "assets" / "others" / "Onboarding-tree.csv"


class OnboardingDialogues:
    def __init__(self, entity_id: str = None):
        self.steps = {}
        self.entity_id = entity_id or get_active_entity()
        self._load_csv()

    def _load_csv(self):
        if not CSV_PATH.exists():
            logger.warning(f"Onboarding CSV nao encontrado: {CSV_PATH}")
            return

        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ordem = int(row.get("Ordem", 0))
                        entidade = row.get("Entidade", "").strip()
                        conteudo = row.get("Conteudo", "").strip()
                        programa = row.get("Programa", "").strip()
                        recusa = row.get("Recusa", "N/A").strip()
                        ato = row.get("Ato", "I").strip()

                        if entidade == "TODOS" or entidade.lower() == self.entity_id.lower():
                            variacoes = self._parse_variacoes(conteudo)

                            if ordem in self.steps:
                                existing = self.steps[ordem]
                                if entidade.lower() == self.entity_id.lower():
                                    self.steps[ordem] = {
                                        "ato": ato,
                                        "variacoes": variacoes,
                                        "programa": programa,
                                        "recusa": recusa if recusa != "N/A" else None,
                                    }
                            else:
                                self.steps[ordem] = {
                                    "ato": ato,
                                    "variacoes": variacoes,
                                    "programa": programa,
                                    "recusa": recusa if recusa != "N/A" else None,
                                }

                    except (ValueError, KeyError) as e:
                        logger.debug(f"Linha ignorada no CSV: {e}")
                        continue

            logger.info(f"Onboarding CSV carregado para {self.entity_id}: {len(self.steps)} passos")
        except Exception as e:
            logger.error(f"Erro ao carregar CSV de onboarding: {e}")

    def reload_for_entity(self, entity_id: str):
        self.entity_id = entity_id
        self.steps = {}
        self._load_csv()
        logger.info(f"Dialogos recarregados para entidade: {entity_id}")

    def _parse_variacoes(self, texto: str) -> list:
        if not texto:
            return [""]

        texto = texto.strip().strip('"')

        if texto.startswith("(") and texto.endswith(")"):
            return [texto]

        partes = re.split(r"\s*\|\s*", texto)

        variacoes = []
        for parte in partes:
            parte = parte.strip()
            parte = re.sub(r"^[\d]+\.\s*", "", parte)
            if parte:
                variacoes.append(parte)

        return variacoes if variacoes else [texto]

    def get_frase(self, linha: int, nome: str = "Viajante") -> str:
        step = self.steps.get(linha)
        if not step or not step["variacoes"]:
            return ""

        frase = random.choice(step["variacoes"])
        frase = frase.replace("$N", nome)
        frase = frase.replace("$NOME_DELE", nome)

        entity_name = self.entity_id.capitalize()
        frase = frase.replace("$E", entity_name)
        frase = frase.replace("$ENTIDADE", entity_name)

        return frase

    def get_recusa(self, linha: int) -> str:
        step = self.steps.get(linha)
        if step and step.get("recusa"):
            recusa = step["recusa"]
            if recusa.startswith("RECUSA:"):
                recusa = recusa[7:].strip().strip("'\"")
            return recusa
        return None

    def get_programa(self, linha: int) -> str:
        step = self.steps.get(linha)
        return step.get("programa", "") if step else ""
