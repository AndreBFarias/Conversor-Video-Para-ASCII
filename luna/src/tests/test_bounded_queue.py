"""Testes para BoundedQueue."""

import pytest


class TestBoundedQueue:
    def test_import(self):
        from src.core.bounded_queue import BoundedQueue

        assert BoundedQueue is not None

    def test_create_queue(self):
        from src.core.bounded_queue import BoundedQueue

        queue = BoundedQueue(name="test_queue", maxsize=10)
        assert queue is not None
        assert queue.maxsize == 10
        assert queue.name == "test_queue"

    def test_put_get(self):
        from src.core.bounded_queue import BoundedQueue

        queue = BoundedQueue(name="test_queue", maxsize=5)
        queue.put("item1")
        result = queue.get()
        assert result == "item1"
