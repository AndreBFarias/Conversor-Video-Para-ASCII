import json
import logging
import re

import config

from .constants import ACTION_PATTERNS, EMOTION_KEYWORDS
from .helpers import get_entity_prefix
from .models import LunaResponseData

logger = logging.getLogger(__name__)


class UniversalResponseParser:
    def __init__(self):
        self.fallback_count = 0
        self.success_count = 0

    def parse(self, raw_text: str) -> tuple[dict, str]:
        if not raw_text or not raw_text.strip():
            return self._create_fallback("Resposta vazia").to_dict(), "empty"

        raw_text = raw_text.strip()

        result, method = self._try_json_parse(raw_text)
        if result:
            self.success_count += 1
            return result, method

        result, method = self._try_semicolon_parse(raw_text)
        if result:
            self.fallback_count += 1
            logger.info(f"Fallback semicolon usado (total: {self.fallback_count})")
            return result, method

        result, method = self._try_field_extraction(raw_text)
        if result:
            self.fallback_count += 1
            logger.info(f"Fallback field extraction usado (total: {self.fallback_count})")
            return result, method

        result = self._build_from_raw_text(raw_text)
        self.fallback_count += 1
        logger.info(f"Fallback raw text usado (total: {self.fallback_count})")
        return result.to_dict(), "raw_fallback"

    def _try_json_parse(self, text: str) -> tuple[dict | None, str]:
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        start_idx = text.find("{")
        if start_idx == -1:
            return None, ""

        depth = 0
        end_idx = start_idx
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start_idx:], start_idx):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

        if depth == 0 and end_idx > start_idx:
            json_str = text[start_idx : end_idx + 1]
            json_str = self._fix_json_syntax(json_str)

            try:
                data = json.loads(json_str)
                validated = self._validate_and_complete(data)
                return validated.to_dict(), "json"
            except json.JSONDecodeError:
                pass

        return None, ""

    def _try_semicolon_parse(self, text: str) -> tuple[dict | None, str]:
        if ";" not in text:
            return None, ""

        parts = [p.strip() for p in text.split(";") if p.strip()]

        if len(parts) < 2:
            return None, ""

        result = LunaResponseData()

        for i, part in enumerate(parts):
            part_lower = part.lower()

            if i == 0 or (not result.fala_tts and len(part) > 10):
                result.fala_tts = self._clean_text(part)
                continue

            if ":" in part:
                key, value = part.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key in ["fala", "fala_tts", "texto", "resposta"]:
                    result.fala_tts = self._clean_text(value)
                elif key in ["leitura", "tom", "emocao"]:
                    result.leitura = value
                elif key in ["log", "log_terminal", "terminal"]:
                    result.log_terminal = value
                elif key in ["animacao", "anim", "expressao"]:
                    result.animacao = self._normalize_animation(value)
                elif key in ["visao", "comando_visao", "olhar"]:
                    result.comando_visao = value.lower() in ["true", "sim", "1", "yes"]
            else:
                if "_" in part_lower and any(e in part_lower for e in ["luna", "juno", "eris", "lars"]):
                    result.animacao = self._normalize_animation(part)
                elif part_lower in ["true", "false", "sim", "nao"]:
                    result.comando_visao = part_lower in ["true", "sim"]
                elif len(part) > 20 and not result.fala_tts:
                    result.fala_tts = self._clean_text(part)

        if result.fala_tts:
            if not result.log_terminal:
                action = self._detect_action(result.fala_tts)
                entity_name = get_entity_prefix()
                result.log_terminal = f"[{entity_name} {action}] {result.fala_tts}"
            return result.to_dict(), "semicolon"

        return None, ""

    def _try_field_extraction(self, text: str) -> tuple[dict | None, str]:
        result = LunaResponseData()

        entity_name = get_entity_prefix()
        patterns = {
            "fala_tts": [
                r'"fala_tts"\s*:\s*"((?:[^"\\]|\\.)*)"',
                r'fala_tts\s*[=:]\s*["\']?(.*?)["\']?(?:;|$)',
                r'resposta\s*[=:]\s*["\']?(.*?)["\']?(?:;|$)',
            ],
            "leitura": [
                r'"leitura"\s*:\s*"((?:[^"\\]|\\.)*)"',
                r'leitura\s*[=:]\s*["\']?(.*?)["\']?(?:;|$)',
                r'tom\s*[=:]\s*["\']?(.*?)["\']?(?:;|$)',
            ],
            "log_terminal": [
                r'"log_terminal"\s*:\s*"((?:[^"\\]|\\.)*)"',
                r'log_terminal\s*[=:]\s*["\']?(.*?)["\']?(?:;|$)',
            ],
            "animacao": [
                r'"animacao"\s*:\s*"([^"]+)"',
                rf'animacao\s*[=:]\s*["\']?({entity_name}_\w+)["\']?',
                rf"\b({entity_name}_\w+)\b",
                r'animacao\s*[=:]\s*["\']?(\w+_\w+)["\']?',
                r"\b(\w+_(?:observando|sarcastica|curiosa|feliz|irritada|triste|apaixonada|flertando|neutra|piscando|sensualizando|obssecada))\b",
            ],
            "comando_visao": [
                r'"comando_visao"\s*:\s*(true|false)',
                r"comando_visao\s*[=:]\s*(true|false|sim|nao)",
            ],
        }

        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    if field_name == "fala_tts":
                        result.fala_tts = self._clean_text(value)
                    elif field_name == "leitura":
                        result.leitura = value
                    elif field_name == "log_terminal":
                        result.log_terminal = value
                    elif field_name == "animacao":
                        result.animacao = self._normalize_animation(value)
                    elif field_name == "comando_visao":
                        result.comando_visao = value.lower() in ["true", "sim"]
                    break

        if result.fala_tts:
            if not result.log_terminal:
                action = self._detect_action(result.fala_tts)
                result.log_terminal = f"[{entity_name} {action}] {result.fala_tts}"
            return result.to_dict(), "field_extraction"

        return None, ""

    def _build_from_raw_text(self, text: str) -> LunaResponseData:
        result = LunaResponseData()
        entity_name = get_entity_prefix()

        text = re.sub(
            rf"^(Pronouns?|Interlocutor|User|Assistant|{entity_name}|Response):?\s*",
            "",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        text = re.sub(r'[{}\[\]"]', " ", text)
        text = re.sub(
            r"\b(fala_tts|leitura|log_terminal|animacao|comando_visao|tts_config|registrar_rosto|filesystem_ops|speed|stability|style|true|false|null)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\s+", " ", text).strip()

        if text:
            result.fala_tts = text[:300]
        else:
            result.fala_tts = "Hmm, deixa eu pensar..."

        result.animacao = self._detect_emotion(result.fala_tts)
        action = self._detect_action(result.fala_tts)
        result.log_terminal = f"[{entity_name} {action}] {result.fala_tts}"

        return result

    def _validate_and_complete(self, data: dict) -> LunaResponseData:
        result = LunaResponseData()
        entity_name = get_entity_prefix()
        default_anim = f"{entity_name}_observando"

        result.fala_tts = self._clean_text(data.get("fala_tts", ""))
        result.leitura = data.get("leitura", "Normal")
        result.log_terminal = data.get("log_terminal", "")
        result.animacao = self._normalize_animation(data.get("animacao", default_anim))
        result.comando_visao = bool(data.get("comando_visao", False))
        result.registrar_rosto = data.get("registrar_rosto")
        result.filesystem_ops = data.get("filesystem_ops", [])

        if isinstance(data.get("tts_config"), dict):
            result.tts_config = {
                "speed": max(0.8, min(1.2, float(data["tts_config"].get("speed", 1.0)))),
                "stability": max(0.1, min(1.0, float(data["tts_config"].get("stability", 0.5)))),
                "style": max(0.0, min(1.0, float(data["tts_config"].get("style", 0.3)))),
            }

        if not result.log_terminal and result.fala_tts:
            action = self._detect_action(result.fala_tts)
            result.log_terminal = f"[{entity_name} {action}] {result.fala_tts}"

        return result

    def _fix_json_syntax(self, text: str) -> str:
        text = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)
        return text

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[\x00-\x1f]", "", text)
        text = text.replace("\\n", " ").replace("\\r", "").replace("\\t", " ")
        text = re.sub(r"\s+", " ", text).strip()

        prefixes = ["fala:", "fala_tts:", "resposta:", "texto:"]
        text_lower = text.lower()
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                text = text[len(prefix) :].strip()
                break

        return self._remove_emojis(text)[:300]

    def _remove_emojis(self, text: str) -> str:
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

    def _normalize_animation(self, value: str) -> str:
        entity_name = get_entity_prefix()
        default_anim = f"{entity_name}_observando"

        if not value:
            return default_anim

        value = value.strip()

        if value in config.ANIMATION_TO_EMOTION:
            return value

        for known_entity in ["Luna", "Juno", "Eris", "Lars"]:
            if value.startswith(f"{known_entity}_"):
                emotion = value[len(known_entity) + 1 :]
                target_anim = f"{entity_name}_{emotion}"
                if target_anim in config.ANIMATION_TO_EMOTION:
                    return target_anim
                break

        if "_" not in value:
            target_anim = f"{entity_name}_{value.lower()}"
            if target_anim in config.ANIMATION_TO_EMOTION:
                return target_anim

        for anim in config.ANIMATION_TO_EMOTION.keys():
            if anim.startswith(f"{entity_name}_"):
                emotion_part = anim[len(entity_name) + 1 :]
                if emotion_part.lower() in value.lower() or value.lower() in emotion_part.lower():
                    return anim

        return default_anim

    def _detect_emotion(self, text: str) -> str:
        text_lower = text.lower()
        entity_name = get_entity_prefix()

        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return f"{entity_name}_{emotion}"

        return f"{entity_name}_observando"

    def _detect_action(self, text: str) -> str:
        text_lower = text.lower()

        for pattern, action in ACTION_PATTERNS:
            if re.search(pattern, text_lower):
                return action

        emotion_anim = self._detect_emotion(text)
        if "_" in emotion_anim:
            emotion = emotion_anim.split("_", 1)[1]
        else:
            emotion = "observando"

        emotion_actions = {
            "sarcastica": "revira os olhos",
            "curiosa": "inclina a cabeca",
            "feliz": "sorri",
            "irritada": "franze a testa",
            "triste": "suspira",
            "apaixonada": "sorri suavemente",
            "flertando": "pisca",
        }

        return emotion_actions.get(emotion, "observa")

    def _create_fallback(self, reason: str) -> LunaResponseData:
        entity_name = get_entity_prefix()
        return LunaResponseData(
            fala_tts="Hmm, tive um problema. Pode repetir?",
            leitura="Confusa",
            log_terminal=f"[{entity_name} franze a testa] {reason}",
            animacao=f"{entity_name}_observando",
            comando_visao=False,
        )

    def get_stats(self) -> dict:
        total = self.success_count + self.fallback_count
        return {
            "total_parsed": total,
            "json_success": self.success_count,
            "fallback_used": self.fallback_count,
            "fallback_rate": self.fallback_count / max(total, 1),
        }
