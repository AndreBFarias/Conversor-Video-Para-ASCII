from __future__ import annotations

from .async_client import OllamaClient
from .models import OllamaResponse
from .sync_client import OllamaSyncClient

__all__ = [
    "OllamaClient",
    "OllamaResponse",
    "OllamaSyncClient",
]


_async_client: OllamaClient | None = None
_sync_client: OllamaSyncClient | None = None


def get_ollama_client(base_url: str | None = None, timeout: int | None = None) -> OllamaClient:
    global _async_client
    if _async_client is None:
        _async_client = OllamaClient(base_url, timeout)
    return _async_client


def get_ollama_sync_client(base_url: str | None = None, timeout: int | None = None) -> OllamaSyncClient:
    global _sync_client
    if _sync_client is None:
        _sync_client = OllamaSyncClient(base_url, timeout)
    return _sync_client


def reset_clients() -> None:
    global _async_client, _sync_client
    _async_client = None
    _sync_client = None
