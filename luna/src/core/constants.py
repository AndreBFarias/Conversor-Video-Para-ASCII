"""
Constantes centralizadas do projeto Luna.

Este modulo centraliza todos os magic numbers e thresholds usados
no projeto, facilitando ajustes e documentacao.

Uso:
    from src.core.constants import MemoryConstants, CacheConstants

    threshold = MemoryConstants.SIMILARITY_THRESHOLD
    max_size = CacheConstants.MAX_SIZE
"""

from typing import Final


class MemoryConstants:
    """Constantes relacionadas ao sistema de memoria."""

    SIMILARITY_THRESHOLD: Final[float] = 0.35
    """Threshold minimo de similaridade para considerar uma memoria relevante."""

    DEDUP_THRESHOLD: Final[float] = 0.92
    """Threshold para detectar memorias duplicadas (muito similares)."""

    MIN_SIMILARITY: Final[float] = 0.40
    """Similaridade minima para incluir memoria no contexto."""

    MIN_TEXT_LENGTH: Final[int] = 20
    """Tamanho minimo de texto para ser armazenado como memoria."""

    MAX_CONTEXT_CHARS: Final[int] = 800
    """Maximo de caracteres de contexto de memoria por requisicao."""

    MAX_CONTEXT_TOKENS: Final[int] = 800
    """Maximo de tokens de contexto de memoria."""

    DECAY_MIN: Final[float] = 0.1
    """Valor minimo de decay (memoria nunca esquece totalmente)."""

    DECAY_HIGH: Final[float] = 0.9
    """Threshold para memoria considerada muito recente."""

    DECAY_MEDIUM: Final[float] = 0.7
    """Threshold para memoria considerada recente."""

    DECAY_LOW: Final[float] = 0.5
    """Threshold para memoria considerada antiga."""

    CATEGORY_BOOST: Final[float] = 0.7
    """Boost aplicado quando categoria da memoria combina com query."""

    ADAPTIVE_THRESHOLD_SHORT: Final[float] = 0.10
    """Threshold adaptativo para queries curtas (<5 palavras)."""

    ADAPTIVE_THRESHOLD_LONG: Final[float] = 0.20
    """Threshold adaptativo para queries longas (>=5 palavras)."""

    RELEVANCE_THRESHOLD: Final[float] = 0.2
    """Threshold minimo de relevancia para incluir memoria."""

    COMPACT_DAYS: Final[int] = 30
    """Dias apos os quais memorias sao compactadas."""


class CacheConstants:
    """Constantes relacionadas ao sistema de cache."""

    L1_TTL_SECONDS: Final[int] = 7200
    """TTL do cache L1 em segundos (2 horas)."""

    L2_TTL_SECONDS: Final[int] = 86400
    """TTL do cache L2 (SQLite) em segundos (24 horas)."""

    MAX_SIZE: Final[int] = 200
    """Tamanho maximo do cache L1 em entradas."""

    SIMILARITY_THRESHOLD: Final[float] = 0.85
    """Threshold de similaridade para cache hit."""

    ENTITY_CACHE_MAX_SIZE: Final[int] = 300
    """Tamanho maximo do cache de entidades."""

    ENTITY_CACHE_TTL: Final[int] = 3600
    """TTL do cache de entidades em segundos (1 hora)."""

    TEXT_PREVIEW_LENGTH: Final[int] = 100
    """Tamanho do preview de texto armazenado no cache."""


class AudioConstants:
    """Constantes relacionadas ao sistema de audio."""

    SAMPLE_RATE: Final[int] = 16000
    """Taxa de amostragem padrao para audio (16kHz)."""

    NATIVE_SAMPLE_RATE: Final[int] = 48000
    """Taxa de amostragem nativa de alguns dispositivos."""

    CHANNELS: Final[int] = 1
    """Numero de canais de audio (mono)."""

    MAX_CONSECUTIVE_ERRORS: Final[int] = 10
    """Maximo de erros consecutivos antes de parar thread de audio."""

    WARMUP_FRAMES: Final[int] = 10
    """Frames de warmup antes de processar audio."""

    TTS_TIMEOUT: Final[int] = 60
    """Timeout para geracao de TTS em segundos."""

    DAEMON_TIMEOUT: Final[float] = 30.0
    """Timeout para comunicacao com daemon TTS."""

    RESPONSE_TIMEOUT: Final[float] = 0.1
    """Timeout para obter resposta em modo live."""


