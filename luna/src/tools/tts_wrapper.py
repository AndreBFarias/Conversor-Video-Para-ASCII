import logging
import os
import sys
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["COQUI_TOS_AGREED"] = "1"
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

SCRIPT_DIR = Path(__file__).parent.parent.parent
TTS_CACHE_DIR = SCRIPT_DIR / "src" / "models" / "tts"
os.environ["TTS_HOME"] = str(TTS_CACHE_DIR)

logging.basicConfig(level=logging.WARNING)
logging.getLogger("TTS").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

import torch

torch.serialization.add_safe_globals([])
original_load = torch.load


def patched_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return original_load(*args, **kwargs)


torch.load = patched_load


def main():
    if len(sys.argv) < 4:
        print("ERROR: Uso: python tts_wrapper.py <texto> <output_path> <reference_audio> [speed]", file=sys.stderr)
        sys.exit(1)

    texto = sys.argv[1]
    output_path = sys.argv[2]
    reference_audio = sys.argv[3]
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    if not texto.strip():
        print("ERROR: Texto vazio", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(reference_audio):
        print(f"ERROR: Reference audio nao encontrado: {reference_audio}", file=sys.stderr)
        sys.exit(1)

    try:
        import torch
        from TTS.api import TTS

        device = "cuda" if torch.cuda.is_available() else "cpu"

        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
        tts.to(device)

        tts.tts_to_file(text=texto, file_path=output_path, speaker_wav=reference_audio, language="pt", speed=speed)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"SUCCESS: {output_path}")
            sys.exit(0)
        else:
            print("ERROR: Arquivo de saida vazio ou nao criado", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
