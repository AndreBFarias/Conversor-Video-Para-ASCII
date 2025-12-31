import numpy as np
from sentence_transformers import SentenceTransformer

import config
from src.core.logging_config import get_logger
from src.data_memory.embeddings_cache import get_embeddings_cache

logger = get_logger(__name__)


class EmbeddingGenerator:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384
        self._cache_folder = str(config.EMBEDDINGS_MODELS_DIR)

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Carregando modelo de embeddings: {self.model_name}")
            logger.info(f"Cache folder: {self._cache_folder}")
            self._model = SentenceTransformer(self.model_name, cache_folder=self._cache_folder, device="cpu")
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(self, text: str) -> np.ndarray:
        if not text or len(text.strip()) < 3:
            return np.zeros(self._dimension, dtype=np.float32)

        cache = get_embeddings_cache()
        cached = cache.get(text)
        if cached is not None:
            return cached

        try:
            embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            result = embedding.astype(np.float32)
            cache.set(text, result)
            return result
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return np.zeros(self._dimension, dtype=np.float32)

    def batch_encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([]).reshape(0, self._dimension)

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings em batch: {e}")
            return np.zeros((len(texts), self._dimension), dtype=np.float32)


_generator_instance = None


def get_embedding_generator() -> EmbeddingGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = EmbeddingGenerator()
    return _generator_instance


def get_embedding(text: str) -> np.ndarray:
    return get_embedding_generator().encode(text)
