"""
Extrator e reparador de JSON de respostas LLM.

Este modulo lida com a extracao de JSON de texto livre,
reparo de sintaxe quebrada, e construcao de JSON a partir
de texto quando o LLM falha em gerar JSON valido.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import config
from src.core.entity_loader import get_entity_name
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class JSONExtractor:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id

    def extract(self, text: str) -> str:
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = text.strip()

        start_idx = text.find("{")
        if start_idx == -1:
            logger.warning("Nenhum JSON encontrado na resposta")
            return self.build_from_text(text)

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
            extracted = text[start_idx : end_idx + 1]
            return self.fix_syntax(extracted)

        logger.warning("JSON incompleto, tentando reparar...")
        partial = text[start_idx:]
        open_braces = partial.count("{") - partial.count("}")
        if open_braces > 0:
            partial += "}" * open_braces
        return self.fix_syntax(partial)

    def fix_syntax(self, text: str) -> str:
        text = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)

        text = re.sub(r"\\\\u([0-9a-fA-F]{4})", r"\\u\1", text)

        return text

    def build_from_text(self, text: str) -> str:
        entity_name = get_entity_name(self.entity_id)
        if not text:
            return json.dumps(
                {
                    "fala_tts": "Desculpe, nao entendi.",
                    "leitura": "Normal",
                    "log_terminal": f"[{entity_name} confusa]",
                    "animacao": f"{entity_name}_observando",
                    "comando_visao": False,
                    "tts_config": {"speed": 1.0, "stability": 0.5},
                    "registrar_rosto": None,
                    "filesystem_ops": [],
                },
                ensure_ascii=False,
            )

        original_text = text
        text = re.sub(
            r"^(Pronouns?|Interlocutor|User|Assistant|Luna|Response):?\s*", "", text, flags=re.IGNORECASE | re.MULTILINE
        )

        def extract_field(pattern: str, default: str = None) -> str:
            match = re.search(pattern, original_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else default

        fala = extract_field(r'"fala_tts"\s*:\s*"((?:[^"\\]|\\.)*)"')
        log_terminal = extract_field(r'"log_terminal"\s*:\s*"((?:[^"\\]|\\.)*)"')
        leitura = extract_field(r'"leitura"\s*:\s*"((?:[^"\\]|\\.)*)"', "Normal")
        animacao = extract_field(r'"animacao"\s*:\s*"([^"]+)"')
        comando_visao = extract_field(r'"comando_visao"\s*:\s*(true|false)', "false")

        speed_match = re.search(r'"speed"\s*:\s*([\d.]+)', text)
        stability_match = re.search(r'"stability"\s*:\s*([\d.]+)', text)
        style_match = re.search(r'"style"\s*:\s*([\d.]+)', text)

        speed = float(speed_match.group(1)) if speed_match else 1.0
        stability = float(stability_match.group(1)) if stability_match else 0.5
        style = float(style_match.group(1)) if style_match else 0.3

        speed = max(0.8, min(1.2, speed))
        stability = max(0.1, min(1.0, stability))
        style = max(0.0, min(1.0, style))

        if not fala:
            quoted = re.findall(r'"([^"]{15,})"', text)
            field_names = [
                "fala_tts",
                "leitura",
                "log_terminal",
                "animacao",
                "comando_visao",
                "tts_config",
                "registrar_rosto",
                "filesystem_ops",
                "speed",
                "stability",
                "style",
            ]
            for q in quoted:
                if q.lower() not in field_names and not q.startswith("Luna_"):
                    fala = q[:300]
                    break

        if not fala:
            clean = re.sub(r'[{}\[\]":]', " ", text)
            clean = re.sub(
                r"\b(fala_tts|leitura|log_terminal|animacao|comando_visao|tts_config|registrar_rosto|filesystem_ops|speed|stability|style|true|false|null|Luna_\w+)\b",
                "",
                clean,
                flags=re.IGNORECASE,
            )
            clean = re.sub(r"\s+", " ", clean).strip()
            fala = clean[:300] if clean else "Hmm, deixa eu pensar..."

        if not log_terminal:
            log_terminal = fala

        actions = re.findall(r"\[([^\]]+)\]", log_terminal)
        if not actions:
            fala_lower = fala.lower()
            if any(w in fala_lower for w in ["mortal", "tedio", "obvio"]):
                log_terminal = f"[{entity_name} revira os olhos] {log_terminal}"
            elif any(w in fala_lower for w in ["curioso", "interessante", "hmm"]):
                log_terminal = f"[{entity_name} inclina a cabeca] {log_terminal}"
            elif any(w in fala_lower for w in ["irritada", "raiva", "droga"]):
                log_terminal = f"[{entity_name} franze a testa] {log_terminal}"
            elif any(w in fala_lower for w in ["amor", "querido", "fofo"]):
                log_terminal = f"[{entity_name} sorri suavemente] {log_terminal}"

        if animacao and animacao in config.ANIMATION_TO_EMOTION:
            pass
        else:
            animacao = f"{entity_name}_observando"
            fala_lower = fala.lower()
            if any(w in fala_lower for w in ["haha", "riso", "piada", "engracado"]):
                animacao = f"{entity_name}_rindo"
            elif any(w in fala_lower for w in ["curioso", "interessante", "hmm", "deixa eu ver"]):
                animacao = f"{entity_name}_curiosa"
            elif any(w in fala_lower for w in ["serio", "importante", "atencao"]):
                animacao = f"{entity_name}_seria"
            elif any(w in fala_lower for w in ["triste", "pena", "sinto muito"]):
                animacao = f"{entity_name}_triste"
            elif any(w in fala_lower for w in ["irritada", "raiva", "droga", "merda"]):
                animacao = f"{entity_name}_irritada"
            elif any(w in fala_lower for w in ["amor", "querido", "fofo", "doce"]):
                animacao = f"{entity_name}_apaixonada"
            elif any(w in fala_lower for w in ["mortal", "tedio", "obvio", "claro"]):
                animacao = f"{entity_name}_sarcastica"
            elif any(w in fala_lower for w in ["olhe", "veja", "camera", "webcam"]):
                animacao = f"{entity_name}_curiosa"

        def sanitize(s: str) -> str:
            s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "").replace("\t", " ")
            return re.sub(r"[\x00-\x1f]", "", s)

        fala = sanitize(fala)[:300]
        log_terminal = sanitize(log_terminal)[:500]
        leitura = sanitize(leitura)[:100]

        logger.info(f"JSON construido: fala={fala[:40]}... animacao={animacao} visao={comando_visao}")

        return json.dumps(
            {
                "fala_tts": fala,
                "leitura": leitura,
                "log_terminal": log_terminal,
                "animacao": animacao,
                "comando_visao": comando_visao.lower() == "true",
                "tts_config": {"speed": speed, "stability": stability, "style": style},
                "registrar_rosto": None,
                "filesystem_ops": [],
            },
            ensure_ascii=False,
        )


def get_json_extractor(entity_id: str) -> JSONExtractor:
    return JSONExtractor(entity_id)
