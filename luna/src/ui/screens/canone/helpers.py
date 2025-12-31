from __future__ import annotations

import logging
from pathlib import Path

from dotenv import dotenv_values
from textual.widgets import Select

import config

logger = logging.getLogger(__name__)


class EnvHelper:
    def __init__(self):
        self.env_path = config.APP_DIR / ".env"
        self.echoes_path = config.APP_DIR / "src" / "models" / "echoes" / "chatterbox"
        self._env_values = {}
        self._valid_voice_values = {""}
        self._load_env_values()

    def _load_env_values(self):
        try:
            if self.env_path.exists():
                self._env_values = dict(dotenv_values(self.env_path))
        except Exception as e:
            logger.error(f"Erro ao carregar .env: {e}")

    def get(self, key: str, default: str = "") -> str:
        return self._env_values.get(key, default)

    def get_voice_options(self) -> list:
        options = [("Voz Padrao (Coqui)", "")]
        self._valid_voice_values = {""}
        try:
            if self.echoes_path.exists():
                wav_files = sorted(self.echoes_path.glob("*.wav"))
                for wav in wav_files:
                    options.append((wav.stem, str(wav)))
                    self._valid_voice_values.add(str(wav))
        except Exception as e:
            logger.error(f"Erro ao listar vozes: {e}")
        return options

    def get_current_voice(self):
        current = self.get("COQUI_REFERENCE_AUDIO", "")
        if current in self._valid_voice_values:
            return current
        return Select.BLANK


class OllamaModelHelper:
    @staticmethod
    def get_chat_models(env_helper: EnvHelper) -> tuple[list[tuple[str, str]], str]:
        current_model = env_helper.get("CHAT_LOCAL_MODEL", "dolphin-mistral")

        base_models = [
            ("dolphin-mistral", "7B", "4.1GB"),
            ("llama3.2:3b", "3B", "2.0GB"),
            ("llama3.2:1b", "1B", "1.3GB"),
            ("qwen2.5:3b", "3B", "1.9GB"),
            ("gemma2:2b", "2.6B", "1.6GB"),
            ("phi3:mini", "3.8B", "2.2GB"),
            ("tinyllama", "1.1B", "0.6GB"),
        ]

        options = []
        for name, params, size in base_models:
            label = f"{name} ({params} - {size})"
            options.append((label, name))

        existing_values = {opt[1] for opt in options}
        if current_model and current_model not in existing_values:
            options.insert(0, (f"{current_model} (Atual)", current_model))
            selected = current_model
        else:
            selected = current_model if current_model in existing_values else options[0][1]

        return options, selected

    @staticmethod
    def get_vision_models(env_helper: EnvHelper) -> tuple[list[tuple[str, str]], str]:
        current_model = env_helper.get("VISION_LOCAL_MODEL", "moondream")

        base_models = [
            ("moondream", "1.8B", "1.7GB"),
            ("llava-phi3", "3B", "2.9GB"),
            ("llava:7b", "7B", "4.7GB"),
        ]

        options = []
        for name, params, size in base_models:
            label = f"{name} ({params} - {size})"
            options.append((label, name))

        existing_values = {opt[1] for opt in options}
        if current_model and current_model not in existing_values:
            options.insert(0, (f"{current_model} (Atual)", current_model))
            selected = current_model
        else:
            selected = current_model if current_model in existing_values else options[0][1]

        return options, selected

    @staticmethod
    def get_code_models(env_helper: EnvHelper) -> tuple[list[tuple[str, str]], str]:
        current_model = env_helper.get("CODE_LOCAL_MODEL", "qwen2.5-coder:7b")

        base_models = [
            ("qwen2.5-coder:7b", "7B", "4.7GB"),
            ("qwen2.5-coder:3b", "3B", "1.9GB"),
            ("qwen2.5-coder:1.5b", "1.5B", "1.0GB"),
            ("deepseek-coder:1.3b", "1.3B", "0.8GB"),
            ("deepseek-coder:6.7b", "6.7B", "3.8GB"),
            ("codellama:7b", "7B", "3.8GB"),
            ("starcoder2:3b", "3B", "1.7GB"),
        ]

        options = []
        for name, params, size in base_models:
            label = f"{name} ({params} - {size})"
            options.append((label, name))

        existing_values = {opt[1] for opt in options}
        if current_model and current_model not in existing_values:
            options.insert(0, (f"{current_model} (Atual)", current_model))
            selected = current_model
        else:
            selected = current_model if current_model in existing_values else options[0][1]

        return options, selected
