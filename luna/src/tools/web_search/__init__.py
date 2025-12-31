from .detection import REALTIME_KEYWORDS, SEARCH_PATTERNS, detect_search_intent
from .helpers import get_web_search
from .models import SearchResult
from .search import WebSearch

__all__ = [
    "SearchResult",
    "WebSearch",
    "get_web_search",
    "detect_search_intent",
    "SEARCH_PATTERNS",
    "REALTIME_KEYWORDS",
]
