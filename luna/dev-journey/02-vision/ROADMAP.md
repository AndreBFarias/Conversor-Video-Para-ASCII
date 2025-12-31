# Roadmap do Projeto Luna

**Data:** 2025-12-18

## TL;DR

Evolução de Luna desde MVP até assistente autônoma completa. Fases: v1 (TUI básica), v2 (multimodal + threading), v3 (memória + UX), v4 (plugins + integração), v5+ (autonomia + comunidade).

## Contexto

Este roadmap mapeia a trajetória técnica de Luna desde o protótipo inicial até a visão de longo prazo. Cada fase tem objetivos claros e entregáveis mensuráveis.

## Estrutura de Versões

Seguimos versionamento semântico adaptado:
- **Major (vX.0.0):** Mudanças arquiteturais ou de paradigma
- **Minor (v1.X.0):** Novas features significativas
- **Patch (v1.0.X):** Bugfixes e melhorias incrementais

## Fases do Projeto

### v1.0 - MVP (Q3 2024) [CONCLUÍDO]

#### Objetivo
Provar o conceito de assistente TUI com personalidade.

#### Features Implementadas
1. Interface TUI basica com Textual
2. Integracao com API LLM
3. Sistema de input/output de texto
4. Personalidade gótica inicial
5. Tema dark com ASCII art simples

#### Stack Técnico
- Python 3.10
- Textual 0.x
- API LLM (Gemini/Ollama)
- Config via .env

#### Aprendizados
- TUI é viável para assistentes IA
- Personalidade importa para engagement
- Performance de API precisa ser otimizada

### v2.0 - Multimodal + Performance (Q4 2024) [CONCLUÍDO]

#### Objetivo
Adicionar voz e visão, otimizar threading.

#### Features Implementadas
1. Input/output de voz (Whisper + TTS)
2. Processamento de imagens via LLM Vision
3. Threading paralelo para operacoes assincronas
4. Rate limiting e quota management
5. Sistema de delegação de modelos

#### Módulos Criados
- `voz_module.py`: Áudio bidirecional
- `consciencia.py`: Delegação inteligente
- `api_optimizer.py`: Controle de quota

#### Melhorias de Performance
- Operações de I/O não bloqueantes
- Cache de respostas repetidas
- Lazy loading de módulos pesados

#### Desafios Superados
- Deadlocks em threading inicial
- Rate limiting da API LLM
- Sincronizacao de UI durante operacoes longas

### v3.0 - Memória + UX (Q1 2025) [EM DESENVOLVIMENTO]

#### Objetivo Atual
Sistema de memória persistente e UX polida.

#### Features em Implementação
1. Sistema de memória contextual
2. Glitch effects procedurais
3. Status bar com decriptação animada
4. Onboarding interativo para novos usuários
5. Sistema de dev_log para continuidade

#### Features Planejadas
1. Busca em histórico de conversas
2. Exportação de sessões
3. Configuração via TUI (sem editar INI)
4. Atalhos customizáveis

#### Módulos Novos
- `memoria.py`: Persistência de contexto
- `onboarding.py`: Tutorial interativo
- `glitch_effects.py`: Animações ASCII

#### Melhorias de UX
- Feedback visual para operações longas
- Mensagens de erro mais descritivas
- Navegação por histórico (setas)
- Modo de ajuda contextual

### v4.0 - Plugins + Integração (Q2-Q3 2025) [PLANEJADO]

#### Objetivo
Tornar Luna extensível via plugins e integrada ao desktop.

#### Features Planejadas

##### Sistema de Plugins
1. API pública para extensões
2. Gerenciador de plugins via TUI
3. Hot-reload de módulos
4. Sandboxing para segurança
5. Documentação de desenvolvimento

##### Integração Desktop
1. Hotkeys globais (ex: Ctrl+Alt+L)
2. Overlay sobre aplicações ativas
3. Captura de contexto de janelas
4. Automação de GUI via acessibilidade

