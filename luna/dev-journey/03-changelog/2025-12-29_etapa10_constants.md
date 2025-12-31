# 2025-12-29: ETAPA 10 - Documentar Constantes Magicas

## Objetivo
Centralizar magic numbers em arquivo documentado com classes organizadas por dominio.

## Arquivo Criado

### src/core/constants.py (~180 linhas)
Modulo com 10 classes de constantes documentadas:

#### MemoryConstants
- `SIMILARITY_THRESHOLD`: 0.35 - Threshold minimo para memoria relevante
- `DEDUP_THRESHOLD`: 0.92 - Detecta memorias duplicadas
- `MIN_SIMILARITY`: 0.40 - Similaridade minima para contexto
- `MIN_TEXT_LENGTH`: 20 - Tamanho minimo de texto
- `MAX_CONTEXT_CHARS`: 800 - Max caracteres de contexto
- `DECAY_MIN/LOW/MEDIUM/HIGH`: Thresholds de decaimento
- `ADAPTIVE_THRESHOLD_SHORT/LONG`: Thresholds adaptativos por tamanho de query

#### CacheConstants
- `L1_TTL_SECONDS`: 7200 (2 horas)
- `L2_TTL_SECONDS`: 86400 (24 horas)
- `MAX_SIZE`: 200 - Tamanho do cache L1
- `SIMILARITY_THRESHOLD`: 0.85 - Para cache hit
- `ENTITY_CACHE_MAX_SIZE`: 300
- `ENTITY_CACHE_TTL`: 3600 (1 hora)

#### AudioConstants
- `SAMPLE_RATE`: 16000 Hz
- `NATIVE_SAMPLE_RATE`: 48000 Hz
- `CHANNELS`: 1 (mono)
- `MAX_CONSECUTIVE_ERRORS`: 10
- `TTS_TIMEOUT`: 60 segundos
- `DAEMON_TIMEOUT`: 30 segundos

#### TTSConstants
- `DEFAULT_SPEED/STABILITY/STYLE`: Valores padrao para TTS
- `ONBOARDING_*`: Valores especificos para onboarding

#### CircuitBreakerConstants
- `MAX_FAILURES`: 3 - Falhas para abrir circuito
- `RESET_TIMEOUT`: 60 segundos
- `HALF_OPEN_SUCCESSES`: 2

#### PersonalityConstants
- `REINFORCEMENT_INTERVAL`: 5 mensagens
- `EMOTION_DECAY_RATE`: 0.1
- `PROACTIVE_BASE_CHANCE`: 0.02

#### EmbeddingConstants
- `DIMENSION`: 384 - Dimensao dos vetores

#### SessionConstants
- `SUMMARY_INTERVAL`: 2 mensagens
- `CONSOLIDATION_INTERVAL_MINUTES`: 30

#### VisionConstants
- `CHANGE_THRESHOLD`: 15
- `HISTOGRAM_THRESHOLD`: 0.7
- `CACHE_TTL`: 120 segundos
- `FACE_TOLERANCE`: 0.6

#### EmotionalConstants
- `NEUTRAL_SCORE`: 0.5
- `HIGH/MEDIUM/LOW_CONFIDENCE`: Thresholds de confianca

## Arquivos Modificados

### src/data_memory/smart_memory.py
- Import: `from src.core.constants import MemoryConstants`
- Substituidos: MAX_CONTEXT_CHARS, SIMILARITY_THRESHOLD, ADAPTIVE_THRESHOLD_*

### src/soul/semantic_cache.py
- Import: `from src.core.constants import CacheConstants`
- Substituidos: SIMILARITY_THRESHOLD, MAX_SIZE, L1_TTL_SECONDS

### src/data_memory/entity_memory.py
- Import: `from src.core.constants import CacheConstants, MemoryConstants`
- Substituidos: ENTITY_CACHE_*, MIN_TEXT_LENGTH, DEDUP_THRESHOLD, MIN_SIMILARITY

## Testes Criados

### src/tests/test_constants.py (27 testes)
- TestMemoryConstants: 5 testes
- TestCacheConstants: 3 testes
- TestAudioConstants: 3 testes
- TestTTSConstants: 2 testes
- TestCircuitBreakerConstants: 3 testes
- TestPersonalityConstants: 3 testes
- TestEmbeddingConstants: 1 teste
- TestSessionConstants: 2 testes
- TestVisionConstants: 2 testes
- TestEmotionalConstants: 2 testes
- TestConstantsIntegration: 1 teste

## Beneficios

1. **Documentacao**: Cada constante tem docstring explicando seu proposito
2. **Centralizacao**: Um unico arquivo para ajustar todos os thresholds
3. **Tipagem**: Uso de `Final` para indicar imutabilidade
4. **Organizacao**: Classes separadas por dominio
5. **Testabilidade**: Testes validam ranges e relacoes entre constantes

## Validacao

- [x] constants.py criado com 10 classes
- [x] 27 testes passando
- [x] Arquivos atualizados para usar constantes
- [x] Pre-commit passa
