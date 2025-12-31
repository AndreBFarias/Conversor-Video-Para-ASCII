# -*- coding: utf-8 -*-
"""
Script de inferencia para Chatterbox com voz clonada
Gerado por Neurosonancy em 2025-12-28 05:56:58
"""

import torch
import torchaudio
from pathlib import Path
from chatterbox.tts import ChatterboxTTS

MODEL_DIR = Path(__file__).parent
OUTPUT_DIR = MODEL_DIR / "outputs"
REFERENCE_AUDIO = MODEL_DIR / "reference.wav"


def load_model(device: str = None):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return ChatterboxTTS.from_pretrained(device=device)


def generate_speech(
    text: str,
    output_file: str = "output.wav",
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5,
) -> Path:
    """
    Gera audio usando Chatterbox com voz clonada.

    Args:
        text: Texto para sintetizar
        output_file: Nome do arquivo de saida
        exaggeration: Nivel de expressividade (0.0-1.0)
        cfg_weight: Peso do classifier-free guidance (0.0-1.0)

    Returns:
        Path do arquivo de audio gerado
    """
    if not REFERENCE_AUDIO.exists():
        raise ValueError(f"Audio de referencia nao encontrado: {REFERENCE_AUDIO}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / output_file

    model = load_model()

    audio = model.generate(
        text=text,
        audio_prompt_path=str(REFERENCE_AUDIO),
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
    )

    torchaudio.save(str(output_path), audio.squeeze(0).cpu(), 24000)

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python inference.py <texto>")
        print("")
        print("Exemplo:")
        print("  python inference.py 'Ola, como voce esta?'")
        sys.exit(1)

    text = sys.argv[1]
    result = generate_speech(text)
    print(f"Audio gerado: {result}")
