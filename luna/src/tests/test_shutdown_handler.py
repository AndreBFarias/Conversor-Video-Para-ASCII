"""Testes para ShutdownHandler."""

import pytest


class TestShutdownHandler:
    def test_import(self):
        from src.core.shutdown_handler import ShutdownHandler

        assert ShutdownHandler is not None

    def test_create_handler(self):
        from src.core.shutdown_handler import ShutdownHandler

        handler = ShutdownHandler()
        assert handler is not None

    def test_register_callback(self):
        from src.core.shutdown_handler import ShutdownHandler

        handler = ShutdownHandler()
        called = []

        def callback():
            called.append(True)

        handler.register(callback)
        assert len(handler.callbacks) >= 1
