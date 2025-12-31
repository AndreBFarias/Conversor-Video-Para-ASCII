import subprocess
import threading
from unittest.mock import MagicMock, patch


class TestModelStatusEnum:
    def test_values(self):
        from src.soul.model_manager import ModelStatus

        assert ModelStatus.NOT_INSTALLED.value == "not_installed"
        assert ModelStatus.DOWNLOADING.value == "downloading"
        assert ModelStatus.INSTALLED.value == "installed"
        assert ModelStatus.ERROR.value == "error"


class TestModelInfoDataclass:
    def test_fields(self):
        from src.soul.model_manager import ModelInfo, ModelStatus

        info = ModelInfo(name="test-model", size="1GB", description="Test model", category="chat")

        assert info.name == "test-model"
        assert info.size == "1GB"
        assert info.description == "Test model"
        assert info.category == "chat"
        assert info.status == ModelStatus.NOT_INSTALLED

    def test_custom_status(self):
        from src.soul.model_manager import ModelInfo, ModelStatus

        info = ModelInfo(name="test", size="1GB", description="Test", category="vision", status=ModelStatus.INSTALLED)

        assert info.status == ModelStatus.INSTALLED


class TestAvailableModels:
    def test_chat_models_exist(self):
        from src.soul.model_manager import AVAILABLE_MODELS

        assert "chat" in AVAILABLE_MODELS
        assert len(AVAILABLE_MODELS["chat"]) > 0

    def test_vision_models_exist(self):
        from src.soul.model_manager import AVAILABLE_MODELS

        assert "vision" in AVAILABLE_MODELS
        assert len(AVAILABLE_MODELS["vision"]) > 0


class TestModelManagerInit:
    def test_creates_instance(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nmodel1\nmodel2")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            assert manager._installed_models is not None
            assert isinstance(manager._downloading, dict)
            assert isinstance(manager._lock, type(threading.Lock()))


class TestModelManagerRefreshInstalled:
    def test_parses_ollama_list(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3:latest\nmistral:7b")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            result = manager.refresh_installed()

            assert "llama3" in result or "llama3:latest" in result

    def test_handles_ollama_not_found(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ollama not found")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            assert manager._installed_models == []

    def test_handles_timeout(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ollama", 10)

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            assert manager._installed_models == []


class TestModelManagerIsInstalled:
    def test_exact_match(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3:latest")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            manager._installed_models = ["llama3:latest", "llama3"]

            assert manager.is_installed("llama3:latest") is True

    def test_base_name_match(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3:latest")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            manager._installed_models = ["llama3:latest"]

            assert manager.is_installed("llama3") is True

    def test_not_installed(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3:latest")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            manager._installed_models = ["llama3:latest"]

            assert manager.is_installed("mistral") is False


class TestModelManagerIsDownloading:
    def test_returns_true_when_downloading(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            manager._downloading["test-model"] = MagicMock()

            assert manager.is_downloading("test-model") is True

    def test_returns_false_when_not_downloading(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            assert manager.is_downloading("test-model") is False


class TestModelManagerGetModelStatus:
    def test_returns_downloading(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager, ModelStatus

            manager = ModelManager()
            manager._downloading["test"] = MagicMock()

            assert manager.get_model_status("test") == ModelStatus.DOWNLOADING

    def test_returns_installed(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\ntest:latest")

            from src.soul.model_manager import ModelManager, ModelStatus

            manager = ModelManager()

            assert manager.get_model_status("test") == ModelStatus.INSTALLED

    def test_returns_not_installed(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager, ModelStatus

            manager = ModelManager()

            assert manager.get_model_status("unknown") == ModelStatus.NOT_INSTALLED


class TestModelManagerDownloadModel:
    def test_returns_true_if_already_installed(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME\ntest:latest")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            callback = MagicMock()

            result = manager.download_model("test", on_complete=callback)

            assert result is True
            callback.assert_called_once()

    def test_returns_false_if_already_downloading(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()
            manager._downloading["test"] = MagicMock()

            result = manager.download_model("test")

            assert result is False


class TestModelManagerDeleteModel:
    def test_successful_deletion(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            mock_run.return_value = MagicMock(returncode=0)
            result = manager.delete_model("test")

            assert result is True

    def test_failed_deletion(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            result = manager.delete_model("nonexistent")

            assert result is False


class TestModelManagerGetAvailableModels:
    def test_returns_all_models(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            result = manager.get_available_models()

            assert len(result) > 0

    def test_filters_by_category(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            result = manager.get_available_models(category="vision")

            assert all(m.category == "vision" for m in result)


class TestModelManagerCheckOllamaRunning:
    def test_returns_true_when_running(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            mock_run.return_value = MagicMock(returncode=0)
            result = manager.check_ollama_running()

            assert result is True

    def test_returns_false_when_not_running(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            from src.soul.model_manager import ModelManager

            manager = ModelManager()

            mock_run.side_effect = Exception("Not running")
            result = manager.check_ollama_running()

            assert result is False


class TestGetModelManagerSingleton:
    def test_returns_singleton(self):
        with patch("src.soul.model_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="NAME")

            import src.soul.model_manager as module

            module._manager_instance = None

            from src.soul.model_manager import get_model_manager

            m1 = get_model_manager()
            m2 = get_model_manager()

            assert m1 is m2
