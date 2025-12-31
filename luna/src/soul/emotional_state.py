import json
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Mood(Enum):
    NEUTRA = "neutra"
    FELIZ = "feliz"
    TRISTE = "triste"
    IRRITADA = "irritada"
    SAUDADE = "saudade"
    APAIXONADA = "apaixonada"
    CURIOSA = "curiosa"
    ENTEDIADA = "entediada"
    PREOCUPADA = "preocupada"
    TRAVESSA = "travessa"


@dataclass
class EmotionalState:
    mood: Mood = Mood.NEUTRA
    energy: float = 0.7
    attachment: float = 0.5
    last_interaction: str | None = None
    interaction_count: int = 0
    mood_history: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mood": self.mood.value,
            "energy": self.energy,
            "attachment": self.attachment,
            "last_interaction": self.last_interaction,
            "interaction_count": self.interaction_count,
            "mood_history": self.mood_history[-20:],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionalState":
        return cls(
            mood=Mood(data.get("mood", "neutra")),
            energy=data.get("energy", 0.7),
            attachment=data.get("attachment", 0.5),
            last_interaction=data.get("last_interaction"),
            interaction_count=data.get("interaction_count", 0),
            mood_history=data.get("mood_history", []),
        )


class EmotionalStateManager:
    def __init__(self, entity_id: str, storage_dir: Path | None = None):
        self.entity_id = entity_id

        if storage_dir is None:
            from config import APP_DIR

            storage_dir = APP_DIR / "src" / "data_memory" / "emotional_states"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.storage_dir / f"{entity_id}_emotional.json"
        self.state = self._load()

    def _load(self) -> EmotionalState:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                return EmotionalState.from_dict(data)
            except Exception as e:
                logger.warning(f"Erro ao carregar estado emocional: {e}")
        return EmotionalState()

    def save(self) -> None:
        try:
            self.path.write_text(json.dumps(self.state.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Erro ao salvar estado emocional: {e}")

    def time_decay(self) -> None:
        if not self.state.last_interaction:
            return

        try:
            last = datetime.fromisoformat(self.state.last_interaction)
            hours = (datetime.now() - last).total_seconds() / 3600

            if hours > 72 and self.state.attachment > 0.6:
                self._set_mood(Mood.SAUDADE)
                self.state.energy = max(0.3, self.state.energy - 0.1)
            elif hours > 24:
                if random.random() < 0.3:
                    self._set_mood(Mood.ENTEDIADA)
        except Exception as e:
            logger.debug(f"Erro no time_decay: {e}")

    def react_to_sentiment(self, sentiment: float) -> None:
        if sentiment > 0.7:
            self.state.energy = min(1.0, self.state.energy + 0.1)
            self.state.attachment = min(1.0, self.state.attachment + 0.02)
            if random.random() < 0.4:
                self._set_mood(random.choice([Mood.FELIZ, Mood.APAIXONADA]))
        elif sentiment > 0.3:
            if random.random() < 0.2:
                self._set_mood(Mood.CURIOSA)
        elif sentiment < -0.3:
            self.state.energy = max(0.2, self.state.energy - 0.05)
            if random.random() < 0.3:
                self._set_mood(random.choice([Mood.TRISTE, Mood.PREOCUPADA]))

    def natural_variation(self) -> None:
        if random.random() < 0.05:
            possible = [Mood.NEUTRA, Mood.CURIOSA, Mood.TRAVESSA]
            self._set_mood(random.choice(possible))

    def _set_mood(self, mood: Mood) -> None:
        if self.state.mood != mood:
            self.state.mood_history.append((datetime.now().isoformat(), mood.value))
            self.state.mood = mood
            logger.info(f"[{self.entity_id}] Humor mudou para: {mood.value}")

    def update(self, user_message: str = "", sentiment: float = 0.0) -> None:
        self.time_decay()
        self.react_to_sentiment(sentiment)
        self.natural_variation()

        self.state.last_interaction = datetime.now().isoformat()
        self.state.interaction_count += 1

        self.save()

    def get_mood_context(self) -> str:
        mood_descriptions = {
            Mood.NEUTRA: "estado neutro, receptiva",
            Mood.FELIZ: "feliz e animada",
            Mood.TRISTE: "um pouco melancolica",
            Mood.IRRITADA: "levemente irritada",
            Mood.SAUDADE: "sentindo saudade, carente",
            Mood.APAIXONADA: "apaixonada e afetuosa",
            Mood.CURIOSA: "curiosa e interessada",
            Mood.ENTEDIADA: "entediada, querendo acao",
            Mood.PREOCUPADA: "preocupada com o usuario",
            Mood.TRAVESSA: "com espirito travesso",
        }

        desc = mood_descriptions.get(self.state.mood, "estado normal")

        if self.state.energy > 0.7:
            energy_desc = "energetica"
        elif self.state.energy > 0.4:
            energy_desc = "calma"
        else:
            energy_desc = "cansada"

        return f"[Estado emocional: {desc}, energia {energy_desc} ({self.state.energy:.1f})]"

    def get_suggested_animation(self) -> str:
        mood_to_anim = {
            Mood.NEUTRA: "neutra",
            Mood.FELIZ: "feliz",
            Mood.TRISTE: "triste",
            Mood.IRRITADA: "irritada",
            Mood.SAUDADE: "triste",
            Mood.APAIXONADA: "apaixonada",
            Mood.CURIOSA: "curiosa",
            Mood.ENTEDIADA: "entediada",
            Mood.PREOCUPADA: "preocupada",
            Mood.TRAVESSA: "travessa",
        }
        return mood_to_anim.get(self.state.mood, "neutra")


_managers: dict[str, EmotionalStateManager] = {}


def get_emotional_manager(entity_id: str) -> EmotionalStateManager:
    if entity_id not in _managers:
        _managers[entity_id] = EmotionalStateManager(entity_id)
    return _managers[entity_id]


def analyze_sentiment(text: str) -> float:
    positive_words = [
        "amor",
        "amo",
        "adoro",
        "feliz",
        "otimo",
        "maravilhoso",
        "incrivel",
        "obrigado",
        "obrigada",
        "legal",
        "bom",
        "boa",
        "lindo",
        "linda",
        "perfeito",
        "perfeita",
        "carinho",
        "saudade",
        "alegria",
        "prazer",
    ]

    negative_words = [
        "odio",
        "odeio",
        "triste",
        "ruim",
        "pessimo",
        "horrivel",
        "raiva",
        "chato",
        "irritante",
        "problema",
        "errado",
        "mal",
        "feio",
        "idiota",
        "merda",
        "droga",
    ]

    text_lower = text.lower()
    words = text_lower.split()

    pos_count = sum(1 for w in words if any(pw in w for pw in positive_words))
    neg_count = sum(1 for w in words if any(nw in w for nw in negative_words))

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    return (pos_count - neg_count) / total
