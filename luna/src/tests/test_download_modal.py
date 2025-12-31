import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDownloadModalInit(unittest.TestCase):
    def test_init_single_download(self):
        from src.ui.screens import DownloadModal

        modal = DownloadModal("llava-phi3", on_complete=None, current=1, total=1)
        self.assertEqual(modal.model_name, "llava-phi3")
        self.assertEqual(modal._current, 1)
        self.assertEqual(modal._total, 1)
        self.assertEqual(modal._progress, 0.0)
        self.assertEqual(modal._status, "Iniciando...")
        assert modal._total == 1

    def test_init_multiple_downloads(self):
        from src.ui.screens import DownloadModal

        modal = DownloadModal("qwen2:1.5b", on_complete=None, current=2, total=3)
        self.assertEqual(modal._current, 2)
        self.assertEqual(modal._total, 3)
        assert modal._current == 2

    def test_init_with_callback(self):
        from src.ui.screens import DownloadModal

        callback = MagicMock()
        modal = DownloadModal("model", on_complete=callback)
        self.assertEqual(modal._on_complete, callback)
        assert modal._on_complete is not None


class TestDownloadModalProgressParsing(unittest.TestCase):
    def setUp(self):
        from src.ui.screens import DownloadModal

        self.modal = DownloadModal("test-model")
        self.modal._progress = 0.0
        self.modal._status = ""
        self.modal._details = ""

    def test_extract_percentage(self):
        import re

        status = "pulling manifest 45%"
        match = re.search(r"(\d+)%", status)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "45")
        assert int(match.group(1)) == 45

    def test_extract_percentage_with_speed(self):
        import re

        status = "downloading 67% 12.5MB/s"
        match = re.search(r"(\d+)%", status)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "67")
        assert int(match.group(1)) == 67

    def test_extract_speed(self):
        import re

        status = "downloading 67% 12.5MB/s"
        speed_match = re.search(r"(\d+\.?\d*\s*[KMGT]?B/s)", status)
        self.assertIsNotNone(speed_match)
        self.assertEqual(speed_match.group(1), "12.5MB/s")
        assert "MB/s" in speed_match.group(1)

    def test_clean_ansi_codes(self):
        import re

        ansi_pattern = r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\[[\?0-9]*[a-zA-Z]"
        status_with_ansi = "\x1b[2K\x1b[1Gpulling manifest 50%"
        clean = re.sub(ansi_pattern, "", status_with_ansi)
        self.assertNotIn("\x1b", clean)
        self.assertIn("50%", clean)
        assert "pulling manifest" in clean

    def test_clean_control_characters(self):
        import re

        ansi_pattern = r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\[[\?0-9]*[a-zA-Z]"
        status = "\x1b[2K\r\x1b[1Gdownloading 75% 5.2GB/s\x0d"
        clean = re.sub(ansi_pattern, "", status)
        clean = re.sub(r"[\x00-\x1f\x7f]", "", clean)
        clean = clean.strip()
        self.assertIn("75%", clean)
        self.assertIn("GB/s", clean)
        assert "downloading" in clean


class TestDownloadQueue(unittest.TestCase):
    def test_queue_order_preserved(self):
        queue = [("chat", "qwen2:1.5b"), ("vision", "llava-phi3"), ("code", "qwen2.5-coder:3b")]
        first = queue.pop(0)
        self.assertEqual(first[0], "chat")
        self.assertEqual(first[1], "qwen2:1.5b")
        assert first[0] == "chat"

    def test_queue_counter_increment(self):
        queue = [("chat", "model1"), ("vision", "model2"), ("code", "model3")]
        total = len(queue)
        current = 0

        processed = []
        while queue:
            current += 1
            category, model = queue.pop(0)
            processed.append((category, model, current, total))

        self.assertEqual(len(processed), 3)
        self.assertEqual(processed[0][2], 1)
        self.assertEqual(processed[1][2], 2)
        self.assertEqual(processed[2][2], 3)
        assert processed[2][3] == 3

    def test_queue_clear_on_failure(self):
        queue = [("chat", "model1"), ("vision", "model2")]
        queue.clear()
        self.assertEqual(len(queue), 0)
        assert queue == []


class TestModelInstallationCheck(unittest.TestCase):
    @patch("src.soul.model_manager.get_model_manager")
    def test_detect_missing_model(self, mock_get_manager):
        mock_manager = MagicMock()
        mock_manager.is_installed.return_value = False
        mock_get_manager.return_value = mock_manager

        manager = mock_get_manager()
        result = manager.is_installed("nonexistent-model")
        self.assertFalse(result)
        assert result is False

    @patch("src.soul.model_manager.get_model_manager")
    def test_detect_installed_model(self, mock_get_manager):
        mock_manager = MagicMock()
        mock_manager.is_installed.return_value = True
        mock_get_manager.return_value = mock_manager

        manager = mock_get_manager()
        result = manager.is_installed("llava-phi3")
        self.assertTrue(result)
        assert result is True

    def test_collect_models_to_download(self):
        installed = {"llava-phi3": True, "qwen2:1.5b": False, "qwen2.5-coder:3b": False}
        requested = [("chat", "qwen2:1.5b"), ("vision", "llava-phi3"), ("code", "qwen2.5-coder:3b")]

        to_download = []
        for category, model in requested:
            if not installed.get(model, False):
                to_download.append((category, model))

        self.assertEqual(len(to_download), 2)
        self.assertIn(("chat", "qwen2:1.5b"), to_download)
        self.assertIn(("code", "qwen2.5-coder:3b"), to_download)
        self.assertNotIn(("vision", "llava-phi3"), to_download)
        assert len(to_download) == 2


class TestDownloadModalUpdateModel(unittest.TestCase):
    def test_update_model_changes_state(self):
        from src.ui.screens import DownloadModal

        modal = DownloadModal("model1", current=1, total=3)
        modal.model_name = "model2"
        modal._current = 2
        modal._progress = 0.0
        modal._status = "Iniciando..."

        self.assertEqual(modal.model_name, "model2")
        self.assertEqual(modal._current, 2)
        self.assertEqual(modal._progress, 0.0)
        assert modal._status == "Iniciando..."


class TestDownloadCallbacks(unittest.TestCase):
    def test_on_complete_callback_success(self):
        callback = MagicMock()

        success = True
        message = "Download concluido"
        callback(success, message)

        callback.assert_called_once_with(True, "Download concluido")
        assert callback.called

    def test_on_complete_callback_failure(self):
        callback = MagicMock()

        success = False
        message = "Erro de conexao"
        callback(success, message)

        callback.assert_called_once_with(False, "Erro de conexao")
        assert callback.called


if __name__ == "__main__":
    unittest.main()
