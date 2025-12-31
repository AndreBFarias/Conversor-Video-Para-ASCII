import logging
import re
from enum import Enum

import config

logger = logging.getLogger(__name__)


class Intent(Enum):
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    SYSTEM = "system"


CODE_PATTERNS = [
    r"\b(codigo|code|script|funcao|function|classe|class)\b",
    r"\b(python|sql|javascript|typescript|r|bash|shell)\b",
    r"\b(cria|crie|faz|faca|implementa|implementar|escreva|escreve)\b.*\b(um|uma|o|a)\b.*\b(script|funcao|codigo|classe)\b",
    r"\b(debug|erro|error|bug|fix|corrige|corrigir|conserta)\b",
    r"\b(dataframe|pandas|numpy|query|select|insert|update|delete)\b",
    r"\b(pipeline|etl|airflow|dbt|bigquery|gcp|aws|azure)\b",
    r"\b(power\s*bi|pbi|dashboard|relatorio|report)\b",
    r"\b(api|endpoint|request|response|rest|graphql)\b",
    r"\b(git|commit|branch|merge|pull|push)\b",
    r"\b(docker|container|kubernetes|k8s)\b",
    r"\b(teste|test|unittest|pytest|mock)\b",
    r"\b(refatora|refactor|otimiza|optimize)\b",
    r"```\w*\n",
]

VISION_PATTERNS = [
    r"\b(olha|olhe|ve|veja)\b.*\b(para\s+mim|pra\s+mim|mim|isso|imagem|foto|tela|camera)\b",
    r"\b(olha|olhe|ve|veja)\s+(para\s+mim|pra\s+mim|aqui)\b",
    r"\b(o\s+que\s+(voce\s+)?ve|que\s+ve|esta\s+vendo|ta\s+vendo)\b",
    r"\b(descreve|descreva|identifica|identifique)\b.*\b(imagem|foto|tela)\b",
    r"\b(mostra|mostre)\b.*\b(camera|webcam|tela)\b",
    r"\b(captura|capture|tire|tira)\b.*\b(foto|imagem|print)\b",
    r"\b(reconhece|reconheca|detecta|detecte)\b.*\b(rosto|face|objeto|pessoa)\b",
    r"\b(me\s+ve|me\s+olha|me\s+veja)\b",
    r"\b(o\s+que\s+acha\s+d(esse|essa|isso|aquilo))\b",
]

SYSTEM_PATTERNS = [
    r"^/(nova|historico|alma|sair|config|ajuda|help|quit|exit)",
    r"^/(clear|limpa|reset)",
]


def detect_intent(user_input: str, has_image: bool = False, has_code_context: bool = False) -> Intent:
    input_lower = user_input.lower().strip()

    for pattern in SYSTEM_PATTERNS:
        if re.search(pattern, input_lower):
            return Intent.SYSTEM

    if has_image:
        return Intent.VISION

    for pattern in VISION_PATTERNS:
        if re.search(pattern, input_lower):
            return Intent.VISION

    if has_code_context:
        return Intent.CODE

    for pattern in CODE_PATTERNS:
        if re.search(pattern, input_lower):
            logger.debug(f"Intent CODE detectado pelo pattern: {pattern}")
            return Intent.CODE

    return Intent.CHAT


def get_provider_config(intent: Intent) -> tuple[str, dict]:
    if intent == Intent.CODE:
        if config.CODE_PROVIDER == "local":
            return ("ollama", config.CODE_LOCAL)
        else:
            return (config.CODE_API["provider"], config.CODE_API)

    elif intent == Intent.VISION:
        if config.VISION_PROVIDER == "local":
            return ("ollama", config.VISION_LOCAL)
        else:
            return ("gemini", config.VISION_GEMINI)

    else:
        if config.CHAT_PROVIDER == "local":
            return ("ollama", config.CHAT_LOCAL)
        else:
            return ("gemini", config.CHAT_GEMINI)


def get_model_for_intent(intent: Intent) -> str:
    if intent == Intent.CODE:
        if config.CODE_PROVIDER == "local":
            return config.CODE_LOCAL["model"]
        return config.CODE_API.get("model", "deepseek-coder")

    elif intent == Intent.VISION:
        if config.VISION_PROVIDER == "local":
            return config.VISION_LOCAL["model"]
        return config.VISION_GEMINI.get("model", "gemini-1.5-flash")

    else:
        if config.CHAT_PROVIDER == "local":
            return config.CHAT_LOCAL["model"]
        return config.CHAT_GEMINI.get("model", "gemini-1.5-flash")


def should_use_local(intent: Intent) -> bool:
    if intent == Intent.CODE:
        return config.CODE_PROVIDER == "local"
    elif intent == Intent.VISION:
        return config.VISION_PROVIDER == "local"
    else:
        return config.CHAT_PROVIDER == "local"


def get_intent_display_name(intent: Intent) -> str:
    names = {
        Intent.CHAT: "Conversa",
        Intent.CODE: "Codigo",
        Intent.VISION: "Visao",
        Intent.SYSTEM: "Sistema",
    }
    return names.get(intent, "Desconhecido")
