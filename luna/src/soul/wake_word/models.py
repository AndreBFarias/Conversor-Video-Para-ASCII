from dataclasses import dataclass


@dataclass
class WakeWordConfig:
    patterns: list
    cooldown: float
    sample_rate: int
