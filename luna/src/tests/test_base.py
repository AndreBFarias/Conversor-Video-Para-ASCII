"""Testes para providers/base.py - re-exporta de test_universal_llm.py."""

from src.tests.test_universal_llm import (
    TestLLMProviderBase,
    TestLLMResponse,
)

__all__ = [
    "TestLLMProviderBase",
    "TestLLMResponse",
]
