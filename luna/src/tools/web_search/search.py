import hashlib
import logging
import time
from datetime import datetime

from .models import SearchResult

logger = logging.getLogger(__name__)


class WebSearch:
    def __init__(self, cache_ttl: int = 3600, max_cache_size: int = 100):
        self.cache: dict[str, tuple] = {}
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.last_request_time = 0
        self.min_request_interval = 1.0

        self._duckduckgo_available = self._check_duckduckgo()
        logger.info(f"WebSearch inicializado (DuckDuckGo: {self._duckduckgo_available})")

    def _check_duckduckgo(self) -> bool:
        try:
            from ddgs import DDGS

            return True
        except ImportError:
            try:
                from duckduckgo_search import DDGS

                return True
            except ImportError:
                logger.warning("ddgs nao instalado. Execute: pip install ddgs")
                return False

    def _get_cache_key(self, query: str) -> str:
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _is_cache_valid(self, cache_key: str) -> bool:
        if cache_key not in self.cache:
            return False

        _, timestamp = self.cache[cache_key]
        return (time.time() - timestamp) < self.cache_ttl

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def search(self, query: str, max_results: int = 5, region: str = "br-pt") -> list[SearchResult]:
        if not query or not query.strip():
            logger.warning("Query vazia recebida")
            return []

        cache_key = self._get_cache_key(query)
        if self._is_cache_valid(cache_key):
            results, _ = self.cache[cache_key]
            logger.info(f"Cache hit para: '{query[:30]}...'")
            return results

        results = []

        if self._duckduckgo_available:
            results = self._search_duckduckgo(query, max_results, region)

        if not results:
            results = self._search_fallback(query, max_results)

        if results:
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]

            self.cache[cache_key] = (results, time.time())
            logger.info(f"Cached {len(results)} resultados para: '{query[:30]}...'")

        return results

    def _search_duckduckgo(self, query: str, max_results: int, region: str) -> list[SearchResult]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            self._rate_limit()

            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, region=region, safesearch="off", max_results=max_results))

            results = []
            for r in raw_results:
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", r.get("link", "")),
                        snippet=r.get("body", r.get("snippet", "")),
                        source="duckduckgo",
                        timestamp=time.time(),
                    )
                )

            logger.info(f"DuckDuckGo retornou {len(results)} resultados")
            return results

        except Exception as e:
            logger.error(f"Erro no DuckDuckGo: {e}")
            return []

    def _search_fallback(self, query: str, max_results: int) -> list[SearchResult]:
        logger.warning("DuckDuckGo indisponivel, tentando fallback Ollama...")

        ollama_result = self._search_ollama_fallback(query)
        if ollama_result:
            return ollama_result

        return [
            SearchResult(
                title="Busca indisponivel",
                url="",
                snippet=f"Nao foi possivel buscar por '{query}'. Instale: pip install duckduckgo_search",
                source="fallback",
                timestamp=time.time(),
            )
        ]

    def _search_ollama_fallback(self, query: str) -> list[SearchResult] | None:
        try:
            import requests

            ollama_url = "http://localhost:11434"

            try:
                health = requests.get(f"{ollama_url}/api/tags", timeout=2)
                if health.status_code != 200:
                    return None
            except Exception:
                logger.debug("Ollama nao disponivel para fallback")
                return None

            models_to_try = ["qwen2.5:7b", "llama3.1:8b", "dolphin-mistral", "llama3.2:3b"]
            available_model = None

            for model in models_to_try:
                try:
                    check = requests.post(f"{ollama_url}/api/show", json={"name": model}, timeout=2)
                    if check.status_code == 200:
                        available_model = model
                        break
                except Exception:
                    continue

            if not available_model:
                logger.debug("Nenhum modelo Ollama disponivel para fallback")
                return None

            prompt = f"""Voce e um assistente de busca. O usuario quer saber sobre: "{query}"

Responda de forma factual e concisa com as informacoes mais relevantes que voce conhece.
Se a pergunta for sobre eventos em tempo real (placar, cotacao, etc), explique que voce nao tem acesso a dados em tempo real.

Formate sua resposta assim:
TITULO: [titulo resumido]
RESUMO: [resposta factual em 2-3 frases]"""

            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": available_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 256},
                },
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "")

                if text:
                    title = query[:50]
                    snippet = text[:400]

                    if "TITULO:" in text:
                        parts = text.split("TITULO:", 1)
                        if len(parts) > 1:
                            rest = parts[1]
                            if "RESUMO:" in rest:
                                title_part, resumo_part = rest.split("RESUMO:", 1)
                                title = title_part.strip()[:50]
                                snippet = resumo_part.strip()[:400]

                    logger.info(f"Ollama fallback retornou resposta (model: {available_model})")
                    return [
                        SearchResult(
                            title=title,
                            url="",
                            snippet=snippet,
                            source=f"ollama:{available_model}",
                            timestamp=time.time(),
                        )
                    ]

        except Exception as e:
            logger.error(f"Erro no fallback Ollama: {e}")

        return None

    def search_news(self, query: str, max_results: int = 5, region: str = "br-pt") -> list[SearchResult]:
        if not self._duckduckgo_available:
            return self._search_fallback(query, max_results)

        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            self._rate_limit()

            with DDGS() as ddgs:
                raw_results = list(ddgs.news(query, region=region, safesearch="off", max_results=max_results))

            results = []
            for r in raw_results:
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", r.get("link", "")),
                        snippet=r.get("body", r.get("excerpt", "")),
                        source="duckduckgo_news",
                        timestamp=time.time(),
                    )
                )

            logger.info(f"DuckDuckGo News retornou {len(results)} resultados")
            return results

        except Exception as e:
            logger.error(f"Erro no DuckDuckGo News: {e}")
            return self._search_fallback(query, max_results)

    def format_for_prompt(self, results: list[SearchResult], max_chars: int = 1500) -> str:
        if not results:
            return "[Nenhum resultado encontrado nas entranhas da rede]"

        lines = ["[DADOS DA REDE - " + datetime.now().strftime("%d/%m/%Y %H:%M") + "]"]

        char_count = len(lines[0])
        for i, r in enumerate(results[:5], 1):
            entry = f"\n{i}. {r.title}\n   {r.snippet[:200]}..."

            if char_count + len(entry) > max_chars:
                lines.append("\n[...mais resultados omitidos]")
                break

            lines.append(entry)
            char_count += len(entry)

        lines.append("\n[FIM DOS DADOS DA REDE]")
        return "".join(lines)
