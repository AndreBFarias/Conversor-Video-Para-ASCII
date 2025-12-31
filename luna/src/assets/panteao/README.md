# Panteão - Sistema Multi-Entidades

Estrutura centralizada para gerenciamento de personalidades IA no projeto Luna.

## Estrutura

```
panteao/
├── registry.json                # Registro central de todas entidades
├── shared/
│   └── fallback_animation.txt.gz  # Animação padrão quando específica não existe
└── entities/
    ├── luna/
    │   ├── config.json          # Configurações específicas
    │   ├── alma.txt             # SOUL PROMPT (personalidade)
    │   └── animations/          # Animações específicas
    ├── juno/
    ├── eris/
    ├── mars/
    ├── lars/
    └── somn/
```

## Status das Entidades

| ID   | Nome | Gênero   | Status      | Voz Configurada |
|------|------|----------|-------------|-----------------|
| luna | Luna | Feminino | DISPONÍVEL  | Sim             |
| juno | Juno | Feminino | Bloqueado   | Sim             |
| eris | Eris | Feminino | Bloqueado   | Não             |
| mars | Mars | Masculino| Bloqueado   | Não             |
| lars | Lars | Masculino| Bloqueado   | Não             |
| somn | Somn | Masculino| Bloqueado   | Não             |

## Arquivos Obrigatórios por Entidade

1. **config.json** - Configurações JSON completas (persona, voz, estética)
2. **alma.txt** - SOUL PROMPT (instruções de personalidade para LLM)
3. **animations/** - Diretório para animações específicas da entidade

## Registry.json

O arquivo `registry.json` contém:
- Metadados de todas as entidades
- Status de disponibilidade (`available: true/false`)
- Caminhos para arquivos de configuração
- Informações de voz configurada
- Entidade padrão do sistema

## Proximos Passos para Ativar uma Entidade

1. Configurar arquivos de referencia de voz em `voice/coqui/` ou `voice/chatterbox/`
2. Criar animacoes no formato esperado pelo AnimationController
3. Atualizar registry.json:
   - `available: true`
   - `voice_configured: true`
4. Testar carregamento da entidade no sistema principal

### Configuracao de Voz Local

Cada entidade pode usar TTS local (Coqui ou Chatterbox) com arquivos de referencia:
- `voice/coqui/reference.wav` - Audio de referencia para clonagem Coqui
- `voice/chatterbox/reference.wav` - Audio de referencia para Chatterbox

O sistema baixa automaticamente os modelos necessarios na primeira execucao.

## Formato de Animação

Todas as animações devem seguir o formato:
```
[FRAME]
arte ascii aqui

[FRAME]
próximo frame aqui
```

## Notas Técnicas

- Todas as entidades seguem o protocolo de resposta JSON estruturado
- Campos obrigatórios: `fala_tts`, `log_terminal`, `animacao`, `comando_visao`
- SOUL PROMPTs usam placeholders: `{user_name}`, `{pronome}`, `{tratamento_carinhoso}`
- Animações são carregadas pelo `AnimationController` do core

---

## Status de Implementacao (2025-12-25)

### Etapas Concluidas

- [x] Etapa 1: Estrutura de pastas do Panteao
- [x] Etapa 2: EntityLoader (`src/core/entity_loader.py`)
- [x] Etapa 3: AnimationController adaptado
- [x] Etapa 4: Personalidade adaptada
- [x] Etapa 5: EntitySelectorScreen (`src/ui/entity_selector.py`)
- [x] Etapa 6: Integracao no Onboarding
- [x] Etapa 7: Opcao no Canone (CanoneScreen)
- [x] Etapa 8: ThemeManager CSS dinamico (`src/ui/theme_manager.py`)
- [x] Etapa 9: Documentacao (`PANTHEON_SYSTEM.md`)
- [x] Etapa 10: Testes (`test_pantheon.py`)

### Documentacao Completa

Ver: `dev-journey/04-implementation/PANTHEON_SYSTEM.md`
