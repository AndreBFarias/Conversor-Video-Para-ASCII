from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .container import ServiceContainer


def create_config_provider(container: ServiceContainer) -> Any:
    from .adapters import ConfigProviderAdapter

    return ConfigProviderAdapter()


def create_memory_store(container: ServiceContainer) -> Any:
    from src.core.entity_loader import get_active_entity
    from src.data_memory.smart_memory import get_entity_smart_memory

    entity_id = get_active_entity()
    return get_entity_smart_memory(entity_id)


def create_llm_client(container: ServiceContainer) -> Any:
    from .adapters import LLMClientAdapter

    config = container.config
    provider = config.get("CHAT_PROVIDER", "local")
    return LLMClientAdapter(provider, config)


def create_tts_engine(container: ServiceContainer) -> Any:
    from .adapters import TTSEngineAdapter

    config = container.config
    return TTSEngineAdapter(config)


def create_vision_provider(container: ServiceContainer) -> Any:
    from .adapters import VisionProviderAdapter

    config = container.config
    return VisionProviderAdapter(config)


def create_context_builder(container: ServiceContainer) -> Any:
    from src.core.entity_loader import get_active_entity
    from src.soul.context_builder import get_context_builder

    entity_id = get_active_entity()
    return get_context_builder(entity_id)


def create_semantic_cache(container: ServiceContainer) -> Any:
    from src.soul.semantic_cache import SemanticCache

    config = container.config
    cache_config = config.get_nested("CACHE_CONFIG", default={})
    return SemanticCache(
        l1_capacity=cache_config.get("L1_CAPACITY", 100),
        l1_ttl_seconds=cache_config.get("L1_TTL", 3600),
        l2_enabled=cache_config.get("L2_ENABLED", True),
    )


def create_rate_limiter(container: ServiceContainer) -> Any:
    from src.soul.rate_limiter import SmartRateLimiter

    config = container.config
    rate_config = config.get_nested("RATE_LIMITER_CONFIG", default={})
    return SmartRateLimiter(
        max_requests_per_minute=rate_config.get("MAX_REQUESTS_PER_MINUTE", 60),
        max_tokens_per_minute=rate_config.get("MAX_TOKENS_PER_MINUTE", 100000),
        burst_allowance=rate_config.get("BURST_ALLOWANCE", 5),
    )


def create_entity_loader(container: ServiceContainer) -> Any:
    from src.core.entity_loader import EntityLoader, get_active_entity

    entity_id = get_active_entity()
    return EntityLoader(entity_id)


def create_animation_controller(container: ServiceContainer) -> Any:
    return None


def create_audio_player(container: ServiceContainer) -> Any:
    return None


def create_logger(container: ServiceContainer) -> Any:
    from src.core.logging_config import get_logger

    return get_logger("luna")


def create_consciencia_factory(container: ServiceContainer) -> Any:
    def factory(app: Any) -> Any:
        from src.soul import Consciencia

        return Consciencia(app)

    return factory


def create_boca_factory(container: ServiceContainer) -> Any:
    def factory() -> Any:
        from src.soul import Boca

        return Boca()

    return factory


def create_visao_factory(container: ServiceContainer) -> Any:
    def factory() -> Any:
        from src.soul import Visao

        return Visao()

    return factory


def create_ouvido_factory(container: ServiceContainer) -> Any:
    def factory() -> Any | None:
        from src.soul import VOICE_AVAILABLE, OuvidoSussurrante

        if VOICE_AVAILABLE:
            try:
                return OuvidoSussurrante()
            except Exception:
                return None
        return None

    return factory


def create_session_manager_factory(container: ServiceContainer) -> Any:
    def factory(app: Any) -> Any:
        from src.core import SessionManager

        return SessionManager(app)

    return factory


def create_animation_controller_factory(container: ServiceContainer) -> Any:
    def factory(app: Any) -> Any:
        from src.core import AnimationController

        return AnimationController(app)

    return factory


def register_default_services(container: ServiceContainer) -> ServiceContainer:
    from .container import ServiceLifetime

    container.register("config", create_config_provider, ServiceLifetime.SINGLETON)
    container.register("memory", create_memory_store, ServiceLifetime.SINGLETON)
    container.register("llm", create_llm_client, ServiceLifetime.SINGLETON)
    container.register("tts", create_tts_engine, ServiceLifetime.SINGLETON)
    container.register("vision", create_vision_provider, ServiceLifetime.SINGLETON)
    container.register("context_builder", create_context_builder, ServiceLifetime.SINGLETON)
    container.register("cache", create_semantic_cache, ServiceLifetime.SINGLETON)
    container.register("rate_limiter", create_rate_limiter, ServiceLifetime.SINGLETON)
    container.register("entity_loader", create_entity_loader, ServiceLifetime.SINGLETON)
    container.register("animation", create_animation_controller, ServiceLifetime.SINGLETON)
    container.register("audio", create_audio_player, ServiceLifetime.SINGLETON)
    container.register("logger", create_logger, ServiceLifetime.SINGLETON)

    container.register("consciencia_factory", create_consciencia_factory, ServiceLifetime.SINGLETON)
    container.register("boca_factory", create_boca_factory, ServiceLifetime.SINGLETON)
    container.register("visao_factory", create_visao_factory, ServiceLifetime.SINGLETON)
    container.register("ouvido_factory", create_ouvido_factory, ServiceLifetime.SINGLETON)
    container.register("session_manager_factory", create_session_manager_factory, ServiceLifetime.SINGLETON)
    container.register("animation_controller_factory", create_animation_controller_factory, ServiceLifetime.SINGLETON)

    return container
