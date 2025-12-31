from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelSize(Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


@dataclass
class ModelProfile:
    name: str
    context_window: int
    size: ModelSize
    tokens_per_char: float = 0.25
    supports_streaming: bool = True
    supports_system_prompt: bool = True

    @property
    def effective_context(self) -> int:
        return int(self.context_window * 0.9)

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) * self.tokens_per_char)


MODEL_PROFILES: dict[str, ModelProfile] = {
    "llama3.2": ModelProfile(
        name="llama3.2",
        context_window=8192,
        size=ModelSize.SMALL,
        tokens_per_char=0.28,
    ),
    "llama3.2:1b": ModelProfile(
        name="llama3.2:1b",
        context_window=8192,
        size=ModelSize.TINY,
        tokens_per_char=0.28,
    ),
    "llama3.2:3b": ModelProfile(
        name="llama3.2:3b",
        context_window=8192,
        size=ModelSize.SMALL,
        tokens_per_char=0.28,
    ),
    "llama3.1:8b": ModelProfile(
        name="llama3.1:8b",
        context_window=32768,
        size=ModelSize.MEDIUM,
        tokens_per_char=0.28,
    ),
    "gemma2:2b": ModelProfile(
        name="gemma2:2b",
        context_window=8192,
        size=ModelSize.TINY,
        tokens_per_char=0.30,
    ),
    "gemma2:9b": ModelProfile(
        name="gemma2:9b",
        context_window=8192,
        size=ModelSize.MEDIUM,
        tokens_per_char=0.30,
    ),
    "phi3:mini": ModelProfile(
        name="phi3:mini",
        context_window=4096,
        size=ModelSize.TINY,
        tokens_per_char=0.25,
    ),
    "mistral:7b": ModelProfile(
        name="mistral:7b",
        context_window=32768,
        size=ModelSize.MEDIUM,
        tokens_per_char=0.27,
    ),
    "gemini-2.0-flash": ModelProfile(
        name="gemini-2.0-flash",
        context_window=1048576,
        size=ModelSize.XLARGE,
        tokens_per_char=0.25,
    ),
    "gemini-2.0-flash-lite": ModelProfile(
        name="gemini-2.0-flash-lite",
        context_window=1048576,
        size=ModelSize.LARGE,
        tokens_per_char=0.25,
    ),
    "gemini-1.5-pro": ModelProfile(
        name="gemini-1.5-pro",
        context_window=2097152,
        size=ModelSize.XLARGE,
        tokens_per_char=0.25,
    ),
    "gpt-4o": ModelProfile(
        name="gpt-4o",
        context_window=128000,
        size=ModelSize.XLARGE,
        tokens_per_char=0.25,
    ),
    "gpt-4o-mini": ModelProfile(
        name="gpt-4o-mini",
        context_window=128000,
        size=ModelSize.LARGE,
        tokens_per_char=0.25,
    ),
}

DEFAULT_PROFILE = ModelProfile(
    name="default",
    context_window=4096,
    size=ModelSize.SMALL,
    tokens_per_char=0.25,
)


def get_model_profile(model_name: str) -> ModelProfile:
    base_name = model_name.split(":")[0] if ":" in model_name else model_name

    if model_name in MODEL_PROFILES:
        return MODEL_PROFILES[model_name]

    if base_name in MODEL_PROFILES:
        return MODEL_PROFILES[base_name]

    for key, profile in MODEL_PROFILES.items():
        if base_name.lower() in key.lower():
            return profile

    return DEFAULT_PROFILE


@dataclass
class BudgetAllocation:
    system_prompt_pct: float = 0.25
    memory_pct: float = 0.20
    conversation_pct: float = 0.40
    user_input_pct: float = 0.10
    reserve_pct: float = 0.05


@dataclass
class HistoryLimits:
    max_turns: int = 10
    max_chars_per_turn: int = 300
    summary_threshold_pct: float = 0.80
    summary_compress_pct: float = 0.30


@dataclass
class ContextWindowConfig:
    model_profile: ModelProfile = field(default_factory=lambda: DEFAULT_PROFILE)
    budget_allocation: BudgetAllocation = field(default_factory=BudgetAllocation)
    history_limits: HistoryLimits = field(default_factory=HistoryLimits)

    memory_max_chars: int = 600
    enable_progressive_summary: bool = True
    enable_emotional_context: bool = True
    enable_proactive_recall: bool = True

    @property
    def total_budget(self) -> int:
        return self.model_profile.effective_context

    @property
    def system_prompt_budget(self) -> int:
        return int(self.total_budget * self.budget_allocation.system_prompt_pct)

    @property
    def memory_budget(self) -> int:
        return int(self.total_budget * self.budget_allocation.memory_pct)

    @property
    def conversation_budget(self) -> int:
        return int(self.total_budget * self.budget_allocation.conversation_pct)

    @property
    def user_input_budget(self) -> int:
        return int(self.total_budget * self.budget_allocation.user_input_pct)

    @property
    def summary_threshold(self) -> int:
        return int(self.total_budget * self.history_limits.summary_threshold_pct)

    def adjust_for_size(self) -> None:
        size = self.model_profile.size

        if size == ModelSize.TINY:
            self.history_limits.max_turns = 3
            self.history_limits.max_chars_per_turn = 100
            self.memory_max_chars = 300
        elif size == ModelSize.SMALL:
            self.history_limits.max_turns = 5
            self.history_limits.max_chars_per_turn = 150
            self.memory_max_chars = 400
        elif size == ModelSize.MEDIUM:
            self.history_limits.max_turns = 10
            self.history_limits.max_chars_per_turn = 300
            self.memory_max_chars = 600
        elif size == ModelSize.LARGE:
            self.history_limits.max_turns = 20
            self.history_limits.max_chars_per_turn = 500
            self.memory_max_chars = 1000
        elif size == ModelSize.XLARGE:
            self.history_limits.max_turns = 50
            self.history_limits.max_chars_per_turn = 1000
            self.memory_max_chars = 2000

    def get_budget_summary(self) -> dict[str, Any]:
        return {
            "model": self.model_profile.name,
            "size": self.model_profile.size.value,
            "context_window": self.model_profile.context_window,
            "effective_context": self.total_budget,
            "budgets": {
                "system_prompt": self.system_prompt_budget,
                "memory": self.memory_budget,
                "conversation": self.conversation_budget,
                "user_input": self.user_input_budget,
            },
            "limits": {
                "max_turns": self.history_limits.max_turns,
                "max_chars_per_turn": self.history_limits.max_chars_per_turn,
                "memory_max_chars": self.memory_max_chars,
            },
        }


_context_configs: dict[str, ContextWindowConfig] = {}


def get_context_config(model_name: str) -> ContextWindowConfig:
    if model_name not in _context_configs:
        profile = get_model_profile(model_name)
        config = ContextWindowConfig(model_profile=profile)
        config.adjust_for_size()
        _context_configs[model_name] = config
    return _context_configs[model_name]
