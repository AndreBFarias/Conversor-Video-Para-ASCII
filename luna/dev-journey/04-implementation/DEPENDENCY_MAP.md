# Mapa de Dependencias do Projeto Luna

## Visao Geral da Arquitetura

```
                    +----------------+
                    |   main.py      |
                    +-------+--------+
                            |
                    +-------v--------+
                    |  src/app/      |
                    | TemploDaAlma   |
                    +-------+--------+
                            |
        +-------------------+-------------------+
        |                   |                   |
+-------v--------+  +-------v--------+  +-------v--------+
|  src/soul/     |  |  src/core/     |  |  src/ui/       |
| Consciencia    |  | EntityLoader   |  | Widgets        |
| Boca, Visao    |  | Animation      |  | Screens        |
+-------+--------+  +-------+--------+  +----------------+
        |                   |
        +-------------------+
                |
        +-------v--------+
        | src/data_memory|
        | SmartMemory    |
        | VectorStore    |
        +----------------+
```

## Modulos Principais

### 1. src/app/ - Camada de Aplicacao

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `luna_app.py` | App principal Textual (TemploDaAlma) | soul/, core/, ui/, controllers/ |
| `bootstrap.py` | Inicializacao do sistema | core/logging_config |
| `state_manager.py` | Gerencia estados da app (AppMode) | - |
| `event_handlers.py` | Handlers de eventos (on_key, on_button) | ui/, soul/ |
| `lifecycle.py` | Ciclo de vida (on_mount, on_unmount) | core/, soul/ |
| `threading_setup.py` | Setup de threads | soul/threading_manager |
| `ui_helpers.py` | Helpers de UI | ui/ |
| `actions/*.py` | Actions mixins (menu, voice, vision, clipboard) | soul/, core/ |

### 2. src/soul/ - Logica de IA e Processamento

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `consciencia.py` | Processamento central de LLM (~1500 linhas) | providers/, data_memory/, core/ |
| `boca.py` | Sistema TTS (Coqui, Chatterbox) | core/audio_utils, core/entity_loader |
| `visao.py` | Processamento de imagens/visao | core/models/ |
| `comunicacao.py` | Entrada de audio (Whisper) | - |
| `response_pipeline.py` | Pipeline de processamento de respostas | context_builder, response_parser |
| `context_builder.py` | Construcao de contexto para LLM | data_memory/ |
| `response_parser.py` | Parsing de respostas LLM | core/entity_loader |
| `streaming.py` | Streaming de audio/texto | - |
| `providers/*.py` | Providers LLM (Gemini, Ollama) | core/circuit_breaker |
| `personality_anchor.py` | Ancora de personalidade | core/entity_loader |
| `personality_guard.py` | Guard de personalidade | - |
| `emotional_state.py` | Estado emocional persistente | data_memory/ |
| `entity_hotswap.py` | Troca de entidades em runtime | core/entity_loader |
| `onboarding.py` | Fluxo de onboarding | ui/, data_memory/ |
| `wake_word.py` | Deteccao de wake word | comunicacao |
| `model_manager.py` | Gerenciamento de modelos Ollama | core/ollama_client |
| `voice_profile.py` | Perfis de voz | - |
| `voice_system.py` | Sistema de voz unificado | boca, voice_profile |
| `audio_threads.py` | Threads de audio | comunicacao, boca |
| `processing_threads.py` | Threads de processamento | consciencia |
| `threading_manager.py` | Gerenciador de threads | audio_threads, processing_threads |

### 3. src/core/ - Infraestrutura Core

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `entity_loader.py` | Carregamento de entidades do panteao | file_lock |
| `animation.py` | Controlador de animacoes ASCII | - |
| `ollama_client.py` | Cliente Ollama (sync e async) | - |
| `logging_config.py` | Configuracao centralizada de logging | - |
| `router.py` | Roteamento de intents | - |
| `session.py` | Gerenciamento de sessoes | file_lock |
| `file_lock.py` | Locks seguros para arquivos JSON | - |
| `circuit_breaker.py` | Circuit breaker para APIs | - |
| `fallback_manager.py` | Gerenciamento de fallbacks | ollama_client |
| `metricas.py` | Coleta de metricas | - |
| `profiler.py` | Profiling de performance | - |
| `hardware_tiers.py` | Deteccao automatica de hardware | - |
| `audio_utils.py` | Utilitarios de audio (descompressao) | - |
| `interfaces.py` | Protocols para desacoplamento | - |
| `models/*.py` | Wrappers de modelos (Dolphin, Qwen, MiniCPM) | ollama_client |

