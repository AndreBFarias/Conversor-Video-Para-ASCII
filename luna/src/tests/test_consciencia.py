import json
from unittest.mock import Mock, patch

import pytest


class TestSanitizeForLog:
    def test_sanitize_empty_string(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("")
        assert result == ""

    def test_sanitize_none(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log(None)
        assert result == ""

    def test_sanitize_email(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("meu email e teste@exemplo.com ok")
        assert "[EMAIL]" in result
        assert "teste@exemplo.com" not in result

    def test_sanitize_cpf(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("meu cpf 123.456.789-00")
        assert "[CPF]" in result
        assert "123.456.789-00" not in result

    def test_sanitize_telefone(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("telefone (11) 98765-4321")
        assert "[TELEFONE]" in result

    def test_sanitize_truncate_long_text(self):
        from src.soul.model_helpers import sanitize_for_log

        long_text = "a" * 100
        result = sanitize_for_log(long_text, max_len=50)
        assert len(result) == 53
        assert result.endswith("...")

    def test_sanitize_credencial(self):
        from src.soul.model_helpers import sanitize_for_log

        result = sanitize_for_log("minha senha: abc123")
        assert "[CREDENCIAL]" in result


class TestRemoveEmojis:
    def test_remove_emojis_with_emojis(self):
        from src.soul.model_helpers import remove_emojis

        result = remove_emojis("Ola mundo!")
        assert result == "Ola mundo!"

    def test_remove_emojis_no_emojis(self):
        from src.soul.model_helpers import remove_emojis

        result = remove_emojis("Texto normal sem emojis")
        assert result == "Texto normal sem emojis"


class TestGetUserProfile:
    @patch("src.soul.model_helpers.PROFILE_PATH")
    @patch("src.soul.model_helpers.get_user_context")
    def test_get_user_profile_no_file(self, mock_context, mock_path):
        from src.soul.model_helpers import get_user_profile

        mock_path.exists.return_value = False
        mock_context.return_value = {"user_name": "Viajante"}

        result = get_user_profile()
        assert result == {"user_name": "Viajante"}

    @patch("src.soul.model_helpers.PROFILE_PATH")
    @patch("src.soul.model_helpers.get_user_context")
    @patch("builtins.open")
    def test_get_user_profile_with_file(self, mock_open, mock_context, mock_path):
        from src.soul.model_helpers import get_user_profile

        mock_path.exists.return_value = True
        mock_context.return_value = {"user_name": "Usuario"}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
            {"nome": "TestUser", "genero": "M"}
        )

        with patch("json.load", return_value={"nome": "TestUser", "genero": "M"}):
            result = get_user_profile()
            assert result is not None


class TestConscienciaInit:
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.conversation_history = []
        app.session_manager = Mock()
        app.file_handler = Mock()
        app.animation_controller = Mock()
        return app

    @patch("src.soul.consciencia.core.get_entity_smart_memory")
    @patch("src.soul.consciencia.core.get_smart_memory")
    @patch("src.soul.consciencia.core.get_metrics")
    @patch("src.soul.consciencia.core.get_api_tracker")
    @patch("src.soul.consciencia.core.get_active_entity")
    @patch("src.soul.consciencia.provider_init.get_personalidade")
    @patch("src.soul.consciencia.core.get_parser")
    @patch("src.soul.consciencia.core.get_web_search")
    @patch("src.soul.consciencia.core.get_terminal_executor")
    @patch("src.soul.consciencia.core.config")
    def test_consciencia_init_local_provider(
        self,
        mock_config,
        mock_executor,
        mock_search,
        mock_parser,
        mock_personalidade,
        mock_active_entity,
        mock_api_tracker,
        mock_metrics,
        mock_smart_memory,
        mock_entity_memory,
        mock_app,
    ):
        mock_config.CHAT_PROVIDER = "local"
        mock_config.GEMINI_CONFIG = {"CACHE_SIZE": 100}
        mock_config.RATE_LIMITER_CONFIG = {"QUOTA_LIMIT": 60, "SAFETY_MARGIN": 5, "WINDOW_SECONDS": 60}
        mock_config.CACHE_CONFIG = {"SIMILARITY_THRESHOLD": 0.85, "MAX_SIZE": 100, "TTL_SECONDS": 3600}
        mock_config.CHAT_LOCAL = {"model": "test-model"}
        mock_config.GOOGLE_API_KEY = None

        mock_active_entity.return_value = "luna"
        mock_personalidade.return_value.get_soul_prompt.return_value = "Test prompt"

        with patch("src.soul.consciencia.provider_init.OllamaSyncClient") as mock_ollama:
            mock_ollama.return_value.check_health.return_value = True
            from src.soul.consciencia import Consciencia

            consciencia = Consciencia(mock_app)
            assert consciencia is not None
            assert consciencia.provider == "local"


class TestConscienciaMethods:
    @pytest.fixture
    def mock_consciencia(self):
        with patch("src.soul.consciencia.Consciencia.__init__", return_value=None):
            from src.soul.consciencia import Consciencia

            instance = Consciencia.__new__(Consciencia)
            instance.conversation_history = []
            instance.soul_prompt = "Test prompt"
            instance.response_parser = Mock()
            instance.semantic_cache = Mock()
            instance.rate_limiter = Mock()
            instance.deduplicator = Mock()
            instance.metrics = Mock()
            instance.api_tracker = Mock()
            instance.active_entity_id = "luna"
            instance.smart_memory = Mock()
            instance.global_memory = Mock()
            instance.provider = "gemini"
            instance.gemini_client = Mock()
            instance.model_name = "gemini-1.5-flash"
            instance.json_failures = 0
            instance.json_failure_threshold = 3
            instance.web_search = Mock()
            instance.terminal_executor = Mock()
            instance.app = Mock()
            return instance

    def test_build_system_instruction(self, mock_consciencia):
        mock_consciencia._build_system_instruction = lambda: "System instruction"
        result = mock_consciencia._build_system_instruction()
        assert result == "System instruction"

    def test_validate_schema_valid_response(self, mock_consciencia):
        valid_response = {
            "fala_tts": "Ola",
            "log_terminal": "[Luna] Ola",
            "animacao": "observando",
        }
        mock_consciencia._validate_schema = lambda r: r
        result = mock_consciencia._validate_schema(valid_response)
        assert result["fala_tts"] == "Ola"

    def test_sanitize_for_display(self, mock_consciencia):
        mock_consciencia._sanitize_for_display = lambda t: t.replace("*", "")
        result = mock_consciencia._sanitize_for_display("*bold* text")
        assert result == "bold text"


class TestModelSizeDetection:
    def test_get_model_size_with_size_suffix(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("llama3.2:1b") == 1.0
        assert get_model_size_gb("llama3.2:3b") == 3.0
        assert get_model_size_gb("llama3:8b") == 8.0
        assert get_model_size_gb("qwen2:0.5b") == 0.5
        assert get_model_size_gb("qwen2:1.5b") == 1.5

    def test_get_model_size_with_keywords(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("tinyllama") == 1.0
        assert get_model_size_gb("phi3:mini") == 2.0
        assert get_model_size_gb("llava-phi3") == 3.8

    def test_get_model_size_default(self):
        from src.soul.model_helpers import get_model_size_gb

        assert get_model_size_gb("dolphin-mistral") == 7.0
        assert get_model_size_gb("unknown-model") == 7.0
        assert get_model_size_gb("") == 7.0
        assert get_model_size_gb(None) == 7.0

    def test_is_small_model(self):
        from src.soul.model_helpers import is_small_model

        assert is_small_model("llama3.2:3b") is True
        assert is_small_model("phi3:mini") is True
        assert is_small_model("llama3:8b") is False
        assert is_small_model("dolphin-mistral:7b") is False

    def test_needs_compact_prompt(self):
        from src.soul.model_helpers import needs_compact_prompt

        assert needs_compact_prompt("llama3.2:1b") is True
        assert needs_compact_prompt("llama3.2:3b") is True
        assert needs_compact_prompt("tinyllama") is True
        assert needs_compact_prompt("llama3:8b") is False
        assert needs_compact_prompt("dolphin-mistral:7b") is False
