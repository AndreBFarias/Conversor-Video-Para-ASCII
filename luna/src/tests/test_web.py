"""
Testes para o modulo web.
"""

import asyncio
from unittest.mock import MagicMock, patch


class TestWebServer:
    def test_create_app_returns_fastapi(self):
        with patch("src.web.server.STATIC_DIR") as mock_static:
            mock_static.exists.return_value = False

            from src.web.server import create_app

            app = create_app()

            assert app is not None
            assert app.title == "Luna Dashboard"

    def test_create_app_includes_router(self):
        with patch("src.web.server.STATIC_DIR") as mock_static:
            mock_static.exists.return_value = False

            from src.web.server import create_app

            app = create_app()
            routes = [r.path for r in app.routes]

            assert "/api/" in str(routes) or any("/api" in str(r) for r in routes)


class TestRoutes:
    def test_root_endpoint(self):
        from src.web.routes import root

        result = asyncio.run(root())

        assert result["status"] == "ok"
        assert result["service"] == "Luna Dashboard"

    def test_get_status_handles_error(self):
        from src.web.routes import get_status

        async def run_test():
            with patch("src.core.health_check.get_health_check", side_effect=Exception("mock")):
                return await get_status()

        result = asyncio.run(run_test())

        assert "status" in result
        assert result["status"] in ["healthy", "degraded"]

    def test_get_metrics_returns_defaults_on_error(self):
        from src.web.routes import get_metrics

        async def run_test():
            with patch("src.core.metricas.get_metrics", side_effect=Exception("mock")):
                return await get_metrics()

        result = asyncio.run(run_test())

        assert result["api_calls"] == 0
        assert result["tokens_used"] == 0

    def test_get_memory_stats_returns_defaults_on_error(self):
        from src.web.routes import get_memory_stats

        async def run_test():
            with patch("src.data_memory.smart_memory.get_smart_memory", side_effect=Exception("mock")):
                return await get_memory_stats()

        result = asyncio.run(run_test())

        assert result["total_memories"] == 0


class TestWebSocketHandler:
    def test_connection_manager_init(self):
        from src.web.websocket_handler import ConnectionManager

        manager = ConnectionManager()

        assert manager.active_connections == []

    def test_connection_manager_disconnect_empty(self):
        from src.web.websocket_handler import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()

        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections

    def test_connection_manager_disconnect_removes(self):
        from src.web.websocket_handler import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.active_connections.append(mock_ws)

        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections


class TestWebModuleInit:
    def test_exports(self):
        from src.web import ConnectionManager, create_app, router

        assert create_app is not None
        assert router is not None
        assert ConnectionManager is not None

    def test_docstring_exists(self):
        import src.web

        assert src.web.__doc__ is not None
        assert "Dashboard" in src.web.__doc__
