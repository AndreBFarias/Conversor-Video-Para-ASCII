# Dependency Injection - Sistema de Injecao de Dependencias

## Visao Geral

O modulo `src/core/di/` implementa um container de injecao de dependencias (DI) que permite desacoplar classes de suas implementacoes concretas. Isso facilita testes unitarios e permite trocar implementacoes sem modificar codigo consumidor.

## Problema Resolvido

Antes da DI, o codigo tinha tight coupling:

```python
# ANTES: Tight coupling
class Consciencia:
    def __init__(self):
        self.memory = SmartMemory()           # Instanciacao direta
        self.llm = OllamaClient()             # Impossivel mockar
        import config                          # Import global
        self.model = config.CHAT_LOCAL["model"]
```

Isso tornava testes unitarios impossiveis sem carregar todo o sistema.

## Arquitetura

```
src/core/di/
├── __init__.py          # Exports publicos
├── protocols.py         # Interfaces (Protocols)
├── container.py         # ServiceContainer
├── providers.py         # Factories de servicos reais
└── adapters.py          # Adapters para classes existentes
```

## Protocols (Interfaces)

Cada servico principal tem uma interface definida:

| Protocol | Descricao |
|----------|-----------|
| `IConfigProvider` | Acesso a configuracoes |
| `IMemoryStore` | Armazenamento de memorias |
| `ILLMClient` | Cliente de LLM (Ollama, Gemini) |
| `ITTSEngine` | Motor de TTS |
| `IVisionProvider` | Analise de imagens |
| `IContextBuilder` | Construcao de contexto |
| `ISemanticCache` | Cache semantico |
| `IRateLimiter` | Limitador de taxa |
| `IEntityLoader` | Carregador de entidades |
| `IAnimationController` | Controlador de animacoes |
| `IAudioPlayer` | Player de audio |
| `IConsciencia` | Processador LLM principal |
| `IBoca` | Engine de TTS |
| `IVisao` | Analise visual |
| `IOuvido` | Transcricao de voz |
| `ISessionManager` | Gerenciador de sessoes |
| `ILogger` | Logger |

## ServiceContainer

O container suporta tres lifetimes:

| Lifetime | Comportamento |
|----------|---------------|
| `SINGLETON` | Uma instancia para toda aplicacao |
| `TRANSIENT` | Nova instancia a cada resolucao |
| `SCOPED` | Uma instancia por escopo (pode ser limpo) |

## Uso Basico

### Registrar Servicos

```python
from src.core.di import ServiceContainer, ServiceLifetime

container = ServiceContainer.get_instance()

# Factory function
container.register("config", lambda c: ConfigProviderAdapter(), ServiceLifetime.SINGLETON)

# Instancia direta
container.register_instance("logger", my_logger)
```

### Resolver Servicos

```python
# Resolucao direta
config = container.resolve("config")

# Property shortcuts
config = container.config
memory = container.memory
llm = container.llm
```

### Override para Testes

```python
# Em testes
container.override_instance("llm", MockLLMClient())
container.override("memory", lambda c: FakeMemoryStore())
```

## Inicializacao

O bootstrap.py inicializa o container automaticamente:

```python
from src.app.bootstrap import initialize_application, get_service_container

logger, gemini_error = initialize_application()

# Container ja inicializado com servicos padrao
container = get_service_container()
```

## Decorator @inject

Injeta dependencias automaticamente em funcoes:

```python
from src.core.di import inject

@inject("config")
def get_model_name(config=None):
    return config.get("model_name")

# Chamada normal - config injetado automaticamente
name = get_model_name()

# Override manual
name = get_model_name(config=custom_config)
```

## Exemplo de Teste com DI

```python
import pytest
from src.core.di import ServiceContainer

@pytest.fixture(autouse=True)
def reset_container():
    ServiceContainer.reset()
    yield
    ServiceContainer.reset()

def test_with_mock_llm():
    container = ServiceContainer.get_instance()

    # Mock LLM que sempre retorna resposta fixa
    class MockLLM:
        def generate(self, prompt, **kwargs):
            return "Mocked response"

        @property
        def model_name(self):
            return "mock"

        @property
        def provider_name(self):
            return "test"

    container.override_instance("llm", MockLLM())

    # Codigo sob teste usa o mock
    llm = container.llm
    response = llm.generate("test")

    assert response == "Mocked response"
```

## Servicos Registrados por Padrao

| Servico | Provider | Lifetime |
|---------|----------|----------|
| `config` | ConfigProviderAdapter | SINGLETON |
| `memory` | get_entity_smart_memory | SINGLETON |
| `llm` | LLMClientAdapter | SINGLETON |
| `tts` | TTSEngineAdapter | SINGLETON |
| `vision` | VisionProviderAdapter | SINGLETON |
| `context_builder` | get_context_builder | SINGLETON |
| `cache` | SemanticCache | SINGLETON |
| `rate_limiter` | SmartRateLimiter | SINGLETON |
| `entity_loader` | EntityLoader | SINGLETON |
| `logger` | get_logger | SINGLETON |
| `consciencia_factory` | Factory function | SINGLETON |
| `boca_factory` | Factory function | SINGLETON |
| `visao_factory` | Factory function | SINGLETON |
| `ouvido_factory` | Factory function | SINGLETON |
| `session_manager_factory` | Factory function | SINGLETON |
| `animation_controller_factory` | Factory function | SINGLETON |

## TemploDaAlma com DI

O `TemploDaAlma` aceita um container opcional e dependencias diretas:

```python
from src.app import TemploDaAlma
from src.app.bootstrap import get_service_container

# Opcao 1: Usar container (producao)
container = get_service_container()
app = TemploDaAlma(container=container)

# Opcao 2: Injetar mocks diretos (testes)
app = TemploDaAlma(
    consciencia=MockConsciencia(),
    boca=MockBoca(),
    visao=MockVisao(),
)

# Opcao 3: Override via container (testes)
container.override("consciencia_factory", lambda c: lambda app: MockConsciencia(app))
app = TemploDaAlma(container=container)
```

Factories seguem o padrao:
- `consciencia_factory(app)` - recebe app
- `boca_factory()` - sem argumentos
- `visao_factory()` - sem argumentos
- `ouvido_factory()` - retorna None se voz indisponivel

## Migracao Gradual

O sistema permite migracao gradual. Codigo antigo continua funcionando:

```python
# AINDA FUNCIONA (mas evitar em codigo novo)
from src.data_memory.smart_memory import get_entity_smart_memory
memory = get_entity_smart_memory("luna")

# PREFERIDO (usa DI)
from src.core.di import get_container
memory = get_container().memory
```

## Testes

42 testes no total:

### test_di_container.py (24 testes)
- TestServiceLifetime: 1 teste
- TestServiceContainer: 13 testes
- TestGetContainer: 1 teste
- TestScopedServices: 2 testes
- TestInjectDecorator: 2 testes
- TestPropertyAccessors: 3 testes
- TestServiceDescriptor: 2 testes

### test_templo_di.py (18 testes)
- TestTemploDaAlmaWithContainer: 2 testes
- TestTemploDaAlmaDirectInjection: 5 testes
- TestTemploDaAlmaBackwardCompatibility: 2 testes
- TestContainerFactoryOverride: 3 testes
- TestContainerPropertyAccessors: 2 testes
- TestNewProtocols: 4 testes
