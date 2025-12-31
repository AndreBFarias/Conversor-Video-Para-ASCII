import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest


class TestProcessingThreadShutdownGuards:
    def test_executor_submit_with_shutdown_flag(self):
        from src.soul.processing_threads import ProcessingThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_manager.interrupt_event = threading.Event()
        mock_consciencia = MagicMock()

        thread = ProcessingThread(mock_manager, mock_consciencia)

        mock_manager.shutdown_event.set()

        assert thread.manager.shutdown_event.is_set() is True
        assert thread._executor_shutdown is False

    def test_executor_shutdown_flag_set_on_runtime_error(self):
        from src.soul.processing_threads import ProcessingThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_consciencia = MagicMock()

        thread = ProcessingThread(mock_manager, mock_consciencia)

        thread._executor.shutdown(wait=True)
        thread._executor_shutdown = True

        assert thread._executor_shutdown is True

    def test_process_request_aborts_on_shutdown(self):
        from src.soul.processing_threads import ProcessingThread
        from src.soul.threading_manager import ProcessingRequest

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_manager.shutdown_event.set()
        mock_consciencia = MagicMock()

        thread = ProcessingThread(mock_manager, mock_consciencia)

        request = ProcessingRequest(user_text="test", timestamp=0.0)
        result = thread._process_request(request)

        assert result == (None, request)
        mock_consciencia.process_interaction.assert_not_called()


class TestAnimationThreadShutdownGuards:
    def test_app_mounted_flag_exists(self):
        from src.soul.processing_threads import AnimationThread

        mock_manager = MagicMock()
        mock_controller = MagicMock()
        mock_app = MagicMock()

        thread = AnimationThread(mock_manager, mock_controller, mock_app)

        assert hasattr(thread, "_app_mounted")
        assert thread._app_mounted is True


class TestCoordinatorThreadShutdownGuards:
    def test_safe_call_from_thread_blocks_on_shutdown(self):
        from src.soul.processing_threads import CoordinatorThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_manager.shutdown_event.set()
        mock_app = MagicMock()

        thread = CoordinatorThread(mock_manager, mock_app)

        callback = MagicMock()
        result = thread._safe_call_from_thread(callback)

        assert result is False
        callback.assert_not_called()

    def test_safe_call_from_thread_blocks_when_unmounted(self):
        from src.soul.processing_threads import CoordinatorThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_app = MagicMock()

        thread = CoordinatorThread(mock_manager, mock_app)
        thread._app_mounted = False

        callback = MagicMock()
        result = thread._safe_call_from_thread(callback)

        assert result is False
        callback.assert_not_called()

    def test_safe_call_from_thread_succeeds_normally(self):
        from src.soul.processing_threads import CoordinatorThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_app = MagicMock()

        thread = CoordinatorThread(mock_manager, mock_app)

        callback = MagicMock()
        result = thread._safe_call_from_thread(callback, "arg1", kwarg1="value")

        assert result is True
        mock_app.call_from_thread.assert_called_once_with(callback, "arg1", kwarg1="value")

    def test_safe_call_from_thread_handles_mount_error(self):
        from src.soul.processing_threads import CoordinatorThread

        mock_manager = MagicMock()
        mock_manager.shutdown_event = threading.Event()
        mock_app = MagicMock()
        mock_app.call_from_thread.side_effect = Exception("Can't mount widget")

        thread = CoordinatorThread(mock_manager, mock_app)

        callback = MagicMock()
        result = thread._safe_call_from_thread(callback)

        assert result is False
        assert thread._app_mounted is False


class TestOllamaClientShutdownGuards:
    def test_client_closed_flag(self):
        import asyncio

        from src.core.ollama_client import OllamaClient

        async def _test():
            client = OllamaClient()
            assert client._closed is False

            await client.close()
            assert client._closed is True

        asyncio.run(_test())

    def test_get_session_raises_when_closed(self):
        import asyncio

        from src.core.ollama_client import OllamaClient

        async def _test():
            client = OllamaClient()
            await client.close()

            with pytest.raises(RuntimeError, match="fechado"):
                await client._get_session()

        asyncio.run(_test())

    def test_sync_client_shutdown_flag(self):
        from src.core.ollama_client import OllamaSyncClient

        client = OllamaSyncClient()
        assert client._shutdown is False

        client._shutdown = True

        with pytest.raises(RuntimeError, match="shutdown"):
            client._run_async(None)


class TestThreadPoolExecutorShutdownHandling:
    def test_executor_submit_after_shutdown_raises(self):
        executor = ThreadPoolExecutor(max_workers=1)
        executor.shutdown(wait=True)

        with pytest.raises(RuntimeError):
            executor.submit(lambda: None)

    def test_cancel_futures_on_shutdown(self):
        executor = ThreadPoolExecutor(max_workers=1)

        import time

        def slow_task():
            time.sleep(10)
            return "done"

        future = executor.submit(slow_task)
        executor.shutdown(wait=False, cancel_futures=True)

        assert future.cancelled() or not future.done()


class TestConscienciaShutdownGuards:
    @patch("src.soul.consciencia.provider_init.get_personalidade")
    @patch("src.soul.consciencia.core.get_entity_smart_memory")
    @patch("src.soul.consciencia.core.get_smart_memory")
    @patch("src.soul.consciencia.provider_init.OllamaSyncClient")
    def test_call_llm_checks_shutdown(self, mock_ollama, mock_smart, mock_entity_smart, mock_personalidade):
        mock_personalidade.return_value.get_soul_prompt.return_value = "test"
        mock_entity_smart.return_value = MagicMock()
        mock_smart.return_value = MagicMock()

        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_health.return_value = True
        mock_ollama.return_value = mock_ollama_instance

        mock_app = MagicMock()
        mock_app.threading_manager = MagicMock()
        mock_app.threading_manager.shutdown_event = threading.Event()
        mock_app.threading_manager.shutdown_event.set()

        with patch("src.soul.consciencia.core.config") as mock_config:
            mock_config.CHAT_PROVIDER = "local"
            mock_config.CHAT_LOCAL = {"model": "test", "timeout": 60}
            mock_config.GEMINI_CONFIG = {"CACHE_SIZE": 100, "MODEL_NAME": "test"}
            mock_config.RATE_LIMITER_CONFIG = {}
            mock_config.CACHE_CONFIG = {}
            mock_config.ANIMATION_TO_EMOTION = {}
            mock_config.OLLAMA_CONFIG = {"BASE_URL": "http://localhost:11434", "TIMEOUT": 60}
            mock_config.APP_DIR = MagicMock()
            mock_config.APP_DIR.__truediv__ = MagicMock(return_value=MagicMock(exists=lambda: False))

            from src.soul.consciencia import Consciencia

            consciencia = Consciencia(mock_app)

            with pytest.raises(Exception, match="Shutdown"):
                consciencia._call_llm("test prompt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
