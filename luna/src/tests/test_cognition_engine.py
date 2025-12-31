from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_consciencia():
    mock = MagicMock()
    mock.active_entity_id = "luna"
    mock.llm_caller = MagicMock()
    mock.llm_caller.call.return_value = "test response"
    mock.llm_caller.has_provider.return_value = True
    mock._universal_llm = None
    mock.provider = "gemini"
    mock.model_name = "gemini-1.5-flash"
    mock.response_streamer = MagicMock()
    mock.metrics = MagicMock()
    mock.app = None
    return mock


class TestCognitionEngineInit:
    def test_creates_engine(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        assert engine._consciencia == mock_consciencia
        assert engine._system_instruction == ""
        assert engine._soul_prompt == ""

    def test_properties(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        engine._system_instruction = "test instruction"
        engine._soul_prompt = "test prompt"

        assert engine.system_instruction == "test instruction"
        assert engine.soul_prompt == "test prompt"


class TestCognitionEngineSoulPrompt:
    def test_init_soul_prompt_loads_file(self, mock_consciencia, tmp_path):
        from src.soul.consciencia.services import CognitionEngine

        entity_dir = tmp_path / "luna"
        entity_dir.mkdir(parents=True)
        alma_file = entity_dir / "alma.txt"
        alma_file.write_text("Eu sou Luna, assistente gotica.")

        with patch("src.soul.consciencia.services.cognition_engine.config") as mock_config:
            mock_config.ENTITIES_DIR = tmp_path

            engine = CognitionEngine(mock_consciencia)
            engine.init_soul_prompt()

            assert "Luna" in engine.soul_prompt
            assert engine.system_instruction == engine.soul_prompt

    def test_init_soul_prompt_fallback(self, mock_consciencia, tmp_path):
        from src.soul.consciencia.services import CognitionEngine

        with patch("src.soul.consciencia.services.cognition_engine.config") as mock_config:
            mock_config.ENTITIES_DIR = tmp_path

            engine = CognitionEngine(mock_consciencia)
            engine.init_soul_prompt()

            assert "assistente virtual" in engine.soul_prompt


class TestCognitionEnginePromptBuilder:
    def test_build_full_prompt_basic(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        engine._soul_prompt = "Voce e Luna."

        prompt = engine.build_full_prompt("Oi Luna")

        assert "Voce e Luna." in prompt
        assert "[USUARIO]" in prompt
        assert "Oi Luna" in prompt

    def test_build_full_prompt_with_memory(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        prompt = engine.build_full_prompt(
            "Qual meu nome?",
            memory_context="Usuario se chama test_user",
        )

        assert "[CONTEXTO DE MEMORIA]" in prompt
        assert "test_user" in prompt

    def test_build_full_prompt_with_visual(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        prompt = engine.build_full_prompt(
            "O que voce ve?",
            visual_context="Uma tela de computador",
        )

        assert "[VISAO ATUAL]" in prompt
        assert "tela de computador" in prompt

    def test_build_full_prompt_with_attachment(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        prompt = engine.build_full_prompt(
            "Analise isso",
            attached_content="def foo(): pass",
        )

        assert "[DOCUMENTO ANEXADO]" in prompt
        assert "def foo" in prompt


class TestCognitionEngineLLM:
    def test_call_llm(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        result = engine.call_llm("test prompt")

        assert result == "test response"
        mock_consciencia.llm_caller.call.assert_called_once_with("test prompt")

    def test_has_provider(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        assert engine.has_provider() is True

    def test_get_llm_status_no_universal(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        status = engine.get_llm_status()

        assert status["active"] == "gemini"
        assert status["model"] == "gemini-1.5-flash"

    def test_get_llm_status_with_universal(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        mock_consciencia._universal_llm = MagicMock()
        mock_consciencia._universal_llm.get_status.return_value = {"providers": ["gemini", "ollama"]}

        engine = CognitionEngine(mock_consciencia)
        status = engine.get_llm_status()

        assert "providers" in status


class TestCognitionEngineIntentRouting:
    def test_get_model_for_intent_default(self, mock_consciencia):
        from src.core.router import Intent
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        target, original = engine.get_model_for_intent(Intent.CHAT)

        assert target == original
        assert target == "gemini-1.5-flash"

    def test_get_model_for_intent_returns_original(self, mock_consciencia):
        from src.core.router import Intent
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        target, original = engine.get_model_for_intent(Intent.CODE)

        assert original == "gemini-1.5-flash"
        assert isinstance(target, str)


class TestCognitionEngineStreaming:
    def test_stream_response(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        mock_consciencia.response_streamer.stream.return_value = iter([("chunk", False, None)])

        engine = CognitionEngine(mock_consciencia)
        result = list(engine.stream_response("test"))

        assert len(result) == 1
        assert result[0][0] == "chunk"


class TestCognitionEngineFallback:
    def test_on_llm_fallback(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)
        engine.on_llm_fallback("gemini", "ollama")

        mock_consciencia.metrics.increment.assert_called_once_with("llm_fallbacks")

    def test_call_with_universal_llm_not_initialized(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        engine = CognitionEngine(mock_consciencia)

        with pytest.raises(RuntimeError, match="UniversalLLM nao inicializado"):
            engine.call_with_universal_llm("test")

    def test_call_with_universal_llm(self, mock_consciencia):
        from src.soul.consciencia.services import CognitionEngine

        mock_response = MagicMock()
        mock_response.text = "universal response"
        mock_response.fallback_used = False
        mock_consciencia._universal_llm = MagicMock()
        mock_consciencia._universal_llm.generate.return_value = mock_response

        engine = CognitionEngine(mock_consciencia)
        result = engine.call_with_universal_llm("test prompt")

        assert result == "universal response"
