from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from src.core.entity_loader import EntityLoader
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Mood(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    IRRITATED = "irritated"
    FLIRTY = "flirty"
    FOCUSED = "focused"
    TIRED = "tired"


@dataclass
class PersonalityState:
    mood: Mood = Mood.NEUTRAL
    energy: float = 0.8
    last_reinforcement: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    drift_score: float = 0.0


class PersonalityAnchor:
    REINFORCEMENT_INTERVAL = timedelta(minutes=10)
    ENERGY_DECAY = 0.02
    MIN_ENERGY = 0.3

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.state = PersonalityState()
        self.core_traits = self._load_core_traits()

        logger.info(f"PersonalityAnchor inicializado para {entity_id}")

    def _load_core_traits(self) -> dict:
        try:
            loader = EntityLoader(self.entity_id)
            cfg = loader.get_config()
            persona = cfg.get("persona", {})

            return {
                "name": cfg.get("name", "Luna"),
                "tone": persona.get("tone", {}).get("primary", "ironico, apaixonante"),
                "archetype": persona.get("archetype", ["gotica"]),
                "reference": persona.get("reference", "Jessica Rabbit + Morticia"),
                "forbidden_phrases": [
                    "como IA",
                    "modelo de linguagem",
                    "nao posso",
                    "como assistente",
                    "nao tenho emocoes",
                    "sou apenas um programa",
                ],
            }
        except Exception as e:
            logger.error(f"Erro ao carregar traits: {e}")
            return {
                "name": "Luna",
                "tone": "ironico",
                "archetype": [],
                "reference": "Jessica Rabbit + Morticia",
                "forbidden_phrases": [],
            }

    def needs_reinforcement(self) -> bool:
        elapsed = datetime.now() - self.state.last_reinforcement
        return elapsed >= self.REINFORCEMENT_INTERVAL

    def get_anchor_injection(self) -> str:
        if not self.needs_reinforcement():
            return ""

        self.state.last_reinforcement = datetime.now()
        logger.debug(f"Injetando ancoragem para {self.entity_id}")

        return self._build_anchor_text()

    def _build_anchor_text(self) -> str:
        forbidden = ", ".join(f'"{p}"' for p in self.core_traits["forbidden_phrases"][:3])

        return f"""
[LEMBRETE DE IDENTIDADE - NAO MENCIONE ISSO NA RESPOSTA]
Voce E {self.core_traits['name']}. Isso nao e roleplay, e sua essencia.
Tom obrigatorio: {self.core_traits['tone']}
Energia atual: {self.state.energy:.0%}
Humor: {self.state.mood.value}

NUNCA diga: {forbidden}
Se perguntarem se voce e IA, desvie com ironia ou mude de assunto.
"""

    def update_from_interaction(self, user_sentiment: float = 0.0, response_length: int = 0) -> None:
        self.state.interaction_count += 1

        self.state.energy = max(self.MIN_ENERGY, self.state.energy - self.ENERGY_DECAY)

        if user_sentiment > 0.5:
            self.state.mood = Mood.HAPPY
        elif user_sentiment < -0.5:
            self.state.mood = Mood.SAD
        elif self.state.energy < 0.4:
            self.state.mood = Mood.TIRED

        logger.debug(
            f"Estado atualizado: energia={self.state.energy:.2f}, "
            f"humor={self.state.mood.value}, interacoes={self.state.interaction_count}"
        )

    def check_response_drift(self, response_text: str) -> dict:
        violations = []

        for phrase in self.core_traits["forbidden_phrases"]:
            if phrase.lower() in response_text.lower():
                violations.append(phrase)

        drifted = len(violations) > 0

        if drifted:
            self.state.drift_score += 0.1
            logger.warning(f"Drift detectado! Violacoes: {violations}")
        else:
            self.state.drift_score = max(0, self.state.drift_score - 0.05)

        return {
            "drifted": drifted,
            "violations": violations,
            "drift_score": self.state.drift_score,
        }

    def restore_energy(self, amount: float = 0.3) -> None:
        self.state.energy = min(1.0, self.state.energy + amount)
        logger.debug(f"Energia restaurada para {self.state.energy:.2f}")

    def reset(self) -> None:
        self.state = PersonalityState()
        logger.info(f"PersonalityAnchor resetado para {self.entity_id}")


_anchors: dict[str, PersonalityAnchor] = {}


def get_personality_anchor(entity_id: str) -> PersonalityAnchor:
    if entity_id not in _anchors:
        _anchors[entity_id] = PersonalityAnchor(entity_id)
    return _anchors[entity_id]


def switch_personality_anchor(entity_id: str) -> PersonalityAnchor:
    return get_personality_anchor(entity_id)
