"""
WebSocket Handler - Streaming de chat via WebSocket.

Gerencia conexoes WebSocket para chat em tempo real:
- Conexao/desconexao de clientes
- Streaming de respostas token-by-token
- Broadcast de mensagens
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket desconectado. Total: {len(self.active_connections)}")

    async def send_json(self, websocket: WebSocket, data: dict[str, Any]):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Erro ao enviar JSON: {e}")

    async def broadcast(self, data: dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Erro no broadcast: {e}")


manager = ConnectionManager()


async def process_chat_stream(
    websocket: WebSocket,
    message: str,
    entity_id: str = "luna",
):
    try:
        from src.soul.response_pipeline import get_response_pipeline
        from src.soul.providers import get_universal_llm

        pipeline = get_response_pipeline(entity_id)
        llm = get_universal_llm()

        def stream_caller(prompt: str):
            return llm.generate_stream(prompt, "")

        await manager.send_json(websocket, {"type": "start", "message": message})

        accumulated_text = ""

        for event in pipeline.process_stream(message, llm_stream_caller=stream_caller):
            stage = event.get("stage")

            if stage == "chunk":
                chunk_text = event.get("text", "")
                accumulated_text += chunk_text
                await manager.send_json(
                    websocket,
                    {"type": "chunk", "text": chunk_text, "index": event.get("chunk_index", 0)},
                )
                await asyncio.sleep(0.01)

            elif stage == "complete":
                parsed = event.get("parsed_response", {})
                await manager.send_json(
                    websocket,
                    {
                        "type": "complete",
                        "full_text": accumulated_text,
                        "animation": parsed.get("animacao", "observando"),
                        "emotion": parsed.get("leitura"),
                        "timing_ms": event.get("timing_ms", 0),
                    },
                )

            elif stage == "context":
                await manager.send_json(
                    websocket,
                    {"type": "status", "message": "Construindo contexto..."},
                )

    except Exception as e:
        logger.error(f"Erro no stream de chat: {e}")
        await manager.send_json(
            websocket,
            {"type": "error", "message": str(e)},
        )


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                message = payload.get("message", "")
                entity_id = payload.get("entity_id", "luna")

                if message:
                    await process_chat_stream(websocket, message, entity_id)

            except json.JSONDecodeError:
                await manager.send_json(
                    websocket,
                    {"type": "error", "message": "JSON invalido"},
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        manager.disconnect(websocket)
