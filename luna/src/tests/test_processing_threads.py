from unittest.mock import MagicMock


class TestSanitizeLog:
    def test_redacts_email(self):
        from src.soul.processing_threads import sanitize_log

        result = sanitize_log("Contact me at test@example.com please")

        assert "test@example.com" not in result
        assert "[REDACTED]" in result

    def test_redacts_cpf(self):
        from src.soul.processing_threads import sanitize_log

        result = sanitize_log("Meu CPF e 123.456.789-00")

        assert "123.456.789-00" not in result
        assert "[REDACTED]" in result

    def test_truncates_long_text(self):
        from src.soul.processing_threads import sanitize_log

        long_text = "a" * 100

        result = sanitize_log(long_text, max_len=50)

        assert len(result) <= 53
        assert result.endswith("...")

    def test_handles_empty(self):
        from src.soul.processing_threads import sanitize_log

        result = sanitize_log("")

        assert result == ""

    def test_handles_none(self):
        from src.soul.processing_threads import sanitize_log

        result = sanitize_log(None)

        assert result == ""


class TestProcessingThreadInit:
    def test_creates_instance(self):
        from src.soul.processing_threads import ProcessingThread

        manager = MagicMock()
        consciencia = MagicMock()

        thread = ProcessingThread(manager, consciencia)

        assert thread.manager == manager
        assert thread.consciencia == consciencia
        assert thread._executor is not None


class TestAnimationThreadInit:
    def test_creates_instance(self):
        from src.soul.processing_threads import AnimationThread

        manager = MagicMock()
        controller = MagicMock()
        app = MagicMock()

        thread = AnimationThread(manager, controller, app)

        assert thread.manager == manager
        assert thread.animation_controller == controller
        assert thread.app == app


class TestCoordinatorThreadInit:
    def test_creates_instance(self):
        from src.soul.processing_threads import CoordinatorThread

        manager = MagicMock()
        app = MagicMock()

        thread = CoordinatorThread(manager, app)

        assert thread.manager == manager
        assert thread.app == app


class TestCoordinatorThreadExtractActions:
    def test_extracts_actions(self):
        from src.soul.processing_threads import CoordinatorThread

        thread = CoordinatorThread.__new__(CoordinatorThread)

        clean, actions = thread._extract_actions("[Luna sorri] Hello world [Luna acena]")

        assert "Luna sorri" in actions
        assert "Luna acena" in actions
        assert "[Luna" not in clean

    def test_no_actions(self):
        from src.soul.processing_threads import CoordinatorThread

        thread = CoordinatorThread.__new__(CoordinatorThread)

        clean, actions = thread._extract_actions("Hello world")

        assert actions == []
        assert clean == "Hello world"


class TestCoordinatorThreadParseMarkdown:
    def test_extracts_code_blocks(self):
        from src.soul.processing_threads import CoordinatorThread

        thread = CoordinatorThread.__new__(CoordinatorThread)

        text = "Hello\\n```python\\nprint('hi')\\n```\\nGoodbye"

        parts = thread._parse_markdown(text)

        code_parts = [p for p in parts if p[0] == "code"]
        assert len(code_parts) >= 1

    def test_no_code_blocks(self):
        from src.soul.processing_threads import CoordinatorThread

        thread = CoordinatorThread.__new__(CoordinatorThread)

        text = "Just plain text here"

        parts = thread._parse_markdown(text)

        assert len(parts) == 1
        assert parts[0][0] == "text"
        assert parts[0][1] == "Just plain text here"

    def test_handles_newline_escape(self):
        from src.soul.processing_threads import CoordinatorThread

        thread = CoordinatorThread.__new__(CoordinatorThread)

        text = "Line 1\\nLine 2"

        parts = thread._parse_markdown(text)

        assert "\n" in parts[0][1]


class TestRECodeBlock:
    def test_matches_code_block(self):
        from src.soul.processing_threads import RE_CODE_BLOCK

        text = "```python\nprint('hello')\n```"

        matches = RE_CODE_BLOCK.findall(text)

        assert len(matches) == 1
        assert matches[0][0] == "python"

    def test_matches_code_block_no_lang(self):
        from src.soul.processing_threads import RE_CODE_BLOCK

        text = "```\nsome code\n```"

        matches = RE_CODE_BLOCK.findall(text)

        assert len(matches) == 1
        assert matches[0][0] == ""


class TestREAction:
    def test_matches_luna_action(self):
        from src.soul.processing_threads import RE_ACTION

        text = "[Luna sorri]"

        matches = RE_ACTION.findall(text)

        assert len(matches) == 1
        assert "Luna sorri" in matches[0]

    def test_no_match_without_luna(self):
        from src.soul.processing_threads import RE_ACTION

        text = "[Something else]"

        matches = RE_ACTION.findall(text)

        assert len(matches) == 0


class TestSensitiveRE:
    def test_matches_email(self):
        from src.soul.processing_threads import _SENSITIVE_RE

        text = "email: user@test.com"

        match = _SENSITIVE_RE.search(text)

        assert match is not None

    def test_matches_cpf(self):
        from src.soul.processing_threads import _SENSITIVE_RE

        text = "cpf: 123.456.789-00"

        match = _SENSITIVE_RE.search(text)

        assert match is not None

    def test_matches_phone(self):
        from src.soul.processing_threads import _SENSITIVE_RE

        text = "tel: (11) 99999-8888"

        match = _SENSITIVE_RE.search(text)

        assert match is not None
