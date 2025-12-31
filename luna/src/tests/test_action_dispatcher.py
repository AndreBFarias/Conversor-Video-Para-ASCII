from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_consciencia():
    mock = MagicMock()
    mock.web_search = MagicMock()
    mock.web_search.search.return_value = [
        {"title": "Resultado 1", "snippet": "Descricao do resultado 1"},
        {"title": "Resultado 2", "snippet": "Descricao do resultado 2"},
    ]
    return mock


@pytest.fixture
def mock_terminal():
    with patch("src.soul.consciencia.services.action_dispatcher.get_terminal_executor") as mock:
        executor = MagicMock()
        executor.execute.return_value = (0, "output", "")
        mock.return_value = executor
        yield executor


class TestActionDispatcherInit:
    def test_creates_dispatcher(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)

        assert dispatcher._consciencia == mock_consciencia
        assert dispatcher._max_commands == 5
        assert dispatcher._command_timeout == 30

    def test_properties(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        stats = dispatcher.get_stats()

        assert stats["max_commands"] == 5
        assert stats["command_timeout"] == 30
        assert stats["web_search_enabled"] is True


class TestActionDispatcherFilesystemOps:
    def test_execute_filesystem_ops_empty(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": []}
        result = dispatcher.execute_filesystem_ops(data, "test input")

        assert result["log_terminal"] == "test"

    def test_execute_filesystem_ops_single_command(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": ["ls -la"]}
        result = dispatcher.execute_filesystem_ops(data, "test input")

        assert "--- TERMINAL ---" in result["log_terminal"]
        assert "$ ls -la" in result["log_terminal"]

    def test_execute_filesystem_ops_error(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        mock_terminal.execute.return_value = (1, "", "command not found")

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": ["invalid_cmd"]}
        result = dispatcher.execute_filesystem_ops(data, "test input")

        assert "[ERRO]" in result["log_terminal"]

    def test_execute_filesystem_ops_max_commands(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        commands = ["cmd1", "cmd2", "cmd3", "cmd4", "cmd5", "cmd6", "cmd7"]
        data = {"log_terminal": "test", "filesystem_ops": commands}
        dispatcher.execute_filesystem_ops(data, "test input")

        assert mock_terminal.execute.call_count == 5


class TestActionDispatcherNaturalCommands:
    def test_natural_command_parsed(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        with patch("src.soul.consciencia.services.action_dispatcher.parse_natural_command") as mock_parse:
            mock_parse.return_value = "ls -la"

            dispatcher = ActionDispatcher(mock_consciencia)
            data = {"log_terminal": "test", "filesystem_ops": []}
            result = dispatcher.execute_filesystem_ops(data, "liste os arquivos")

            assert "$ ls -la" in result["log_terminal"]

    def test_natural_command_not_parsed(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        with patch("src.soul.consciencia.services.action_dispatcher.parse_natural_command") as mock_parse:
            mock_parse.return_value = None

            dispatcher = ActionDispatcher(mock_consciencia)
            data = {"log_terminal": "test", "filesystem_ops": []}
            result = dispatcher.execute_filesystem_ops(data, "oi")

            assert result["log_terminal"] == "test"


class TestActionDispatcherWebSearch:
    def test_execute_web_search_success(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        result = dispatcher.execute_web_search("python tutorial")

        assert result is not None
        assert "Resultado 1" in result

    def test_execute_web_search_no_results(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        mock_consciencia.web_search.search.return_value = []

        dispatcher = ActionDispatcher(mock_consciencia)
        result = dispatcher.execute_web_search("xyz123abc")

        assert result is None

    def test_execute_web_search_not_available(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        mock_consciencia.web_search = None

        dispatcher = ActionDispatcher(mock_consciencia)
        result = dispatcher.execute_web_search("test")

        assert result is None

    def test_execute_web_search_error(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        mock_consciencia.web_search.search.side_effect = Exception("API error")

        dispatcher = ActionDispatcher(mock_consciencia)
        result = dispatcher.execute_web_search("test")

        assert result is None


class TestActionDispatcherDispatch:
    def test_dispatch_with_filesystem_ops(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": ["echo hello"]}
        result = dispatcher.dispatch(data, "test")

        assert "--- TERMINAL ---" in result["log_terminal"]

    def test_dispatch_with_web_search(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": [], "pesquisa_web": "python docs"}
        result = dispatcher.dispatch(data, "test")

        assert "--- WEB ---" in result["log_terminal"]

    def test_dispatch_with_empty_web_search(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {"log_terminal": "test", "filesystem_ops": [], "pesquisa_web": ""}
        result = dispatcher.dispatch(data, "test")

        assert "--- WEB ---" not in result["log_terminal"]

    def test_dispatch_combined(self, mock_consciencia, mock_terminal):
        from src.soul.consciencia.services import ActionDispatcher

        dispatcher = ActionDispatcher(mock_consciencia)
        data = {
            "log_terminal": "test",
            "filesystem_ops": ["pwd"],
            "pesquisa_web": "python docs",
        }
        result = dispatcher.dispatch(data, "test")

        assert "--- TERMINAL ---" in result["log_terminal"]
        assert "--- WEB ---" in result["log_terminal"]
