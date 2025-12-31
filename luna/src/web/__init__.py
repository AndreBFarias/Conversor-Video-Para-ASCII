"""
Web Dashboard - Interface web para Luna.

Fornece um dashboard web usando FastAPI:
- Endpoints REST para status e configuracao
- WebSocket para streaming de chat
- Frontend HTML/JS simples

Modulos:
    server: Servidor FastAPI principal
    websocket_handler: Handler de WebSocket para chat
    routes: Rotas REST

Para iniciar:
    python -m src.web.server
"""

from .routes import router
from .server import create_app
from .websocket_handler import ConnectionManager

__all__ = [
    "create_app",
    "router",
    "ConnectionManager",
]
