"""
Helpers para deteccao de modelo, sanitizacao e perfil de usuario.

Este modulo contem funcoes auxiliares extraidas de consciencia.py
para manter o arquivo principal mais enxuto e coeso.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import config
from src.core.gender_detector import get_user_context
from src.core.logging_config import get_logger

logger = get_logger(__name__)

PROFILE_PATH = config.APP_DIR / "src" / "data_memory" / "user" / "profile.json"

SENSITIVE_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"), "[CNPJ]"),
    (re.compile(r"\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}\b"), "[TELEFONE]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARTAO]"),
    (re.compile(r"\b(?:senha|password|api[_-]?key|token|secret)[:\s=]+\S+", re.IGNORECASE), "[CREDENCIAL]"),
]

SMALL_MODEL_THRESHOLD_GB = 7.0
COMPACT_MODEL_THRESHOLD_GB = 4.0


def get_model_size_gb(model_name: str) -> float:
    if not model_name:
        return 7.0
    model_lower = model_name.lower()

    for pattern in [r":(\d+(\.\d+)?b)$", r"(\d+(\.\d+)?b)-", r"-(\d+(\.\d+)?b)$"]:
        match = re.search(pattern, model_lower)
        if match and match.groups() and match.groups()[0]:
            try:
                size_str = match.groups()[0].replace("b", "")
                return float(size_str)
            except ValueError:
                pass

    if any(kw in model_lower for kw in ["tiny", "nano"]):
        return 1.0
    if any(kw in model_lower for kw in ["mini", "small", "phi-1", "phi-2"]):
        return 2.0
    if "phi-3" in model_lower or "phi3" in model_lower:
        return 3.8

    return 7.0


def is_small_model(model_name: str) -> bool:
    return get_model_size_gb(model_name) < SMALL_MODEL_THRESHOLD_GB


def needs_compact_prompt(model_name: str) -> bool:
    return get_model_size_gb(model_name) < COMPACT_MODEL_THRESHOLD_GB


def sanitize_for_log(text: str, max_len: int = 50) -> str:
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    if len(sanitized) > max_len:
        return f"{sanitized[:max_len]}..."
    return sanitized


def get_user_profile() -> dict:
    default_context = get_user_context("Viajante", "N")
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, encoding="utf-8") as f:
                profile = json.load(f)
                nome = profile.get("nome", "Viajante")
                genero = profile.get("genero", "N")
                if "tratamentos" in profile:
                    return profile["tratamentos"]
                return get_user_context(nome, genero)
        except Exception as e:
            logger.debug(f"Erro ao ler profile: {e}")
    return default_context


def get_user_name() -> str:
    profile = get_user_profile()
    return profile.get("user_name", "Viajante")


def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\U00002600-\U000026ff"
        "\U00002700-\U000027bf"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()
