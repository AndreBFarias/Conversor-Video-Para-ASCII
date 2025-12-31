"""
UserProfiler - Sistema de perfil de usuario

Este modulo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/user_profiler/
"""

from src.soul.user_profiler import (
    DIMINUTIVOS_COMUNS,
    NOMES_FEMININOS,
    NOMES_MASCULINOS,
    NOMES_NEUTROS,
    ORIGENS_CULTURAIS,
    NameAnalysis,
    NameAnalyzer,
    PhotoAnalyzer,
    ProfileStorage,
    UserProfile,
    UserProfiler,
    VisualAnalysis,
    VoiceAnalysis,
    get_user_profiler,
)

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
