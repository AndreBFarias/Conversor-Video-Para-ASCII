from .search import WebSearch

_web_search_instance: WebSearch | None = None


def get_web_search() -> WebSearch:
    global _web_search_instance
    if _web_search_instance is None:
        _web_search_instance = WebSearch()
    return _web_search_instance
