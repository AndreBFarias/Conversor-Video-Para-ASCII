from __future__ import annotations

import config

EXACT_HALLUCINATIONS = [
    "obrigado",
    "obrigada",
    "tchau",
    "adeus",
    "bye",
    "ok",
    "okay",
    "sim",
    "nao",
    "não",
    "oi",
    "olá",
    "hm",
    "hmm",
    "ah",
    "eh",
    "uh",
    "um",
    "e",
    "é",
    "a",
    "o",
    "i",
    "u",
    "ta",
    "tá",
    "né",
    "ne",
    "legal",
    "beleza",
    "blz",
    "vlw",
    "valeu",
    "certo",
    "entendi",
    "aham",
    "uhum",
    "hum",
    "pois",
    "pois é",
    "então",
    "entao",
    "tipo",
    "sei",
    "bom",
    "bem",
    "ai",
    "aí",
    "la",
    "lá",
]

PATTERN_HALLUCINATIONS = [
    "obrigado por assistir",
    "obrigado por teres assistido",
    "conversa em portugues",
    "conversa em português",
    "portugues brasileiro",
    "português brasileiro",
    "legendado por",
    "inscreva-se",
    "subscribe",
    "thank you for watching",
    "thanks for watching",
    "até logo",
    "ate logo",
    "até mais",
    "ate mais",
    "música",
    "musica",
    "♪",
    "...",
    "…",
    "silêncio",
    "silencio",
    "[música]",
    "[musica]",
    "não se esqueça",
    "nao se esqueca",
    "like",
    "deixe seu like",
    "compartilhe",
    "comente",
    "continue assistindo",
    "se inscreva",
    "clique aqui",
    "link na descricao",
    "vamos lá",
    "vamos la",
    "então vamos",
    "próximo vídeo",
    "proximo video",
    "por favor",
    "com licença",
    "com licenca",
    "desculpa",
    "desculpe",
    "perdão",
    "perdao",
    "aguarde",
    "espere",
    "um momento",
    "fala pessoal",
    "e aí pessoal",
    "e ai pessoal",
    "bom dia",
    "boa tarde",
    "boa noite",
    "fala galera",
    "opa",
    "epa",
    "ops",
    "a emissora",
    "emissora",
    "legendas",
    "aplausos",
    "risos",
    "[aplausos]",
    "[risos]",
    "gostou do video",
    "gostou do vídeo",
    "até a próxima",
    "ate a proxima",
    "nos vemos",
    "a gente se vê",
    "a gente se ve",
]


def is_hallucination(text: str) -> tuple[bool, str | None]:
    texto_lower = text.lower().strip()

    if texto_lower in EXACT_HALLUCINATIONS:
        return True, f"exact: '{text}'"

    if len(set(texto_lower.replace(" ", ""))) <= 3:
        return True, f"repetitive: '{text}'"

    all_patterns = PATTERN_HALLUCINATIONS + config.WHISPER_HALLUCINATION_FILTERS

    for pattern in all_patterns:
        if pattern in texto_lower:
            return True, f"pattern: '{pattern}'"

    if len(text) < 5:
        return True, f"too_short: '{text}'"

    return False, None


def filter_transcription(text: str) -> str | None:
    if len(text) < 2:
        return None

    is_hal, reason = is_hallucination(text)
    if is_hal:
        return None

    return text
