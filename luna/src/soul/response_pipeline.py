"""
ResponsePipeline - Pipeline de processamento de respostas LLM.

Orquestra o fluxo completo de processamento:
1. Construcao de contexto (ContextBuilder)
2. Chamada ao LLM (generate ou generate_stream)
3. Parsing da resposta (ResponseParser)
4. Atualizacao de memoria e estado emocional

Classes principais:
    ResponsePipeline: Pipeline principal
    PipelineStage: Enum de estagios
    PipelineResult: Resultado do processamento

Funcoes de factory:
    get_response_pipeline(entity_id): Factory por entidade

Dependencias:
    - context_builder: Construcao de contexto
    - response_parser: Parsing de respostas
    - data_memory: Atualizacao de memoria
"""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.core.logging_config import get_logger
from src.data_memory.proactive_system import get_proactive_system
from src.soul.context_builder import BuiltContext, get_context_builder
from src.soul.emotional_state import analyze_sentiment, get_emotional_manager
from src.soul.response_parser import get_parser

logger = get_logger(__name__)


class PipelineStage(Enum):
    CONTEXT_BUILD = "context_build"
    LLM_CALL = "llm_call"
    RESPONSE_PARSE = "response_parse"
    ACTION_EXECUTE = "action_execute"
    MEMORY_UPDATE = "memory_update"


@dataclass
class PipelineResult:
    success: bool
    stage: PipelineStage
    context: BuiltContext | None = None
    raw_response: str | None = None
    parsed_response: dict | None = None
    error: str | None = None
    timing_ms: int = 0


