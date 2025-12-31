# Voice Trainer Integration Guide

## Arquivos Criados

- `src/ui/trainer_screen.py` - Tela de treinamento de voz completa
- Estilos adicionados em `src/assets/css/templo_de_luna.css`

## Como Integrar no main.py

### 1. Adicionar Import

```python
# No topo do main.py, adicione:
from src.ui.trainer_screen import VoiceTrainerScreen
```

### 2. Adicionar Binding (Opcional)

```python
# Em LunaApp.BINDINGS, adicione:
BINDINGS = [
    # ... bindings existentes ...
    ("ctrl+t", "open_trainer", "Treinar Voz"),
]
```

### 3. Adicionar Botão no Menu (Opcional)

```python
# Em LunaApp.compose(), dentro do #top-bar, adicione:
with Horizontal(id="top-bar"):
    yield Button("Nova Conversa", id="new_conversation", variant="default")
    yield Button("Ver Historico", id="view_history", variant="default")
    yield Button("Editar Alma", id="edit_soul", variant="default")
    yield Button("Treinar Voz", id="open_trainer", variant="default")  # NOVO
    yield Button("Ver", id="olhar", variant="primary")
    yield Button("Sair", id="quit", variant="error")
```

### 4. Adicionar Action Handler

```python
# Em LunaApp, adicione o método:
async def action_open_trainer(self) -> None:
    """Abre a tela de treinamento de voz."""
    await self.push_screen(VoiceTrainerScreen())

# Também adicione o handler de botão em on_button_pressed (se existir):
async def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id

    if button_id == "open_trainer":
        await self.action_open_trainer()
    # ... outros handlers ...
```

### 5. Handler do Evento de Treinamento (Opcional)

```python
# Para receber o evento quando o usuário iniciar o treinamento:
from src.ui.trainer_screen import VoiceTrainerScreen

# Em LunaApp:
def on_voice_trainer_screen_training_started(self, event: VoiceTrainerScreen.TrainingStarted) -> None:
    """Recebe o evento de início de treinamento."""
    logger.info(f"Treinamento iniciado: {event.model_name}")
    logger.info(f"Amostras: {len(event.samples)}")
    logger.info(f"Épocas: {event.epochs}")
    logger.info(f"LR: {event.learning_rate}")

    # Aqui você pode iniciar o processo real de fine-tuning
    # self.start_voice_training(event.model_name, event.samples, event.epochs, event.learning_rate)
```

## Exemplo Completo de Uso

```python
# main.py (trecho)

from src.ui.trainer_screen import VoiceTrainerScreen

class LunaApp(App):
    BINDINGS = [
        ("ctrl+n", "new_conversation", "Nova Conversa"),
        ("ctrl+h", "view_history", "Ver Historico"),
        ("ctrl+e", "edit_soul", "Editar Alma"),
        ("ctrl+t", "open_trainer", "Treinar Voz"),  # NOVO
        ("ctrl+v", "olhar", "Ver"),
        ("ctrl+q", "quit", "Sair"),
        ("ctrl+a", "attach_file", "Anexar Arquivo"),
        ("ctrl+space", "toggle_voice_call", "Voz"),
    ]

    # ... resto do código ...

    async def action_open_trainer(self) -> None:
        await self.push_screen(VoiceTrainerScreen())
```

## Frases de Treinamento Incluídas

O arquivo inclui 10 frases foneticamente ricas em PT-BR:

1. "O vento uiva através das árvores antigas do templo sagrado."
2. "Nas profundezas da floresta, ecoam cantos de pássaros exóticos."
3. "A lua cheia ilumina o caminho entre as montanhas nebulosas."
4. "Borboletas azuis dançam sobre o jardim de flores silvestres."
5. "O rio cristalino serpenteia pela planície verdejante."
6. "Nuvens escuras anunciam a chegada da tempestade de verão."
7. "A brisa marinha traz o perfume salgado das ondas distantes."
8. "Estrelas cintilantes pintam o céu da madrugada serena."
9. "O sino do monastério ressoa pelo vale enevoado ao entardecer."
10. "Chamas douradas dançam na lareira durante a noite fria."

## Métodos Stub para Implementar

A classe `VoiceTrainerScreen` inclui 4 métodos stub que precisam de implementação real:

### `start_recording(output_path: str)`
```python
def start_recording(self, output_path: str) -> None:
    """Implementar gravação real com sounddevice."""
    import sounddevice as sd
    import numpy as np

    self.sample_rate = 22050
    self.recording_data = []

    def callback(indata, frames, time, status):
        self.recording_data.append(indata.copy())

    self.stream = sd.InputStream(
        samplerate=self.sample_rate,
        channels=1,
        callback=callback
    )
    self.stream.start()
```

### `stop_recording()`
```python
def stop_recording(self) -> None:
    """Para gravação e salva arquivo."""
    import numpy as np
    from scipy.io import wavfile

    if hasattr(self, 'stream'):
        self.stream.stop()
        self.stream.close()

    if self.recording_data:
        audio = np.concatenate(self.recording_data)
        wavfile.write(self.last_recording_path, self.sample_rate, audio)
```

### `play_audio(audio_path: str)`
```python
def play_audio(self, audio_path: str) -> None:
    """Reproduz áudio gravado."""
    import sounddevice as sd
    from scipy.io import wavfile

    sample_rate, data = wavfile.read(audio_path)
    sd.play(data, sample_rate)
```

### `begin_training(...)`
```python
def begin_training(self, model_name, samples, epochs, learning_rate, output_dir) -> None:
    """Inicia fine-tuning do modelo TTS."""
    # Depende da sua implementação de fine-tuning
    # Pode chamar TTS.train() ou script externo
    pass
```

## CSS Adicionado

O CSS inclui estilos para:
- Layout de dois painéis (gravador + configurações)
- Botões coloridos (verde=gravar, vermelho=parar, azul=ouvir, laranja=descartar)
- Indicador de gravação animado
- Barra de progresso
- Inputs estilizados no tema dark/cyberpunk
- Botão de treinamento com gradiente roxo/rosa
