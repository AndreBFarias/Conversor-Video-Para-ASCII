# Fix: Excecoes Silenciadas

**Data:** 2025-12-29
**Tipo:** Bugfix
**Prioridade:** P0 - Critica
**Issue:** #33

## Resumo

Substituicao de todos os `except: pass` e `except Exception: pass` por tratamento adequado com logging.

## Motivacao

Excecoes silenciadas causam:
- Bugs dificeis de rastrear
- Comportamentos inesperados sem feedback
- Perda de informacao de debug

## Mudancas

### Arquivos Modificados

#### src/soul/ (10 arquivos)
- `consciencia.py` - Tratamento de erros em leitura de profile
- `audio_threads.py` - Tratamento de erros em visualizador e cleanup
- `threading_manager.py` - Tratamento de erros em injecao de sentinelas
- `semantic_cache.py` - Tratamento de erros em contagem de cache L2
- `processing_threads.py` - Tratamento de erros em UI updates
- `voice_profile.py` - Tratamento de erros em leitura de profile
- `entity_switch.py` - Tratamento de erros em leitura de preferencias
- `live_session.py` - Tratamento de erros em cleanup de audio
- `onboarding.py` - Tratamento de erros em elementos UI

#### src/core/ (4 arquivos)
- `desktop_integration.py` - Tratamento de erros em clipboard e idle time
- `tray.py` - Tratamento de erros em atualizacao de menu
- `animation.py` - Tratamento de erros em atualizacao de ASCII pane
- `hardware_tiers.py` - Tratamento de erros em deteccao de RAM

#### src/app/ (4 arquivos)
- `state_manager.py` - Tratamento de erros em notificacao de observers
- `threading_setup.py` - Tratamento de erros em wake word UI
- `actions/menu_actions.py` - Tratamento de erros em placeholder e timer
- `event_handlers.py` - Tratamento de erros em UI de processamento
- `lifecycle.py` - Tratamento de erros em stats e placeholder

#### src/ui/ (6 arquivos)
- `screens.py` - 15 ocorrencias corrigidas
- `banner.py` - 16 ocorrencias corrigidas
- `code_output_panel.py` - 1 ocorrencia corrigida
- `context_menu.py` - 2 ocorrencias corrigidas
- `multiline_input.py` - 1 ocorrencia corrigida
- `emotion_manager.py` - 1 ocorrencia corrigida

#### Outros
- `src/data_memory/proactive_system.py` - 3 ocorrencias corrigidas
- `src/controllers/threading_controller.py` - except bare corrigido
- `src/tools/setup_desktop_entry.py` - 2 ocorrencias corrigidas
- `src/tools/diagnostico_recursos.py` - 1 ocorrencia corrigida
- `src/tools/find_working_device.py` - 2 ocorrencias corrigidas

### Arquivos Criados
- `src/tests/test_exception_handling.py` - Testes de verificacao

### Pre-commit
- Adicionado hook `no-silent-except` para prevenir novas ocorrencias

## Padrao Adotado

```python
# ANTES (errado)
except:
    pass

except Exception:
    pass

# DEPOIS (correto)
except Exception as e:
    logger.debug(f"Erro em [contexto]: {e}")
    # Fallback ou re-raise conforme necessidade
```

## Niveis de Log Utilizados

- `logger.debug()` - Erros esperados (UI queries, cleanup, leitura de config)
- `logger.warning()` - Erros que merecem atencao mas nao sao criticos
- `logger.error()` - Erros inesperados que precisam investigacao

## Testes

```bash
pytest src/tests/test_exception_handling.py -v
```

## Verificacao

```bash
# Deve retornar vazio (exceto arquivos de teste)
grep -rn "except:\s*$" src/ --include="*.py" | grep -v test
```

## Total de Correcoes

- ~70 ocorrencias corrigidas em 29 arquivos
- 1 teste de verificacao criado
- 1 hook pre-commit adicionado
