# TTS Strategy Pattern

## Visao Geral

O modulo `src/soul/boca/` foi refatorado para usar o **Strategy Pattern**, eliminando cadeias de if/elif e centralizando a logica de TTS em providers intercambiaveis.

## Arquitetura

```
src/soul/boca/
├── __init__.py
├── core.py              # Classe Boca (orquestrador)
├── engine_check.py      # Verificacao de engines disponiveis
├── playback.py          # Reproducao de audio
├── sanitizer.py         # Limpeza de texto
├── temp_audio.py        # Gerenciamento de arquivos temporarios
└── providers/
    ├── __init__.py
    ├── base.py          # TTSProvider (ABC) + TTSParams
    ├── coqui.py         # CoquiProvider
    ├── chatterbox.py    # ChatterboxProvider
    ├── elevenlabs.py    # ElevenLabsProvider
    └── daemon.py        # DaemonProvider
```

## Classes Principais

### TTSParams (dataclass)

Encapsula parametros de TTS:

```python
@dataclass
class TTSParams:
    speed: float = 1.0      # Velocidade da fala
    stability: float = 0.5  # Estabilidade (ElevenLabs)
    style: float = 0.0      # Exaggeration/style
    extra: dict = {}        # Parametros adicionais

    @classmethod
    def from_metatags(cls, metatags: dict | None) -> TTSParams:
        ...
```

### TTSProvider (ABC)

Interface abstrata para todos os providers:

```python
class TTSProvider(ABC):
    name: str = "base"
    priority: int = 0

    @property
    def is_available(self) -> bool

    @abstractmethod
    def check_availability(self) -> bool

    @abstractmethod
    def generate(self, text: str, params: TTSParams) -> str | None

    @abstractmethod
    def speak(self, text: str, params: TTSParams) -> bool

    def get_reference_audio(self) -> str | None
```

## Providers Implementados

| Provider | Priority | Descricao |
|----------|----------|-----------|
| DaemonProvider | 100 | TTS Daemon via Unix Socket (mais rapido) |
| ChatterboxProvider | 30 | Chatterbox local com voice cloning |
| CoquiProvider | 20 | Coqui XTTS local |
| ElevenLabsProvider | 10 | API ElevenLabs (cloud) |

## Fluxo de Execucao

1. `Boca.__init__()` verifica engines disponiveis
2. `_init_providers()` cria lista ordenada por prioridade
3. Daemon sempre tem prioridade maxima (se disponivel)
4. Provider preferido (config) vem em segundo
5. Demais providers por ordem de prioridade

```python
def _gerar_audio_interno(self, texto: str, metatags: dict = None) -> str | None:
    texto = sanitize_text(texto)
    params = TTSParams.from_metatags(metatags)

    for provider in self._providers:
        path = provider.generate(texto, params)
        if path:
            return path

    return None
```

## Beneficios

1. **Open/Closed Principle**: Adicionar novo provider = criar nova classe
2. **Single Responsibility**: Cada provider cuida apenas de sua engine
3. **Fallback automatico**: Itera providers ate encontrar um funcional
4. **Testabilidade**: Mocks simples via injecao de dependencia
5. **Configurabilidade**: Ordem de providers via config

## Adicionar Novo Provider

```python
from src.soul.boca.providers.base import TTSParams, TTSProvider

class NovoProvider(TTSProvider):
    name = "novo"
    priority = 25  # Entre coqui (20) e chatterbox (30)

    def check_availability(self) -> bool:
        # Verificar dependencias
        self._available = True
        return self._available

    def generate(self, text: str, params: TTSParams) -> str | None:
        if not self._available:
            return None
        # Gerar audio e retornar path
        return "/tmp/audio.wav"

    def speak(self, text: str, params: TTSParams) -> bool:
        path = self.generate(text, params)
        if path:
            from src.soul.boca.playback import play_audio_file
            return play_audio_file(self._boca, path)
        return False
```

## Testes

45 testes em `src/tests/test_tts_providers.py`:

- TestTTSParams: 6 testes
- TestTTSProviderBase: 3 testes
- TestCoquiProvider: 9 testes
- TestChatterboxProvider: 4 testes
- TestElevenLabsProvider: 6 testes
- TestDaemonProvider: 10 testes
- TestBocaIntegration: 5 testes
- TestProviderOrdering: 1 teste

## Dependencias

- `requests` (ElevenLabs API)
- `subprocess` (Coqui/Chatterbox wrappers)
- `socket` (TTS Daemon)
- `tempfile` (audio temporario)

## Metricas de Performance

Cada provider tem decorator `@perf_monitor`:

```python
@perf_monitor("tts.provider.coqui.generate")
def generate(self, text: str, params: TTSParams) -> str | None:
    ...
```

Metricas coletadas:
- Tempo de geracao
- Taxa de sucesso
- Fallbacks utilizados
