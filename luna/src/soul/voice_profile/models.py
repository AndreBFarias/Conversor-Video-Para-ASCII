from dataclasses import dataclass

import numpy as np


@dataclass
class VoiceProfile:
    name: str
    embedding: np.ndarray | None = None
    created_at: str = ""
    updated_at: str = ""
    sample_count: int = 0
