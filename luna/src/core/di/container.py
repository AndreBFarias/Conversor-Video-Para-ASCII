from __future__ import annotations

import threading
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from src.core.logging_config import get_logger

if TYPE_CHECKING:
    from .protocols import (
        IAnimationController,
        IAudioPlayer,
        IConfigProvider,
        IContextBuilder,
        IEntityLoader,
        ILLMClient,
        ILogger,
        IMemoryStore,
        IRateLimiter,
        ISemanticCache,
        ITTSEngine,
        IVisionProvider,
    )

logger = get_logger(__name__)

T = TypeVar("T")


class ServiceLifetime(Enum):
    SINGLETON = auto()
    TRANSIENT = auto()
    SCOPED = auto()


class ServiceDescriptor:
    __slots__ = ("factory", "lifetime", "instance")

    def __init__(
        self,
        factory: Callable[["ServiceContainer"], Any],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        self.factory = factory
        self.lifetime = lifetime
        self.instance: Any = None


class ServiceContainer:
    _instance: ServiceContainer | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._services: dict[str, ServiceDescriptor] = {}
        self._scoped_instances: dict[str, Any] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> ServiceContainer:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                cls._instance._services.clear()
                cls._instance._scoped_instances.clear()
                cls._instance._initialized = False
            cls._instance = None

    def register(
        self,
        service_type: str,
        factory: Callable[[ServiceContainer], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> ServiceContainer:
        self._services[service_type] = ServiceDescriptor(factory, lifetime)
        return self

    def register_instance(
        self,
        service_type: str,
        instance: T,
    ) -> ServiceContainer:
        descriptor = ServiceDescriptor(lambda _: instance, ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor
        return self

    def resolve(self, service_type: str) -> Any:
        if service_type not in self._services:
            raise KeyError(f"Service '{service_type}' not registered")

        descriptor = self._services[service_type]

        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is None:
                descriptor.instance = descriptor.factory(self)
            return descriptor.instance

        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = descriptor.factory(self)
            return self._scoped_instances[service_type]

        return descriptor.factory(self)

    def try_resolve(self, service_type: str) -> Any | None:
        try:
            return self.resolve(service_type)
        except KeyError:
            return None

    def is_registered(self, service_type: str) -> bool:
        return service_type in self._services

    def clear_scoped(self) -> None:
        self._scoped_instances.clear()

    def override(
        self,
        service_type: str,
        factory: Callable[[ServiceContainer], T],
    ) -> ServiceContainer:
        if service_type in self._services:
            old_descriptor = self._services[service_type]
            old_descriptor.instance = None
        self._services[service_type] = ServiceDescriptor(factory, ServiceLifetime.SINGLETON)
        return self

    def override_instance(
        self,
        service_type: str,
        instance: T,
    ) -> ServiceContainer:
        descriptor = ServiceDescriptor(lambda _: instance, ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor
        return self

    @property
    def config(self) -> IConfigProvider:
        return self.resolve("config")

    @property
    def memory(self) -> IMemoryStore:
        return self.resolve("memory")

    @property
    def llm(self) -> ILLMClient:
        return self.resolve("llm")

    @property
    def tts(self) -> ITTSEngine:
        return self.resolve("tts")

    @property
    def vision(self) -> IVisionProvider:
        return self.resolve("vision")

    @property
    def context_builder(self) -> IContextBuilder:
        return self.resolve("context_builder")

    @property
    def cache(self) -> ISemanticCache:
        return self.resolve("cache")

    @property
    def rate_limiter(self) -> IRateLimiter:
        return self.resolve("rate_limiter")

    @property
    def entity_loader(self) -> IEntityLoader:
        return self.resolve("entity_loader")

    @property
    def animation(self) -> IAnimationController:
        return self.resolve("animation")

    @property
    def audio(self) -> IAudioPlayer:
        return self.resolve("audio")

    @property
    def logger(self) -> ILogger:
        return self.resolve("logger")

    def get_registered_services(self) -> list[str]:
        return list(self._services.keys())

    def get_service_info(self, service_type: str) -> dict[str, Any]:
        if service_type not in self._services:
            return {"registered": False}

        descriptor = self._services[service_type]
        return {
            "registered": True,
            "lifetime": descriptor.lifetime.name,
            "instantiated": descriptor.instance is not None,
        }


def get_container() -> ServiceContainer:
    return ServiceContainer.get_instance()


def inject(service_type: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            container = get_container()
            if service_type not in kwargs:
                kwargs[service_type] = container.resolve(service_type)
            return func(*args, **kwargs)

        return wrapper

    return decorator
