import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSessionManagerInit:
    def test_init_with_app(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        assert sm.app is mock_app
        assert sm.current_session_id is None
        assert sm.conversation_history == []
        assert sm._user_message_count == 0

    def test_init_summary_interval(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        assert sm._summary_interval == 2
        assert sm._current_summary is None


class TestOnMessageAdded:
    def test_increments_user_count(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        sm.on_message_added("user")
        assert sm._user_message_count == 1

        sm.on_message_added("user")
        assert sm._user_message_count == 2

    def test_does_not_increment_for_model(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        sm.on_message_added("model")
        assert sm._user_message_count == 0


class TestResetMessageCount:
    def test_resets_count_to_zero(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        sm._user_message_count = 10
        sm._current_summary = "Test summary"

        sm.reset_message_count()

        assert sm._user_message_count == 0
        assert sm._current_summary is None


class TestLoadSession:
    def test_load_session_file_not_found(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        mock_app.add_chat_entry = MagicMock()
        sm = SessionManager(mock_app)

        with patch("src.core.session.manager.config") as mock_config:
            mock_config.SESSIONS_DIR = "/nonexistent/path"
            sm.load_session("fake_session_id")

        mock_app.add_chat_entry.assert_called()

    def test_load_session_valid_file(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        mock_app.query_one = MagicMock(return_value=MagicMock())
        mock_app.add_chat_entry = MagicMock()
        sm = SessionManager(mock_app)

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "test_session.json"
            session_data = [
                {"role": "user", "parts": ["Hello"]},
                {"role": "model", "parts": ["Hi there"]},
            ]
            session_file.write_text(json.dumps(session_data))

            with (
                patch("src.core.session.manager.config") as mock_config,
                patch("src.core.session.manager.asyncio.create_task"),
            ):
                mock_config.SESSIONS_DIR = tmpdir
                sm.load_session("test_session")

            assert sm.current_session_id == "test_session"
            assert len(sm.conversation_history) == 2


class TestSaveCurrentSession:
    def test_save_empty_history_does_nothing(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)
        sm.conversation_history = []

        asyncio.run(sm.save_current_session())

        assert sm.current_session_id is None

    def test_save_creates_session_id(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)
        sm.conversation_history = [
            {"role": "user", "parts": ["Hello"]},
            {"role": "model", "parts": ["Hi"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"

            with (
                patch("src.core.session.manager.config") as mock_config,
                patch("src.core.session.manager.os.path.exists") as mock_exists,
            ):
                mock_config.SESSIONS_DIR = tmpdir
                mock_config.MANIFEST_FILE = str(manifest_file)
                mock_config.CHAT_PROVIDER = "local"
                mock_exists.return_value = False

                asyncio.run(sm.save_current_session())

            assert sm.current_session_id is not None


class TestUpdateManifestTitle:
    def test_creates_session_id_if_none(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"

            with (
                patch("src.core.session.manager.config") as mock_config,
                patch("src.core.session.manager.os.path.exists") as mock_exists,
            ):
                mock_config.MANIFEST_FILE = str(manifest_file)
                mock_exists.return_value = False

                sm._update_manifest_title("Test Title")

            assert sm.current_session_id is not None

    def test_updates_existing_manifest(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)
        sm.current_session_id = "existing_session"

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "manifest.json"
            manifest_file.write_text('{"other_session": {"title": "Other"}}')

            with (
                patch("src.core.session.manager.config") as mock_config,
                patch("src.core.session.manager.os.path.exists") as mock_exists,
            ):
                mock_config.MANIFEST_FILE = str(manifest_file)
                mock_exists.return_value = True

                sm._update_manifest_title("New Title")

            manifest_data = json.loads(manifest_file.read_text())
            assert "existing_session" in manifest_data
            assert manifest_data["existing_session"]["title"] == "New Title"


class TestGenerateLiveSummary:
    def test_skips_if_history_too_short(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)
        sm.conversation_history = [{"role": "user", "parts": ["Hi"]}]

        sm._generate_live_summary()

        assert sm._current_summary is None


class TestSessionDataStructure:
    def test_conversation_history_is_list(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        assert isinstance(sm.conversation_history, list)

    def test_can_append_to_history(self):
        from src.core.session import SessionManager

        mock_app = MagicMock()
        sm = SessionManager(mock_app)

        sm.conversation_history.append({"role": "user", "parts": ["Test"]})
        assert len(sm.conversation_history) == 1
        assert sm.conversation_history[0]["role"] == "user"