##### Plugins Oficiais (v4.1+)
- **luna-web:** Busca contextual na web
- **luna-tasks:** Integração com todo.txt
- **luna-git:** Assistente para Git/GitHub
- **luna-docs:** Gerador de documentação

#### Arquitetura
```
src/
├── plugins/
│   ├── __init__.py
│   ├── base.py          # Classe abstrata Plugin
│   ├── loader.py        # Carregamento dinâmico
│   └── official/        # Plugins oficiais
└── integrations/
    ├── desktop.py       # X11/Wayland hooks
    └── automation.py    # GUI scripting
```

### v5.0 - Autonomia (Q4 2025) [PLANEJADO]

#### Objetivo
Luna proativa, com capacidade de sugerir e executar tarefas.

#### Features Planejadas

##### Autonomia Básica
1. Sistema de tarefas agendadas
2. Sugestões proativas baseadas em padrões
3. Execução de scripts com aprovação
4. Notificações contextuais

##### Inteligência Contextual
1. Análise de produtividade
2. Detecção de padrões de trabalho
3. Sugestões de otimização de workflow
4. Lembretes inteligentes

##### Workflow Automation
1. Editor visual de workflows
2. Triggers customizáveis
3. Biblioteca de ações pré-definidas
4. Logs de execução automática

### v6.0+ - Além da Interface (2026+) [VISÃO]

#### Objetivos de Longo Prazo

##### Multiplataforma
1. Versão mobile (Termux/Pythonista)
2. WebUI opcional (acesso remoto)
3. Sincronização entre dispositivos
4. CLI headless para scripts

##### Colaboração
1. Modo multiusuário
2. Compartilhamento de sessões
3. Workflows colaborativos
4. Base de conhecimento compartilhada

##### Inteligência Avançada
1. Memória vetorial com embeddings
2. Fine-tuning de modelo personalizado
3. Aprendizado incremental
4. Análise emocional de conversas

## Cronograma Visual

```
2024 Q3 ████████ v1.0 MVP
2024 Q4 ████████ v2.0 Multimodal
2025 Q1 ████████ v3.0 Memória + UX [ATUAL]
2025 Q2 ░░░░░░░░ v4.0 Plugins (início)
2025 Q3 ░░░░░░░░ v4.1 Integração Desktop
2025 Q4 ░░░░░░░░ v5.0 Autonomia
2026 Q1 ░░░░░░░░ v5.1 Workflow Engine
2026 Q2 ░░░░░░░░ v6.0 Multiplataforma
2026+   ░░░░░░░░ Evolução contínua
```

## Critérios de Sucesso por Fase

### v3.0 (Atual)
- [ ] Memória persiste entre sessões
- [ ] Onboarding completo para novos usuários
- [ ] Zero crashes em uso normal
- [ ] Documentação técnica completa

### v4.0
- [ ] 5+ plugins oficiais funcionais
- [ ] API de plugins documentada
- [ ] Hotkey global funciona em X11/Wayland
- [ ] Pelo menos 1 plugin comunitário

### v5.0
- [ ] Sugestões proativas relevantes em 80% dos casos
- [ ] Workflows salvos e reutilizáveis
- [ ] Execução automatizada sem intervenção
- [ ] Análise de produtividade com insights reais

## Princípios de Desenvolvimento

### Para Cada Release
1. Testes automatizados (mínimo 70% coverage)
2. Documentação atualizada antes do merge
3. Changelog detalhado
4. Dev_log da sessão de desenvolvimento

### Qualidade sobre Velocidade
1. Refatoração contínua
2. Code review interno
3. Performance benchmarks
4. Feedback de usuários reais

### Transparência
1. Roadmap público
2. Issues abertas no GitHub
3. Comunicação de atrasos
4. Reconhecimento de limitações

## Links Relacionados

- [O Que Estamos Construindo](./WHAT_WE_ARE_BUILDING.md)
- [Visão de Longo Prazo](./WHERE_WE_WANT_TO_GO.md)
- [Changelog Detalhado](../03-changelog/CHANGELOG.md)
- [Guia de Contribuição](../../docs/CONTRIBUTING.md)
