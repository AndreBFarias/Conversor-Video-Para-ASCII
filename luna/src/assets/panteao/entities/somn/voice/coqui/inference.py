# -*- coding: utf-8 -*-
"""
Script de inferencia para modelo XTTS fine-tuned
Gerado por Neurosonancy em 2025-12-28 05:51:51
"""

import torch
from pathlib import Path
from TTS.api import TTS

MODEL_DIR = Path(__file__).parent
OUTPUT_DIR = MODEL_DIR / "outputs"
REFERENCE_WAV = MODEL_DIR / "reference_speaker.wav"


def generate_speech(
    text: str,
    speaker_wav: str = None,
    output_file: str = "output.wav",
    language: str = "pt"
) -> Path:
    """
    Gera audio usando o modelo XTTS fine-tuned.

    Args:
        text: Texto para sintetizar
        speaker_wav: Caminho para audio de referencia (opcional, usa default se nao fornecido)
        output_file: Nome do arquivo de saida
        language: Idioma (default: pt)

    Returns:
        Path do arquivo de audio gerado
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / output_file

    # Usar referencia default se nao fornecida
    if speaker_wav is None:
        speaker_wav = str(REFERENCE_WAV)

    # Carregar modelo
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    # Gerar audio
    tts.tts_to_file(
        text=text,
        file_path=str(output_path),
        speaker_wav=speaker_wav,
        language=language,
    )

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python inference.py <texto> [speaker_wav]")
        print("Exemplo: python inference.py 'Ola, como vai voce?'")
        sys.exit(1)

    text = sys.argv[1]
    speaker_wav = sys.argv[2] if len(sys.argv) > 2 else None

    result = generate_speech(text, speaker_wav)
    print(f"Audio gerado: {result}")
