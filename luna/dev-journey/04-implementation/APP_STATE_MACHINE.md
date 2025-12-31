# APP_STATE Machine

## Estados

| Estado | Descricao |
|--------|-----------|
| `IDLE` | Pronto para interacao. Usuario pode enviar mensagens, clicar botoes. |
| `BUSY` | Processando. Acoes bloqueadas exceto botoes permitidos. |

## Transicoes

```
     [IDLE]
        |
        | (usuario envia mensagem / clica acao)
        v
     [BUSY]
        |
        | (processamento completo)
        v
     [IDLE]
```

## Acoes Bloqueadas em BUSY

Quando `app_state == "BUSY"`:
- `toggle_voice_call`: bloqueado
- `olhar` (camera): bloqueado
- `ver_historico`: bloqueado
- `editar_alma`: bloqueado
- `canone`: bloqueado
- `nova_conversa`: bloqueado
- Envio de mensagem: bloqueado

## Acoes Permitidas em BUSY

- `quit`: sempre permitido
- `attach_file`: permitido (preparar arquivo para proximo envio)

## Trigger de Transicao

### IDLE -> BUSY
- `on_button_pressed` com acoes de processamento
- `action_enviar_mensagem`
- `_processar_comando_voz`
- `action_olhar`

### BUSY -> IDLE
- Ao final de `_processar_resposta_llm`
- Ao final de `_executar_visao`
- Em caso de erro durante processamento

## Codigo Relevante

```python
# main.py
app_state = reactive("IDLE")

def on_button_pressed(self, event):
    if self.app_state != "IDLE" and event.button.id not in allowed_when_busy:
        return  # bloqueia acao

    self.app_state = "BUSY"
    # ... processa ...
    self.app_state = "IDLE"
```

## Diagrama

```
+-------+     acao     +-------+
| IDLE  | -----------> | BUSY  |
+-------+              +-------+
    ^                      |
    |    fim/erro          |
    +----------------------+
```
