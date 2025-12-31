"""Testes para LunaLiveSession."""

import pytest


class TestLunaLiveSession:
    def test_import(self):
        from src.soul.live_session import LunaLiveSession

        assert LunaLiveSession is not None

    def test_class_exists(self):
        from src.soul import live_session

        assert hasattr(live_session, "LunaLiveSession")
