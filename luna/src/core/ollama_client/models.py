from dataclasses import dataclass


@dataclass
class OllamaResponse:
    text: str
    model: str
    done: bool
    total_duration: int | None = None
    eval_count: int | None = None
    error: str | None = None