class TTSConstants:
    """Constantes relacionadas a sintese de voz."""

    DEFAULT_SPEED: Final[float] = 1.0
    """Velocidade padrao de fala."""

    DEFAULT_STABILITY: Final[float] = 0.5
    """Estabilidade padrao (ElevenLabs)."""

    DEFAULT_STYLE: Final[float] = 0.0
    """Estilo padrao (ElevenLabs)."""

    DEFAULT_EXAGGERATION: Final[float] = 0.5
    """Exageracao padrao (Chatterbox)."""

    ONBOARDING_STABILITY: Final[float] = 0.3
    """Estabilidade para falas de onboarding."""

    ONBOARDING_STYLE: Final[float] = 0.65
    """Estilo para falas de onboarding."""

    ONBOARDING_SPEED: Final[float] = 1.15
    """Velocidade para falas de onboarding."""

    ELEVENLABS_SIMILARITY: Final[float] = 0.85
    """Similaridade padrao para ElevenLabs."""


class CircuitBreakerConstants:
    """Constantes relacionadas ao circuit breaker."""

    MAX_FAILURES: Final[int] = 3
    """Numero de falhas para abrir o circuito."""

    RESET_TIMEOUT: Final[float] = 60.0
    """Tempo para tentar resetar o circuito (segundos)."""

    HALF_OPEN_SUCCESSES: Final[int] = 2
    """Sucessos necessarios em half-open para fechar circuito."""


class PersonalityConstants:
    """Constantes relacionadas a personalidade da entidade."""

    REINFORCEMENT_INTERVAL: Final[int] = 5
    """Mensagens entre reforcos de personalidade."""

    EMOTION_DECAY_RATE: Final[float] = 0.1
    """Taxa de decaimento emocional por interacao."""

    PROACTIVE_BASE_CHANCE: Final[float] = 0.02
    """Chance base de interacao espontanea."""


class EmbeddingConstants:
    """Constantes relacionadas a embeddings."""

    DIMENSION: Final[int] = 384
    """Dimensao dos vetores de embedding."""


class SessionConstants:
    """Constantes relacionadas a sessoes."""

    SUMMARY_INTERVAL: Final[int] = 2
    """Intervalo de mensagens para gerar resumo."""

    CONSOLIDATION_INTERVAL_MINUTES: Final[int] = 30
    """Intervalo para consolidacao de memoria em minutos."""


class VisionConstants:
    """Constantes relacionadas ao sistema de visao."""

    CHANGE_THRESHOLD: Final[int] = 15
    """Threshold para detectar mudanca na imagem."""

    HISTOGRAM_THRESHOLD: Final[float] = 0.7
    """Threshold de histograma para comparacao de imagens."""

    CACHE_TTL: Final[int] = 120
    """TTL do cache de visao em segundos."""

    MAX_CACHE_SIZE: Final[int] = 20
    """Tamanho maximo do cache de visao."""

    FACE_TOLERANCE: Final[float] = 0.6
    """Tolerancia para identificacao facial."""


class EmotionalConstants:
    """Constantes relacionadas ao sistema emocional."""

    NEUTRAL_SCORE: Final[float] = 0.5
    """Score padrao para emocao neutra."""

    HIGH_CONFIDENCE: Final[float] = 0.8
    """Threshold para alta confianca emocional."""

    MEDIUM_CONFIDENCE: Final[float] = 0.5
    """Threshold para media confianca emocional."""

    LOW_CONFIDENCE: Final[float] = 0.2
    """Threshold para baixa confianca emocional."""

    PROACTIVE_MIN_SCORE: Final[float] = 0.5
    """Score minimo para recall proativo."""
