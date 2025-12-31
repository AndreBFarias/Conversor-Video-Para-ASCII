import logging
import random

from src.core.entity_loader import EntityLoader, get_active_entity

from .constants import FALLBACK_ALMA_PATH
from .phrases import DEFAULT_PHRASES

logger = logging.getLogger(__name__)


class DicionarioPersonalidade:
    def __init__(self):
        self._frases_usadas: dict[str, list[int]] = {}
        self._entity_id: str | None = None
        self._entity_loader: EntityLoader | None = None
        self._frases = DEFAULT_PHRASES.copy()

    def _load_entity(self) -> None:
        try:
            self._entity_id = get_active_entity()
            self._entity_loader = EntityLoader(self._entity_id)
            logger.info(f"EntityLoader inicializado para entidade: {self._entity_id}")
        except Exception as e:
            logger.warning(f"Erro ao carregar EntityLoader: {e}. Usando fallback para Luna.")
            self._entity_id = "luna"
            self._entity_loader = None

    def obter_frase(self, categoria: str) -> str:
        entity_phrases = self.get_entity_phrases(categoria)
        phrases_to_use = entity_phrases if entity_phrases else self._frases.get(categoria, [])

        if not phrases_to_use:
            logger.warning(f"Categoria desconhecida: {categoria}")
            return ""

        if categoria not in self._frases_usadas:
            self._frases_usadas[categoria] = []

        disponiveis = [i for i, _ in enumerate(phrases_to_use) if i not in self._frases_usadas[categoria]]

        if not disponiveis:
            self._frases_usadas[categoria] = []
            disponiveis = list(range(len(phrases_to_use)))

        escolhido = random.choice(disponiveis)
        self._frases_usadas[categoria].append(escolhido)

        return phrases_to_use[escolhido]

    def resetar_categoria(self, categoria: str) -> None:
        if categoria in self._frases_usadas:
            self._frases_usadas[categoria] = []

    def resetar_todas(self) -> None:
        self._frases_usadas = {}

    def reload_for_entity(self, entity_id: str) -> None:
        logger.info(f"Recarregando personalidade para entidade: {entity_id}")
        self._entity_id = entity_id
        self._entity_loader = EntityLoader(entity_id)
        self._frases_usadas = {}
        logger.info(f"Personalidade recarregada para: {entity_id}")

    def get_entity_phrases(self, context: str) -> list[str]:
        if not self._entity_loader:
            self._load_entity()

        if not self._entity_loader:
            return self._frases.get(context, [])

        try:
            config = self._entity_loader.get_config()
            phrases_dict = config.get("phrases", {})

            if context in phrases_dict and phrases_dict[context]:
                logger.debug(
                    f"Frases customizadas encontradas para contexto '{context}' da entidade '{self._entity_id}'"
                )
                return phrases_dict[context]
        except Exception as e:
            logger.warning(f"Erro ao buscar frases customizadas: {e}")

        return self._frases.get(context, [])

    def get_soul_prompt(self) -> str:
        if not self._entity_loader:
            self._load_entity()

        if self._entity_loader:
            try:
                soul_prompt = self._entity_loader.get_soul_prompt()
                if soul_prompt:
                    logger.info(f"Soul prompt carregado via EntityLoader para entidade: {self._entity_id}")
                    return soul_prompt
            except Exception as e:
                logger.error(f"Erro ao carregar soul prompt via EntityLoader: {e}")

        logger.warning(f"Fallback para alma_da_luna.txt em {FALLBACK_ALMA_PATH}")

        if FALLBACK_ALMA_PATH.exists():
            try:
                with open(FALLBACK_ALMA_PATH, encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Erro ao ler fallback alma_da_luna.txt: {e}")

        logger.critical("Nenhum soul prompt disponivel! Retornando string vazia.")
        return ""
