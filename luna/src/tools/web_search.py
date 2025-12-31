"""
WebSearch - Modulo de pesquisa web para Luna

Luna descreve esta habilidade como:
"Vasculhar as entranhas da rede" ou "ler o obituario digital do mundo"

#1 - Usa DuckDuckGo (privacidade, sem API key)
#2 - Fallback para Google Custom Search se configurado
#3 - Cache de resultados para evitar requests duplicadas
"""

import logging

from src.tools.web_search import (
    REALTIME_KEYWORDS,
    SEARCH_PATTERNS,
    SearchResult,
    WebSearch,
    detect_search_intent,
    get_web_search,
)

__all__ = [
    "SearchResult",
    "WebSearch",
    "get_web_search",
    "detect_search_intent",
    "SEARCH_PATTERNS",
    "REALTIME_KEYWORDS",
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    ws = WebSearch()

    test_queries = [
        "placar do jogo do Corinthians hoje",
        "noticias sobre inteligencia artificial",
        "qual a cotacao do dolar agora",
    ]

    for q in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {q}")

        search_term = detect_search_intent(q)
        if search_term:
            print(f"Termo detectado: {search_term}")
            results = ws.search(search_term)
            print(ws.format_for_prompt(results))
        else:
            print("Nenhuma intencao de busca detectada")
