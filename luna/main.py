#!/usr/bin/env python3

import atexit
import ctypes
import os
import sys

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["USE_GPU"] = "false"
os.environ["COQUI_DEVICE"] = "cpu"
os.environ["CHATTERBOX_DEVICE"] = "cpu"

_devnull = open(os.devnull, "w")
_original_stderr = sys.stderr
atexit.register(_devnull.close)

try:
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
    )

    def py_error_handler(filename, line, function, err, fmt):
        pass

    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass

import argparse

from src.app.bootstrap import initialize_application


def main():
    parser = argparse.ArgumentParser(description="Luna - Assistente IA")
    parser.add_argument("--skip-onboarding", action="store_true", help="Pula o onboarding inicial")
    args = parser.parse_args()

    logger, gemini_error = initialize_application()
    logger.info("Dispositivo: cpu")

    try:
        logger.info("=" * 60)
        logger.info("         Iniciando Templo da Alma          ")
        logger.info("=" * 60)

        from src.app import TemploDaAlma
        from src.app.actions.menu_actions import set_gemini_error
        from src.app.bootstrap import get_service_container

        if gemini_error:
            set_gemini_error(gemini_error)

        container = get_service_container()
        app = TemploDaAlma(container=container)

        if args.skip_onboarding:
            app.skip_onboarding = True
            logger.info("Onboarding desativado via argumento")

        app.run()

    except KeyboardInterrupt:
        logger.info("Aplicacao interrompida pelo usuario (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Erro fatal na aplicacao: {e}", exc_info=True)
    finally:
        logger.info("=" * 60)
        logger.info("         Templo da Alma Finalizado          ")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
