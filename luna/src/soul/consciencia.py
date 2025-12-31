"""
Consciencia - Modulo central de processamento de LLM.

Este modulo e o coracao do sistema Luna, responsavel por:
- Processar comandos do usuario via LLM (Gemini/Ollama)
- Gerenciar contexto de conversacao
- Executar comandos de terminal
- Coordenar com memoria semantica e estado emocional

Classes principais:
    Consciencia: Classe principal de processamento

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/consciencia/
"""

from src.soul.consciencia import (
    Consciencia,
    build_full_prompt,
    build_memory_context,
    call_llm,
    call_with_universal_llm,
    compress_conversation,
    execute_filesystem_ops,
    fallback_response,
    get_llm_status,
    get_model_for_intent_routing,
    has_provider,
    init_components,
    init_provider,
    init_soul_prompt,
    on_llm_fallback,
    post_process_response,
    process_web_search,
    reload_for_entity,
    save_to_memory,
    stream_response,
    update_history,
    update_memory_tiers,
    update_personality_anchor,
    validate_schema,
    warmup_memory,
)

__all__ = [
    "Consciencia",
    "validate_schema",
    "fallback_response",
    "get_model_for_intent_routing",
    "compress_conversation",
    "call_llm",
    "has_provider",
    "on_llm_fallback",
    "call_with_universal_llm",
    "get_llm_status",
    "stream_response",
    "warmup_memory",
    "build_memory_context",
    "save_to_memory",
    "update_memory_tiers",
    "post_process_response",
    "execute_filesystem_ops",
    "update_history",
    "update_personality_anchor",
    "init_soul_prompt",
    "build_full_prompt",
    "init_provider",
    "init_components",
    "reload_for_entity",
    "process_web_search",
]
