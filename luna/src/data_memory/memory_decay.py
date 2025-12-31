import math
from datetime import datetime

DECAY_RATES = {
    "user_info": 0.99,
    "preference": 0.95,
    "fact": 0.90,
    "event": 0.85,
    "emotion": 0.80,
    "context": 0.70,
    "default": 0.85,
}

HALF_LIFE_DAYS = {
    "user_info": 365,
    "preference": 90,
    "fact": 60,
    "event": 30,
    "emotion": 14,
    "context": 7,
    "default": 30,
}


def calculate_decay(timestamp: str, category: str = "default", reference_time: datetime | None = None) -> float:
    if reference_time is None:
        reference_time = datetime.now()

    try:
        if isinstance(timestamp, str):
            clean_ts = timestamp.replace("Z", "").replace("+00:00", "")
            mem_time = datetime.fromisoformat(clean_ts)
        else:
            mem_time = timestamp
    except (ValueError, TypeError):
        return 1.0

    if mem_time.tzinfo is not None:
        mem_time = mem_time.replace(tzinfo=None)
    if reference_time.tzinfo is not None:
        reference_time = reference_time.replace(tzinfo=None)

    age_days = (reference_time - mem_time).days

    if age_days <= 0:
        return 1.0

    half_life = HALF_LIFE_DAYS.get(category, HALF_LIFE_DAYS["default"])

    decay = math.pow(0.5, age_days / half_life)

    min_decay = 0.1
    return max(decay, min_decay)


def apply_decay_to_score(base_score: float, timestamp: str, category: str = "default") -> float:
    decay = calculate_decay(timestamp, category)
    return base_score * decay


def get_recency_boost(timestamp: str, boost_days: int = 3) -> float:
    try:
        clean_ts = timestamp.replace("Z", "").replace("+00:00", "")
        mem_time = datetime.fromisoformat(clean_ts)

        if mem_time.tzinfo is not None:
            mem_time = mem_time.replace(tzinfo=None)

        age_days = (datetime.now() - mem_time).days

        if age_days <= boost_days:
            return 1.0 + (0.2 * (boost_days - age_days) / boost_days)
        return 1.0
    except (ValueError, TypeError):
        return 1.0


def get_decay_factor_description(timestamp: str, category: str = "default") -> str:
    decay = calculate_decay(timestamp, category)
    if decay >= 0.9:
        return "muito recente"
    elif decay >= 0.7:
        return "recente"
    elif decay >= 0.5:
        return "moderado"
    elif decay >= 0.3:
        return "antigo"
    else:
        return "muito antigo"
