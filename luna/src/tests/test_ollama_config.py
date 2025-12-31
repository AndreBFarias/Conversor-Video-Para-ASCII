import unittest
from unittest.mock import MagicMock, patch


class TestOllamaConfigValues(unittest.TestCase):
    def test_num_ctx_in_config(self):
        import config

        assert "NUM_CTX" in config.OLLAMA_CONFIG

    def test_num_gpu_in_config(self):
        import config

        assert "NUM_GPU" in config.OLLAMA_CONFIG

    def test_keep_alive_in_config(self):
        import config

        assert "KEEP_ALIVE" in config.OLLAMA_CONFIG

    def test_timeout_in_config(self):
        import config

        assert "TIMEOUT" in config.OLLAMA_CONFIG

    def test_base_url_in_config(self):
        import config

        assert "BASE_URL" in config.OLLAMA_CONFIG

    def test_num_ctx_is_int(self):
        import config

        assert isinstance(config.OLLAMA_CONFIG["NUM_CTX"], int)

    def test_num_gpu_is_int(self):
        import config

        assert isinstance(config.OLLAMA_CONFIG["NUM_GPU"], int)

    def test_num_ctx_positive_or_default(self):
        import config

        assert config.OLLAMA_CONFIG["NUM_CTX"] > 0

    def test_num_gpu_allows_negative_one(self):
        import config

        assert config.OLLAMA_CONFIG["NUM_GPU"] >= -1


class TestSyncClientPayload(unittest.TestCase):
    @patch("requests.post")
    def test_stream_includes_num_ctx(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([b'{"response": "test", "done": true}'])
        mock_post.return_value = mock_response

        from src.core.ollama_client.sync_client import OllamaSyncClient

        client = OllamaSyncClient()
        list(client.stream("test", "dolphin-mistral"))

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "num_ctx" in payload["options"]
        assert isinstance(payload["options"]["num_ctx"], int)

    @patch("requests.post")
    def test_stream_includes_num_gpu(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([b'{"response": "test", "done": true}'])
        mock_post.return_value = mock_response

        from src.core.ollama_client.sync_client import OllamaSyncClient

        client = OllamaSyncClient()
        list(client.stream("test", "dolphin-mistral"))

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "num_gpu" in payload["options"]
        assert isinstance(payload["options"]["num_gpu"], int)

    @patch("requests.post")
    def test_stream_includes_keep_alive(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([b'{"response": "test", "done": true}'])
        mock_post.return_value = mock_response

        from src.core.ollama_client.sync_client import OllamaSyncClient

        client = OllamaSyncClient()
        list(client.stream("test", "dolphin-mistral"))

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "keep_alive" in payload

    @patch("requests.post")
    def test_stream_options_complete(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([b'{"response": "test", "done": true}'])
        mock_post.return_value = mock_response

        from src.core.ollama_client.sync_client import OllamaSyncClient

        client = OllamaSyncClient()
        list(client.stream("test", "dolphin-mistral", temperature=0.8, max_tokens=2048))

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        options = payload["options"]

        assert "temperature" in options
        assert "num_predict" in options
        assert "num_ctx" in options
        assert "num_gpu" in options


class TestOllamaModelsConfig(unittest.TestCase):
    def test_models_dict_exists(self):
        import config

        assert "MODELS" in config.OLLAMA_CONFIG

    def test_models_has_chat(self):
        import config

        assert "chat" in config.OLLAMA_CONFIG["MODELS"]

    def test_models_has_code(self):
        import config

        assert "code" in config.OLLAMA_CONFIG["MODELS"]

    def test_models_has_vision(self):
        import config

        assert "vision" in config.OLLAMA_CONFIG["MODELS"]


class TestChatLocalConfig(unittest.TestCase):
    def test_chat_local_has_model(self):
        import config

        assert "model" in config.CHAT_LOCAL

    def test_chat_local_has_fallback(self):
        import config

        assert "fallback_model" in config.CHAT_LOCAL

    def test_chat_local_has_temperature(self):
        import config

        assert "temperature" in config.CHAT_LOCAL

    def test_chat_local_has_max_tokens(self):
        import config

        assert "max_tokens" in config.CHAT_LOCAL


class TestOllamaPerformanceDefaults(unittest.TestCase):
    def test_default_context_is_large(self):
        import config

        assert config.OLLAMA_CONFIG["NUM_CTX"] >= 4096

    def test_default_gpu_is_full(self):
        import config

        assert config.OLLAMA_CONFIG["NUM_GPU"] == -1 or config.OLLAMA_CONFIG["NUM_GPU"] > 0

    def test_keep_alive_is_minutes(self):
        import config

        keep_alive = config.OLLAMA_CONFIG["KEEP_ALIVE"]
        assert "m" in keep_alive or "h" in keep_alive or keep_alive.isdigit()


if __name__ == "__main__":
    unittest.main()
