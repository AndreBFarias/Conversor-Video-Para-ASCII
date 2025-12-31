import re
from datetime import datetime, timedelta
from enum import Enum, auto

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ConversationState(Enum):
    IDLE = auto()
    GREETING = auto()
    CHAT = auto()
    TASK = auto()
    DEEP_TALK = auto()
    FLIRT = auto()
    CONFLICT = auto()
    FAREWELL = auto()


STATE_PATTERNS = {
    ConversationState.GREETING: [
        r"\b(oi|ola|hey|eae|salve|bom dia|boa tarde|boa noite)\b",
        r"\b(tudo bem|como vai|e ai)\b",
    ],
    ConversationState.TASK: [
        r"\b(faz|faca|cria|crie|escreve|escreva|programa|code|implementa)\b",
        r"\b(preciso que|pode|poderia|consegue)\b.*\b(fazer|criar|ajudar)\b",
        r"\b(bug|erro|problema|issue|fix)\b",
    ],
    ConversationState.DEEP_TALK: [
        r"\b(sinto|sentindo|deprimid|trist|ansios|preocupad)\b",
        r"\b(vida|morte|sentido|existencia|proposito)\b",
        r"\b(desabafar|conversar serio|preciso falar)\b",
    ],
    ConversationState.FLIRT: [
        r"\b(linda|lindo|gata|gato|bonita|bonito|sexy)\b",
        r"\b(te amo|te adoro|apaixonad|amor)\b",
        r"\b(beijo|abraco|carinho|saudade)\b",
    ],
    ConversationState.CONFLICT: [
        r"\b(discordo|errad|mentira|nao concordo)\b",
        r"\b(raiva|irritad|frustrad|odei)\b",
        r"\b(voce nao entende|isso e ridiculo)\b",
    ],
    ConversationState.FAREWELL: [r"\b(tchau|adeus|ate|falou|flw|bye)\b", r"\b(vou dormir|tenho que ir|preciso ir)\b"],
}


class ConversationStateMachine:
    def __init__(self):
        self.current_state = ConversationState.IDLE
        self.state_history: list[dict] = []
        self.state_start_time: datetime = datetime.now()
        self.turn_count: int = 0

    def detect_state(self, user_input: str) -> ConversationState:
        input_lower = user_input.lower()

        scores = {state: 0 for state in ConversationState}

        for state, patterns in STATE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    scores[state] += 1

        max_score = max(scores.values())
        if max_score > 0:
            for state, score in scores.items():
                if score == max_score:
                    return state

        if self.turn_count < 2:
            return ConversationState.GREETING

        return ConversationState.CHAT

    def transition(self, user_input: str) -> dict:
        previous_state = self.current_state
        detected_state = self.detect_state(user_input)

        if detected_state != self.current_state:
            self.state_history.append(
                {
                    "from": self.current_state.name,
                    "to": detected_state.name,
                    "timestamp": datetime.now().isoformat(),
                    "trigger": user_input[:50],
                }
            )

            self.current_state = detected_state
            self.state_start_time = datetime.now()

            logger.info(f"State transition: {previous_state.name} -> {detected_state.name}")

        self.turn_count += 1

        return {
            "previous": previous_state.name,
            "current": self.current_state.name,
            "changed": previous_state != self.current_state,
            "turn": self.turn_count,
        }

    def get_state_context(self) -> str:
        state_hints = {
            ConversationState.IDLE: "",
            ConversationState.GREETING: "[Cumprimente de forma acolhedora]",
            ConversationState.CHAT: "[Conversa casual, seja natural]",
            ConversationState.TASK: "[Foco em resolver a tarefa]",
            ConversationState.DEEP_TALK: "[Seja empatica e atenciosa]",
            ConversationState.FLIRT: "[Pode ser sedutora e provocante]",
            ConversationState.CONFLICT: "[Mantenha a calma, seja assertiva]",
            ConversationState.FAREWELL: "[Despedida carinhosa]",
        }

        return state_hints.get(self.current_state, "")

    def get_state_duration(self) -> timedelta:
        return datetime.now() - self.state_start_time

    def get_history(self) -> list[dict]:
        return self.state_history.copy()

    def reset(self):
        self.current_state = ConversationState.IDLE
        self.state_history = []
        self.turn_count = 0
        self.state_start_time = datetime.now()


_state_machine: ConversationStateMachine | None = None


def get_conversation_state_machine() -> ConversationStateMachine:
    global _state_machine
    if _state_machine is None:
        _state_machine = ConversationStateMachine()
    return _state_machine


def reset_conversation_state():
    global _state_machine
    if _state_machine:
        _state_machine.reset()
