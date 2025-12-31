from __future__ import annotations

import pytest


class MockConsciencia:
    def __init__(self):
        self._history = []

    def processar(self, user_input, **kwargs):
        return {"response": f"Processed: {user_input}"}

    def stream_processar(self, user_input, **kwargs):
        yield {"chunk": "test"}

    @property
    def conversation_history(self):
        return self._history


class MockBoca:
    def __init__(self):
        self._is_speaking = False

    def falar(self, texto):
        self._is_speaking = True

    def parar(self):
        self._is_speaking = False

    @property
    def is_speaking(self):
        return self._is_speaking


class MockVisao:
    def __init__(self):
        self._is_available = True

    def olhar(self):
        return "visual context"

    def analisar_imagem(self, image_path):
        return "image analysis"

    @property
    def is_available(self):
        return self._is_available


class MockOuvido:
    def __init__(self):
        self._is_listening = False

    def ouvir(self):
        return "transcribed text"

    def iniciar(self):
        self._is_listening = True

    def parar(self):
        self._is_listening = False

    @property
    def is_listening(self):
        return self._is_listening


class MockSessionManager:
    def __init__(self):
        self._session_id = None
        self._history = []

    def new_session(self):
        self._session_id = "test-session-123"
        return self._session_id

    def load_session(self, session_id):
        self._session_id = session_id
        return True

    def save_session(self):
        pass

    @property
    def current_session_id(self):
        return self._session_id

    @property
    def conversation_history(self):
        return self._history


class TestIConsciencia:
    def test_processar(self):
        mock = MockConsciencia()
        result = mock.processar("test input")
        assert "response" in result
        assert result["response"] == "Processed: test input"

    def test_stream_processar(self):
        mock = MockConsciencia()
        chunks = list(mock.stream_processar("test input"))
        assert len(chunks) > 0
        assert "chunk" in chunks[0]

    def test_conversation_history(self):
        mock = MockConsciencia()
        assert mock.conversation_history == []


class TestIBoca:
    def test_falar(self):
        mock = MockBoca()
        assert mock.is_speaking is False
        mock.falar("hello")
        assert mock.is_speaking is True

    def test_parar(self):
        mock = MockBoca()
        mock.falar("hello")
        mock.parar()
        assert mock.is_speaking is False


class TestIVisao:
    def test_olhar(self):
        mock = MockVisao()
        result = mock.olhar()
        assert result == "visual context"

    def test_analisar_imagem(self):
        mock = MockVisao()
        result = mock.analisar_imagem("/path/to/image.jpg")
        assert result == "image analysis"

    def test_is_available(self):
        mock = MockVisao()
        assert mock.is_available is True


class TestIOuvido:
    def test_ouvir(self):
        mock = MockOuvido()
        result = mock.ouvir()
        assert result == "transcribed text"

    def test_iniciar_parar(self):
        mock = MockOuvido()
        assert mock.is_listening is False
        mock.iniciar()
        assert mock.is_listening is True
        mock.parar()
        assert mock.is_listening is False


class TestISessionManager:
    def test_new_session(self):
        mock = MockSessionManager()
        session_id = mock.new_session()
        assert session_id == "test-session-123"
        assert mock.current_session_id == session_id

    def test_load_session(self):
        mock = MockSessionManager()
        result = mock.load_session("session-456")
        assert result is True
        assert mock.current_session_id == "session-456"

    def test_save_session(self):
        mock = MockSessionManager()
        mock.new_session()
        mock.save_session()
        assert mock.current_session_id is not None

    def test_conversation_history(self):
        mock = MockSessionManager()
        assert mock.conversation_history == []


class TestProtocolRuntimeCheckable:
    def test_iconsciencia_is_runtime_checkable(self):
        from src.core.di import IConsciencia

        mock = MockConsciencia()
        assert isinstance(mock, IConsciencia)

    def test_iboca_is_runtime_checkable(self):
        from src.core.di import IBoca

        mock = MockBoca()
        assert isinstance(mock, IBoca)

    def test_ivisao_is_runtime_checkable(self):
        from src.core.di import IVisao

        mock = MockVisao()
        assert isinstance(mock, IVisao)

    def test_iouvido_is_runtime_checkable(self):
        from src.core.di import IOuvido

        mock = MockOuvido()
        assert isinstance(mock, IOuvido)

    def test_isessionmanager_is_runtime_checkable(self):
        from src.core.di import ISessionManager

        mock = MockSessionManager()
        assert isinstance(mock, ISessionManager)
