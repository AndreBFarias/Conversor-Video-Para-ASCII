"""
Server - Servidor FastAPI principal.

Configura e inicializa o servidor web:
- CORS para desenvolvimento local
- Rotas REST e WebSocket
- Arquivos estaticos e templates
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)

WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Luna Dashboard",
        description="Interface web para Luna AI Assistant",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routes import router
    from .websocket_handler import websocket_endpoint

    app.include_router(router, prefix="/api")
    app.add_api_websocket_route("/ws/chat", websocket_endpoint)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @app.on_event("startup")
    async def startup_event():
        logger.info("Luna Dashboard iniciado")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Luna Dashboard encerrado")

    return app


def run_server(host: str = "0.0.0.0", port: int = 8080):
    app = create_app()
    logger.info(f"Iniciando servidor em http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