### 4. src/data_memory/ - Sistema de Memoria

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `smart_memory.py` | Memoria semantica principal | embeddings, vector_store, emotional_tagger |
| `short_term_memory.py` | Buffer de curto prazo (TTL 5min) | - |
| `memory_tier_manager.py` | Orquestracao de tiers | short_term_memory, smart_memory |
| `memory_interface.py` | Interface abstrata de memoria | - |
| `memory_adapter.py` | Adapter para SmartMemory | smart_memory |
| `entity_memory.py` | Memoria por entidade | smart_memory |
| `vector_store.py` | Armazenamento vetorial JSON | embeddings |
| `vector_store_optimized.py` | Vector store otimizado | embeddings |
| `embeddings.py` | Geracao de embeddings | - |
| `embeddings_cache.py` | Cache de embeddings | - |
| `emotional_tagger.py` | Tagging emocional | - |
| `memory_decay.py` | Decay de memorias | - |
| `memory_consolidator.py` | Consolidacao de memorias | - |
| `proactive_system.py` | Sistema proativo | - |
| `proactive_recall.py` | Recall proativo | smart_memory |

### 5. src/ui/ - Interface Textual

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `widgets.py` | Widgets base (ChatMessage, CodeBlock) | - |
| `screens.py` | Telas (Canone, History) | widgets |
| `banner.py` | Banner ASCII animado | colors |
| `colors.py` | Paleta de cores | - |
| `elements.py` | Mapeamento de elementos UI | - |
| `multiline_input.py` | Input multiline | - |
| `context_menu.py` | Menu de contexto | - |
| `emotion_manager.py` | Gerenciador de emocoes na UI | - |
| `audio_visualizer.py` | Visualizador de audio | - |
| `intro_animation.py` | Animacao de intro | banner |
| `glitch_button.py` | Botao com efeito glitch | - |
| `entity_selector.py` | Seletor de entidades | core/entity_loader |

### 6. src/controllers/ - Controladores

| Arquivo | Responsabilidade | Depende de |
|---------|------------------|------------|
| `ui_controller.py` | Controle de UI | ui/ |
| `audio_controller.py` | Controle de audio | soul/comunicacao, soul/boca |
| `threading_controller.py` | Controle de threads | soul/threading_manager |

## Fluxo de Dados Principal

```
1. User Input (keyboard/voice)
       |
2. TemploDaAlma.on_input_submitted()
       |
3. Consciencia.processar_comando()
       |
4. ResponsePipeline.process()
   |-- ContextBuilder.build()     -> data_memory/
   |-- UniversalLLM.generate()    -> providers/ (Gemini/Ollama)
   |-- ResponseParser.parse()
       |
5. UI Update (animation + text)
   |-- AnimationController.set_animation()
   |-- ChatMessage.update()
       |
6. TTS (optional)
   |-- Boca.falar_async()
       |
7. Memory Update
   |-- SmartMemory.add()
   |-- EmotionalState.update()
```

## Dependencias Circulares Evitadas

1. **core/ -> soul/**: Quebrado via `src/core/interfaces.py` (Protocols)
2. **soul/ -> app/**: Usa TYPE_CHECKING para imports condicionais
3. **data_memory/ -> soul/**: Unidirecional (soul importa data_memory)

## Singletons e Factories

| Funcao | Modulo | Tipo |
|--------|--------|------|
| `get_universal_llm()` | soul/providers | Singleton com lock |
| `get_context_builder()` | soul/context_builder | Factory por entity |
| `get_response_pipeline()` | soul/response_pipeline | Factory por entity |
| `get_smart_memory()` | data_memory/smart_memory | Singleton |
| `get_entity_smart_memory()` | data_memory/smart_memory | Factory por entity |
| `get_tier_manager()` | data_memory/memory_tier_manager | Factory por entity |
| `get_short_term_memory()` | data_memory/short_term_memory | Factory por entity |
| `get_metrics()` | core/metricas | Singleton |
| `get_logger()` | core/logging_config | Factory por module |
| `get_active_entity()` | core/entity_loader | Singleton |

## Arquivos Grandes (>500 linhas)

| Arquivo | Linhas | Necessita Comentarios de Secao |
|---------|--------|--------------------------------|
| `consciencia.py` | ~1548 | Sim |
| `boca.py` | ~738 | Sim |
| `smart_memory.py` | ~591 | Sim |
| `entity_loader.py` | ~357 | Nao |
| `luna_app.py` | ~332 | Nao |

## Dicas para IAs

1. **Entry Point**: Comece por `main.py` -> `src/app/luna_app.py`
2. **Logica de Chat**: `src/soul/consciencia.py` e o coracao do sistema
3. **Memoria**: `src/data_memory/smart_memory.py` gerencia toda memoria semantica
4. **Entidades**: `src/core/entity_loader.py` carrega configuracoes do panteao
5. **Providers LLM**: `src/soul/providers/universal_llm.py` abstrai Gemini/Ollama
6. **Testes**: `src/tests/` contem 1231+ testes organizados por modulo

## Ultima Atualizacao

2025-12-29 - ETAPA 13 (AI-Friendliness)
