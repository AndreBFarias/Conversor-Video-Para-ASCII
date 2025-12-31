import logging
import os
import sys
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

SCRIPT_DIR = Path(__file__).parent.parent.parent
TTS_CACHE_DIR = SCRIPT_DIR / "src" / "models" / "tts"
os.environ["HF_HOME"] = str(TTS_CACHE_DIR)
os.environ["TORCH_HOME"] = str(TTS_CACHE_DIR)

logging.basicConfig(level=logging.WARNING)
logging.getLogger("chatterbox").setLevel(logging.WARNING)

import torch

original_load = torch.load


def patched_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return original_load(*args, **kwargs)


torch.load = patched_load


def main():
    if len(sys.argv) < 4:
        print(
            "ERROR: Uso: python chatterbox_wrapper.py <texto> <output_path> <reference_audio> [exaggeration]",
            file=sys.stderr,
        )
        sys.exit(1)

    texto = sys.argv[1]
    output_path = sys.argv[2]
    reference_audio = sys.argv[3]
    exaggeration = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5

    if not texto.strip():
        print("ERROR: Texto vazio", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(reference_audio):
        print(f"ERROR: Reference audio nao encontrado: {reference_audio}", file=sys.stderr)
        sys.exit(1)

    try:
        import torch
        import torchaudio
        from chatterbox.tts import ChatterboxTTS

        device = "cuda" if torch.cuda.is_available() else "cpu"

        model = ChatterboxTTS.from_pretrained(device=device)

        wav = model.generate(text=texto, audio_prompt_path=reference_audio, exaggeration=exaggeration)

        torchaudio.save(output_path, wav, model.sr)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"SUCCESS: {output_path}")
            sys.exit(0)
        else:
            print("ERROR: Arquivo de saida vazio ou nao criado", file=sys.stderr)
            sys.exit(1)

    except ImportError as e:
        print(f"ERROR: chatterbox-tts nao instalado: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
