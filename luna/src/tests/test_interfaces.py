"""Testes para interfaces/Protocols."""

import pytest


class TestInterfaces:
    def test_import(self):
        from src.core.interfaces import IConsciencia, IBoca, IVisao

        assert IConsciencia is not None
        assert IBoca is not None
        assert IVisao is not None

    def test_protocols_are_protocols(self):
        from typing import Protocol, runtime_checkable

        from src.core.interfaces import IConsciencia

        assert hasattr(IConsciencia, "__protocol_attrs__") or issubclass(IConsciencia, Protocol)
