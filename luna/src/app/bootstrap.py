from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

import config
from src.core.logging_config import get_logger, setup_logging

if TYPE_CHECKING:
    from src.core.di import ServiceContainer


def _suppress_library_warnings() -> None:
    warnings.filterwarnings("ignore")


def _verify_gemini_api(logger: logging.Logger) -> str | None:
    gemini_error = None

    if config.CHAT_PROVIDER == "gemini":
        try:
            from google import genai

            if config.GOOGLE_API_KEY:
                _test_client = genai.Client(api_key=config.GOOGLE_API_KEY)
                logger.info("API do Gemini configurada com sucesso (novo SDK).")
                del _test_client
            else:
                gemini_error = "GOOGLE_API_KEY nao configurada no .env"
                logger.warning(gemini_error)
        except ValueError as e:
            gemini_error = f"Erro ao configurar a API key do Gemini: {e}. Verifique o config.py."
            logger.critical(gemini_error)
        except Exception as e:
            gemini_error = f"Erro inesperado ao configurar a API do Gemini: {e}"
            logger.critical(f"Falha critica ao configurar a API do Gemini: {e}", exc_info=True)
    else:
        logger.info(f"Usando provider local: {config.CHAT_PROVIDER}")

    return gemini_error


def _apply_hardware_tier(logger: logging.Logger) -> None:
    try:
        from src.core.hardware_tiers import apply_hardware_config, get_hardware_config

        hw_config = get_hardware_config()
        apply_hardware_config(hw_config)
        logger.info(f"Hardware tier aplicado: {hw_config.tier.value}")
    except Exception as e:
        logger.warning(f"Erro ao detectar hardware tier: {e}")


def _initialize_container(logger: logging.Logger) -> ServiceContainer:
    from src.core.di import ServiceContainer, register_default_services

    container = ServiceContainer.get_instance()

    if not container.is_registered("config"):
        register_default_services(container)
        logger.info("Container de DI inicializado com servicos padrao")

    return container


def initialize_application() -> tuple[logging.Logger, str | None]:
    _suppress_library_warnings()
    setup_logging(level="INFO", log_to_file=True, log_to_console=False)
    logger = get_logger(__name__)
    _apply_hardware_tier(logger)
    _initialize_container(logger)
    gemini_error = _verify_gemini_api(logger)
    return logger, gemini_error


def get_service_container() -> ServiceContainer:
    from src.core.di import ServiceContainer

    return ServiceContainer.get_instance()
