import json
import logging
import random
import unicodedata
from datetime import datetime

import config

logger = logging.getLogger(__name__)


class AppearanceTracker:
    APPEARANCE_KEYWORDS = {
        "cabelo",
        "barba",
        "oculos",
        "camisa",
        "camiseta",
        "roupa",
        "maquiagem",
        "brinco",
        "colar",
        "bone",
        "chapeu",
        "vestido",
        "blusa",
        "jaqueta",
        "terno",
        "gravata",
        "piercing",
        "tatuagem",
        "bigode",
        "sobrancelha",
        "unhas",
        "esmalte",
    }

    CHANGE_COMMENTS = {
        "cabelo": [
            "Cortou o cabelo? Ou e impressao minha...",
            "Algo diferente no cabelo. Notei.",
            "Mudanca capilar detectada.",
        ],
        "barba": [
            "Mudou a barba. Interessante.",
            "A barba esta diferente hoje.",
            "Algo novo na barba, nao e?",
        ],
        "oculos": [
            "Oculos novos? Ficou diferente.",
            "Notei os oculos. Novo visual?",
            "Esses oculos sao novos?",
        ],
        "camisa": [
            "Gostei da camisa. Ou nao.",
            "Camisa nova? Interessante escolha.",
            "Essa camisa e nova?",
        ],
        "camiseta": [
            "Camiseta diferente hoje.",
            "Roupa nova? Notei.",
            "Mudou o visual?",
        ],
        "maquiagem": [
            "Caprichou na make hoje.",
            "Maquiagem diferente. Ficou bom.",
            "Algo novo no rosto...",
        ],
        "roupa": [
            "Visual diferente hoje.",
            "Mudou as roupas. Notei.",
            "Novo estilo?",
        ],
    }

    def __init__(self):
        self.history_path = config.USER_DATA_DIR / "appearance_history.json"
        self.history: list[dict] = []
        self._load_history()

    def _load_history(self):
        if self.history_path.exists():
            try:
                with open(self.history_path, encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar historico de aparencia: {e}")
                self.history = []

    def _save_history(self):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar historico: {e}")

    def add_observation(self, description: str, photo_path: str = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "photo_path": str(photo_path) if photo_path else None,
        }
        self.history.append(entry)

        if len(self.history) > 50:
            self.history = self.history[-50:]

        self._save_history()
        logger.debug("Observacao de aparencia adicionada")

    def detect_change(self, new_description: str) -> tuple[bool, str | None]:
        if not self.history:
            return False, None

        last = self.history[-1]["description"]

        new_normalized = self._normalize(new_description)
        last_normalized = self._normalize(last)

        new_keywords = set(new_normalized.split()) & self.APPEARANCE_KEYWORDS
        last_keywords = set(last_normalized.split()) & self.APPEARANCE_KEYWORDS

        diff = new_keywords - last_keywords

        if diff:
            change_word = list(diff)[0]
            comments = self.CHANGE_COMMENTS.get(change_word)
            if comments:
                comment = random.choice(comments)
            else:
                comment = f"Algo diferente em voce... {change_word}?"
            return True, comment

        return False, None

    def _normalize(self, text: str) -> str:
        result = text.lower()
        nfkd = unicodedata.normalize("NFKD", result)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def get_recent_observations(self, count: int = 5) -> list[dict]:
        return self.history[-count:] if self.history else []
