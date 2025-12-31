from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_container():
    from src.core.di import ServiceContainer

    ServiceContainer.reset()
    yield
    ServiceContainer.reset()


class TestServiceLifetime:
    def test_singleton_lifetime(self):
        from src.core.di import ServiceLifetime

        assert ServiceLifetime.SINGLETON.name == "SINGLETON"
        assert ServiceLifetime.TRANSIENT.name == "TRANSIENT"
        assert ServiceLifetime.SCOPED.name == "SCOPED"


class TestServiceContainer:
    def test_get_instance_returns_same_instance(self):
        from src.core.di import ServiceContainer

        container1 = ServiceContainer.get_instance()
        container2 = ServiceContainer.get_instance()

        assert container1 is container2

    def test_reset_clears_instance(self):
        from src.core.di import ServiceContainer

        container1 = ServiceContainer.get_instance()
        ServiceContainer.reset()
        container2 = ServiceContainer.get_instance()

        assert container1 is not container2

    def test_register_service(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        container.register("test_service", lambda c: "test_value")

        assert container.is_registered("test_service")
        assert container.resolve("test_service") == "test_value"

    def test_register_instance(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()
        instance = {"key": "value"}

        container.register_instance("my_instance", instance)

        resolved = container.resolve("my_instance")
        assert resolved is instance
        assert resolved["key"] == "value"

    def test_singleton_returns_same_instance(self):
        from src.core.di import ServiceContainer, ServiceLifetime

        container = ServiceContainer.get_instance()
        call_count = [0]

        def factory(c):
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register("singleton_svc", factory, ServiceLifetime.SINGLETON)

        result1 = container.resolve("singleton_svc")
        result2 = container.resolve("singleton_svc")

        assert result1 is result2
        assert call_count[0] == 1

    def test_transient_returns_new_instance(self):
        from src.core.di import ServiceContainer, ServiceLifetime

        container = ServiceContainer.get_instance()
        call_count = [0]

        def factory(c):
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register("transient_svc", factory, ServiceLifetime.TRANSIENT)

        result1 = container.resolve("transient_svc")
        result2 = container.resolve("transient_svc")

        assert result1 is not result2
        assert call_count[0] == 2

    def test_resolve_unregistered_raises(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        with pytest.raises(KeyError, match="not registered"):
            container.resolve("unknown_service")

    def test_try_resolve_returns_none_for_unknown(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        result = container.try_resolve("unknown_service")

        assert result is None

    def test_override_replaces_service(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        container.register("svc", lambda c: "original")
        assert container.resolve("svc") == "original"

        container.override("svc", lambda c: "overridden")
        assert container.resolve("svc") == "overridden"

    def test_override_instance(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        container.register("svc", lambda c: "original")
        container.override_instance("svc", "direct_instance")

        assert container.resolve("svc") == "direct_instance"

    def test_get_registered_services(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        container.register("svc1", lambda c: 1)
        container.register("svc2", lambda c: 2)

        services = container.get_registered_services()

        assert "svc1" in services
        assert "svc2" in services

    def test_get_service_info(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        container.register("svc", lambda c: "value")

        info_before = container.get_service_info("svc")
        assert info_before["registered"] is True
        assert info_before["instantiated"] is False

        container.resolve("svc")

        info_after = container.get_service_info("svc")
        assert info_after["instantiated"] is True

    def test_service_info_unregistered(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()

        info = container.get_service_info("unknown")
        assert info["registered"] is False


class TestGetContainer:
    def test_get_container_returns_singleton(self):
        from src.core.di import ServiceContainer, get_container

        container1 = get_container()
        container2 = ServiceContainer.get_instance()

        assert container1 is container2


class TestScopedServices:
    def test_scoped_returns_same_in_scope(self):
        from src.core.di import ServiceContainer, ServiceLifetime

        container = ServiceContainer.get_instance()
        call_count = [0]

        def factory(c):
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register("scoped_svc", factory, ServiceLifetime.SCOPED)

        result1 = container.resolve("scoped_svc")
        result2 = container.resolve("scoped_svc")

        assert result1 is result2
        assert call_count[0] == 1

    def test_clear_scoped_resets_instances(self):
        from src.core.di import ServiceContainer, ServiceLifetime

        container = ServiceContainer.get_instance()
        call_count = [0]

        def factory(c):
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register("scoped_svc", factory, ServiceLifetime.SCOPED)

        result1 = container.resolve("scoped_svc")
        container.clear_scoped()
        result2 = container.resolve("scoped_svc")

        assert result1 is not result2
        assert call_count[0] == 2


class TestInjectDecorator:
    def test_inject_decorator(self):
        from src.core.di import ServiceContainer, inject

        container = ServiceContainer.get_instance()
        container.register("config", lambda c: {"debug": True})

        @inject("config")
        def get_debug_mode(config=None):
            return config["debug"]

        result = get_debug_mode()
        assert result is True

    def test_inject_can_be_overridden(self):
        from src.core.di import ServiceContainer, inject

        container = ServiceContainer.get_instance()
        container.register("config", lambda c: {"debug": True})

        @inject("config")
        def get_debug_mode(config=None):
            return config["debug"]

        result = get_debug_mode(config={"debug": False})
        assert result is False


class TestPropertyAccessors:
    def test_config_property(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()
        mock_config = {"key": "value"}
        container.register_instance("config", mock_config)

        assert container.config is mock_config

    def test_memory_property(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()
        mock_memory = {"stored": "data"}
        container.register_instance("memory", mock_memory)

        assert container.memory is mock_memory

    def test_llm_property(self):
        from src.core.di import ServiceContainer

        container = ServiceContainer.get_instance()
        mock_llm = {"model": "test"}
        container.register_instance("llm", mock_llm)

        assert container.llm is mock_llm


class TestServiceDescriptor:
    def test_descriptor_fields(self):
        from src.core.di import ServiceDescriptor, ServiceLifetime

        factory = lambda c: "value"
        descriptor = ServiceDescriptor(factory, ServiceLifetime.SINGLETON)

        assert descriptor.factory is factory
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.instance is None

    def test_descriptor_instance_can_be_set(self):
        from src.core.di import ServiceDescriptor

        descriptor = ServiceDescriptor(lambda c: "new")
        descriptor.instance = "cached"

        assert descriptor.instance == "cached"