class ResponsePipeline:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.context_builder = get_context_builder(entity_id)
        self.parser = get_parser()
        self.hooks: dict[PipelineStage, list] = {stage: [] for stage in PipelineStage}
        self._llm_caller: Callable | None = None

    def set_llm_caller(self, caller: Callable[[str], str]):
        self._llm_caller = caller

    def add_hook(self, stage: PipelineStage, hook: Callable):
        self.hooks[stage].append(hook)

    def remove_hook(self, stage: PipelineStage, hook: Callable):
        if hook in self.hooks[stage]:
            self.hooks[stage].remove(hook)

    def _run_hooks(self, stage: PipelineStage, data: Any):
        for hook in self.hooks[stage]:
            try:
                hook(data)
            except Exception as e:
                logger.error(f"Hook error at {stage}: {e}")

    def process(self, user_input: str, conversation_history: list[dict] = None, stream: bool = False) -> PipelineResult:
        start_time = datetime.now()
        result = PipelineResult(success=False, stage=PipelineStage.CONTEXT_BUILD)

        try:
            context = self.context_builder.build(user_input, conversation_history)
            result.context = context
            self._run_hooks(PipelineStage.CONTEXT_BUILD, context)
            logger.debug(f"Context built: ~{context.total_estimated_tokens} tokens")
        except Exception as e:
            result.error = f"Context build failed: {e}"
            logger.error(result.error)
            return result

        result.stage = PipelineStage.LLM_CALL
        try:
            if not self._llm_caller:
                raise ValueError("LLM caller not configured")

            prompt = self.context_builder.build_prompt(user_input, conversation_history)
            raw_response = self._llm_caller(prompt)
            result.raw_response = raw_response
            self._run_hooks(PipelineStage.LLM_CALL, raw_response)
            logger.debug(f"LLM response: {len(raw_response)} chars")
        except Exception as e:
            result.error = f"LLM call failed: {e}"
            logger.error(result.error)
            return result

        result.stage = PipelineStage.RESPONSE_PARSE
        try:
            parsed, parse_method = self.parser.parse(raw_response)
            result.parsed_response = parsed
            self._run_hooks(PipelineStage.RESPONSE_PARSE, parsed)
            logger.debug(f"Parsed via {parse_method}: animation={parsed.get('animacao')}")
        except Exception as e:
            result.error = f"Parse failed: {e}"
            logger.error(result.error)
            result.parsed_response = {
                "fala_tts": raw_response,
                "animacao": f"{self.entity_id.capitalize()}_observando",
                "log_terminal": "",
            }

        result.stage = PipelineStage.MEMORY_UPDATE
        try:
            from src.data_memory.smart_memory import get_entity_smart_memory

            memory = get_entity_smart_memory(self.entity_id)

            memory.add(user_input, source="user_input")

            fala = result.parsed_response.get("fala_tts", "")
            if fala:
                memory.add(fala, source="assistant_response")

            self._run_hooks(PipelineStage.MEMORY_UPDATE, result.parsed_response)
        except Exception as e:
            logger.warning(f"Memory update failed: {e}")

        sentiment = 0.0
        try:
            emotional_mgr = get_emotional_manager(self.entity_id)
            sentiment = analyze_sentiment(user_input)
            emotional_mgr.update(user_message=user_input, sentiment=sentiment)
        except Exception as e:
            logger.debug(f"Emotional state update failed: {e}")

        try:
            proactive = get_proactive_system(self.entity_id)
            proactive.record_interaction(sentiment=sentiment)

            dates = proactive.extract_dates_from_text(user_input)
            for date_str, _ in dates:
                proactive.record_date_mention(date_str, user_input[:100])
        except Exception as e:
            logger.debug(f"Proactive system update failed: {e}")

        result.success = True
        result.timing_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(f"Pipeline complete in {result.timing_ms}ms")
        return result

    def process_stream(
        self,
        user_input: str,
        conversation_history: list[dict] = None,
        llm_stream_caller: Callable[[str], Generator[str, None, None]] | None = None,
    ) -> Generator[dict, None, None]:
        start_time = datetime.now()

        try:
            context = self.context_builder.build(user_input, conversation_history)
            yield {"stage": "context", "tokens": context.total_estimated_tokens, "success": True}
        except Exception as e:
            yield {"stage": "context", "error": str(e), "success": False}
            return

        try:
            prompt = self.context_builder.build_prompt(user_input, conversation_history)
            yield {"stage": "prompt_ready", "prompt_length": len(prompt), "success": True}
        except Exception as e:
            yield {"stage": "prompt_ready", "error": str(e), "success": False}
            return

        accumulated_text = ""
        chunk_count = 0

        try:
            if llm_stream_caller:
                for chunk in llm_stream_caller(prompt):
                    accumulated_text += chunk
                    chunk_count += 1
                    yield {"stage": "chunk", "text": chunk, "chunk_index": chunk_count}
            elif self._llm_caller:
                response = self._llm_caller(prompt)
                accumulated_text = response
                yield {"stage": "chunk", "text": response, "chunk_index": 1}
            else:
                yield {"stage": "llm_call", "error": "No LLM caller configured", "success": False}
                return

            yield {"stage": "llm_complete", "total_chunks": chunk_count, "total_chars": len(accumulated_text)}

        except Exception as e:
            yield {"stage": "llm_call", "error": str(e), "success": False}
            return

        try:
            parsed, parse_method = self.parser.parse(accumulated_text)
            yield {"stage": "parsed", "animation": parsed.get("animacao"), "method": parse_method}
        except Exception as e:
            logger.warning(f"Parse stream failed: {e}")
            parsed = {
                "fala_tts": accumulated_text,
                "animacao": f"{self.entity_id.capitalize()}_observando",
                "log_terminal": "",
            }

        try:
            from src.data_memory.smart_memory import get_entity_smart_memory

            memory = get_entity_smart_memory(self.entity_id)
            memory.add(user_input, source="user_input")
            fala = parsed.get("fala_tts", "")
            if fala:
                memory.add(fala, source="assistant_response")
        except Exception as e:
            logger.warning(f"Memory update in stream failed: {e}")

        timing_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        yield {
            "stage": "complete",
            "success": True,
            "timing_ms": timing_ms,
            "parsed_response": parsed,
            "full_text": accumulated_text,
        }


_pipelines: dict[str, ResponsePipeline] = {}


def get_response_pipeline(entity_id: str) -> ResponsePipeline:
    if entity_id not in _pipelines:
        _pipelines[entity_id] = ResponsePipeline(entity_id)
    return _pipelines[entity_id]
