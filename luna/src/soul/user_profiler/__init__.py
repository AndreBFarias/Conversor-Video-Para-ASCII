from src.soul.user_profiler.constants import (
    DIMINUTIVOS_COMUNS,
    NOMES_FEMININOS,
    NOMES_MASCULINOS,
    NOMES_NEUTROS,
    ORIGENS_CULTURAIS,
)
from src.soul.user_profiler.core import UserProfiler
from src.soul.user_profiler.models import NameAnalysis, UserProfile, VisualAnalysis, VoiceAnalysis
from src.soul.user_profiler.name_analyzer import NameAnalyzer
from src.soul.user_profiler.photo_analyzer import PhotoAnalyzer
from src.soul.user_profiler.storage import ProfileStorage

_profiler: UserProfiler | None = None


def get_user_profiler() -> UserProfiler:
    global _profiler
    if _profiler is None:
        _profiler = UserProfiler()
    return _profiler


__all__ = [
    "NameAnalysis",
    "VisualAnalysis",
    "VoiceAnalysis",
    "UserProfile",
    "UserProfiler",
    "NameAnalyzer",
    "PhotoAnalyzer",
    "ProfileStorage",
    "get_user_profiler",
    "NOMES_FEMININOS",
    "NOMES_MASCULINOS",
    "NOMES_NEUTROS",
    "ORIGENS_CULTURAIS",
    "DIMINUTIVOS_COMUNS",
]
