from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def reset_container():
    from src.core.di import ServiceContainer

    ServiceContainer.reset()
    yield
    ServiceContainer.reset()


class MockConsciencia:
    def __init__(self, app=None):
        self.app = app
        self.conversation_history = []

    def processar(self, user_input, **kwargs):
        return {"response": f"Mock: {user_input}"}

    def stream_processar(self, user_input, **kwargs):
        yield {"chunk": "mock"}


class MockBoca:
    def __init__(self):
        self._is_speaking = False

    def falar(self, texto):
        pass

    def parar(self):
        pass

    @property
    def is_speaking(self):
        return self._is_speaking


class MockVisao:
    def __init__(self):
        self._is_available = True

    def olhar(self):
        return "Mock visual context"

    def analisar_imagem(self, image_path):
        return "Mock image analysis"

    @property
    def is_available(self):
        return self._is_available


class MockOuvido:
    def __init__(self):
        self._is_listening = False

    def ouvir(self):
        return None

    def iniciar(self):
        self._is_listening = True

    def parar(self):
        self._is_listening = False

    @property
    def is_listening(self):
        return self._is_listening


class TestTemploDaAlmaWithContainer:
    def test_init_with_container(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        from src.app import TemploDaAlma

        app = TemploDaAlma(container=container)

        assert app._container is container
        assert hasattr(app, "consciencia")
        assert hasattr(app, "boca")
        assert hasattr(app, "visao")

    def test_factories_are_used_from_container(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        from src.app import TemploDaAlma

        app = TemploDaAlma(container=container)

        consciencia_factory = container.resolve("consciencia_factory")
        assert consciencia_factory is not None
        assert callable(consciencia_factory)


class TestTemploDaAlmaDirectInjection:
    def test_inject_mock_consciencia(self):
        from src.app import TemploDaAlma

        mock_consciencia = MockConsciencia()

        app = TemploDaAlma(consciencia=mock_consciencia)

        assert app.consciencia is mock_consciencia
        assert isinstance(app.consciencia, MockConsciencia)

    def test_inject_mock_boca(self):
        from src.app import TemploDaAlma

        mock_boca = MockBoca()

        app = TemploDaAlma(boca=mock_boca)

        assert app.boca is mock_boca
        assert isinstance(app.boca, MockBoca)

    def test_inject_mock_visao(self):
        from src.app import TemploDaAlma

        mock_visao = MockVisao()

        app = TemploDaAlma(visao=mock_visao)

        assert app.visao is mock_visao
        assert isinstance(app.visao, MockVisao)

    def test_inject_mock_ouvido(self):
        from src.app import TemploDaAlma

        mock_ouvido = MockOuvido()

        app = TemploDaAlma(ouvido=mock_ouvido)

        assert app.ouvido is mock_ouvido
        assert isinstance(app.ouvido, MockOuvido)

    def test_inject_all_mocks(self):
        from src.app import TemploDaAlma

        mock_consciencia = MockConsciencia()
        mock_boca = MockBoca()
        mock_visao = MockVisao()
        mock_ouvido = MockOuvido()

        app = TemploDaAlma(
            consciencia=mock_consciencia,
            boca=mock_boca,
            visao=mock_visao,
            ouvido=mock_ouvido,
        )

        assert app.consciencia is mock_consciencia
        assert app.boca is mock_boca
        assert app.visao is mock_visao
        assert app.ouvido is mock_ouvido


class TestTemploDaAlmaBackwardCompatibility:
    def test_init_without_container(self):
        from src.app import TemploDaAlma

        app = TemploDaAlma()

        assert app._container is None
        assert hasattr(app, "consciencia")
        assert hasattr(app, "boca")
        assert hasattr(app, "visao")

    def test_components_are_real_without_injection(self):
        from src.app import TemploDaAlma
        from src.soul import Boca, Consciencia, Visao

        app = TemploDaAlma()

        assert isinstance(app.consciencia, Consciencia)
        assert isinstance(app.boca, Boca)
        assert isinstance(app.visao, Visao)


class TestContainerFactoryOverride:
    def test_override_consciencia_factory(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        container.override("consciencia_factory", lambda c: lambda app: MockConsciencia(app))

        from src.app import TemploDaAlma

        app = TemploDaAlma(container=container)

        assert isinstance(app.consciencia, MockConsciencia)

    def test_override_boca_factory(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        container.override("boca_factory", lambda c: lambda: MockBoca())

        from src.app import TemploDaAlma

        app = TemploDaAlma(container=container)

        assert isinstance(app.boca, MockBoca)

    def test_override_multiple_factories(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        container.override("consciencia_factory", lambda c: lambda app: MockConsciencia(app))
        container.override("boca_factory", lambda c: lambda: MockBoca())
        container.override("visao_factory", lambda c: lambda: MockVisao())

        from src.app import TemploDaAlma

        app = TemploDaAlma(container=container)

        assert isinstance(app.consciencia, MockConsciencia)
        assert isinstance(app.boca, MockBoca)
        assert isinstance(app.visao, MockVisao)


class TestContainerPropertyAccessors:
    def test_config_accessor(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        config = container.config
        assert config is not None
        assert hasattr(config, "get")

    def test_memory_accessor(self):
        from src.core.di import ServiceContainer, register_default_services

        container = ServiceContainer.get_instance()
        register_default_services(container)

        memory = container.memory
        assert memory is not None
        assert hasattr(memory, "add")
        assert hasattr(memory, "retrieve")


class TestNewProtocols:
    def test_iconsciencia_protocol(self):
        from src.core.di import IConsciencia

        mock = MockConsciencia()
        assert hasattr(mock, "processar")
        assert hasattr(mock, "stream_processar")
        assert hasattr(mock, "conversation_history")

    def test_iboca_protocol(self):
        from src.core.di import IBoca

        mock = MockBoca()
        assert hasattr(mock, "falar")
        assert hasattr(mock, "parar")
        assert hasattr(mock, "is_speaking")

    def test_ivisao_protocol(self):
        from src.core.di import IVisao

        mock = MockVisao()
        assert hasattr(mock, "olhar")
        assert hasattr(mock, "analisar_imagem")
        assert hasattr(mock, "is_available")

    def test_iouvido_protocol(self):
        from src.core.di import IOuvido

        mock = MockOuvido()
        assert hasattr(mock, "ouvir")
        assert hasattr(mock, "iniciar")
        assert hasattr(mock, "parar")
        assert hasattr(mock, "is_listening")
