"""
Routes - Endpoints REST do dashboard.

Endpoints:
    GET /api/status: Status do sistema
    GET /api/entities: Lista de entidades
    GET /api/entity/{id}: Detalhes de uma entidade
    GET /api/metrics: Metricas do sistema
    GET /api/memory/stats: Estatisticas de memoria
    POST /api/chat: Enviar mensagem (sync)
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    entity_id: str = "luna"


class ChatResponse(BaseModel):
    response: str
    animation: str
    emotion: str | None = None


@router.get("/")
async def root():
    return {"status": "ok", "service": "Luna Dashboard", "version": "1.0.0"}


@router.get("/status")
async def get_status() -> dict[str, Any]:
    try:
        from src.core.health_check import get_health_check

        health = get_health_check()
        results = health.get_last_results()
        return {"status": "healthy", "details": results}
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return {"status": "degraded", "error": str(e)}


@router.get("/entities")
async def list_entities() -> dict[str, Any]:
    try:
        from src.core.entity_loader import REGISTRY_PATH
        from src.core.file_lock import read_json_safe

        registry = read_json_safe(REGISTRY_PATH)
        entities = []

        for entity_id, entity_data in registry.get("entities", {}).items():
            entities.append(
                {
                    "id": entity_id,
                    "name": entity_data.get("name", entity_id.capitalize()),
                    "available": entity_data.get("available", False),
                    "description": entity_data.get("description", ""),
                }
            )

        return {"entities": entities, "count": len(entities)}
    except Exception as e:
        logger.error(f"Erro ao listar entidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_id}")
async def get_entity(entity_id: str) -> dict[str, Any]:
    try:
        from src.core.entity_loader import EntityLoader

        loader = EntityLoader(entity_id)
        config = loader.get_config()

        return {
            "id": entity_id,
            "name": config.get("name", entity_id.capitalize()),
            "persona": config.get("persona", {}),
            "animations": list(config.get("animations", {}).keys()),
        }
    except Exception as e:
        logger.error(f"Erro ao obter entidade {entity_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Entidade {entity_id} nao encontrada")


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    try:
        from src.core.metricas import get_metrics as get_system_metrics

        metrics = get_system_metrics()
        return {
            "api_calls": metrics.get_api_call_count(),
            "tokens_used": metrics.get_total_tokens(),
            "avg_latency_ms": metrics.get_average_latency(),
            "errors": metrics.get_error_count(),
        }
    except Exception as e:
        logger.error(f"Erro ao obter metricas: {e}")
        return {"api_calls": 0, "tokens_used": 0, "avg_latency_ms": 0, "errors": 0}


@router.get("/memory/stats")
async def get_memory_stats() -> dict[str, Any]:
    try:
        from src.data_memory.smart_memory import get_smart_memory

        memory = get_smart_memory()
        stats = memory.get_stats()

        return {
            "total_memories": stats.get("total", 0),
            "by_category": stats.get("by_category", {}),
            "recent_count": stats.get("recent_24h", 0),
        }
    except Exception as e:
        logger.error(f"Erro ao obter stats de memoria: {e}")
        return {"total_memories": 0, "by_category": {}, "recent_count": 0}


@router.post("/chat", response_model=ChatResponse)
async def chat_sync(request: ChatRequest) -> ChatResponse:
    try:
        from src.soul.response_pipeline import get_response_pipeline
        from src.soul.providers import get_universal_llm

        pipeline = get_response_pipeline(request.entity_id)
        llm = get_universal_llm()

        pipeline.set_llm_caller(lambda prompt: llm.generate(prompt, "").text)

        result = pipeline.process(request.message)

        if result.success and result.parsed_response:
            return ChatResponse(
                response=result.parsed_response.get("fala_tts", ""),
                animation=result.parsed_response.get("animacao", "observando"),
                emotion=result.parsed_response.get("leitura"),
            )
        else:
            return ChatResponse(
                response="Desculpe, tive um problema ao processar sua mensagem.",
                animation="confusa",
                emotion="confused",
            )

    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request})
