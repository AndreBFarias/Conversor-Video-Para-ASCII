import logging
import re

logger = logging.getLogger(__name__)

SEARCH_PATTERNS = [
    (r"(?:qual|quem|quando|onde|como) (?:e|foi|esta|estao|ficou) (?:o|a|os|as)?\s*(.+?)(?:\?|$)", 1),
    (r"(?:placar|resultado|score) (?:do|da|de)?\s*(.+?)(?:\?|$)", 1),
    (r"(?:noticia|noticias|news) (?:sobre|de)?\s*(.+?)(?:\?|$)", 1),
    (r"(?:busque|pesquise|procure|search) (?:por|sobre|de)?\s*(.+?)(?:\?|$)", 1),
    (r"(?:o que|quem|qual) (?:e|foi|sao|eram)\s+(.+?)(?:\?|$)", 1),
    (r"(?:previsao|previsão|tempo|clima) (?:em|para|de)?\s*(.+?)(?:\?|$)", 1),
    (r"(?:cotacao|cotação|valor|preco|preço) (?:do|da|de)?\s*(.+?)(?:\?|$)", 1),
]

REALTIME_KEYWORDS = [
    "hoje",
    "agora",
    "atual",
    "atualmente",
    "no momento",
    "ultimas",
    "últimas",
    "recente",
    "acabou de",
    "placar",
    "resultado",
    "jogo",
    "partida",
    "cotacao",
    "cotação",
    "dolar",
    "euro",
    "bitcoin",
    "tempo",
    "clima",
    "previsao",
    "previsão",
]


def detect_search_intent(text: str) -> str | None:
    text_lower = text.lower().strip()

    for pattern, group in SEARCH_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            search_term = match.group(group).strip()
            if len(search_term) > 3:
                logger.info(f"Detectada intencao de busca: '{search_term}'")
                return search_term

    if any(kw in text_lower for kw in REALTIME_KEYWORDS):
        words = text_lower.split()
        if len(words) > 2:
            search_term = " ".join(words[:8])
            logger.info(f"Keyword realtime detectada, buscando: '{search_term}'")
            return search_term

    return None
