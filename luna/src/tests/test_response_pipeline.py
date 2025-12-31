from unittest.mock import Mock, patch

import pytest


class TestPipelineStage:
    def test_all_stages_exist(self):
        from src.soul.response_pipeline import PipelineStage

        assert PipelineStage.CONTEXT_BUILD.value == "context_build"
        assert PipelineStage.LLM_CALL.value == "llm_call"
        assert PipelineStage.RESPONSE_PARSE.value == "response_parse"
        assert PipelineStage.ACTION_EXECUTE.value == "action_execute"
        assert PipelineStage.MEMORY_UPDATE.value == "memory_update"

    def test_stages_count(self):
        from src.soul.response_pipeline import PipelineStage

        assert len(PipelineStage) == 5


class TestPipelineResult:
    def test_result_defaults(self):
        from src.soul.response_pipeline import PipelineResult, PipelineStage

        result = PipelineResult(success=False, stage=PipelineStage.CONTEXT_BUILD)
        assert result.success is False
        assert result.stage == PipelineStage.CONTEXT_BUILD
        assert result.context is None
        assert result.raw_response is None
        assert result.parsed_response is None
        assert result.error is None
        assert result.timing_ms == 0

    def test_result_with_values(self):
        from src.soul.response_pipeline import PipelineResult, PipelineStage

        result = PipelineResult(
            success=True,
            stage=PipelineStage.MEMORY_UPDATE,
            raw_response="Test response",
            parsed_response={"fala_tts": "Hello"},
            timing_ms=150,
        )
        assert result.success is True
        assert result.raw_response == "Test response"
        assert result.parsed_response["fala_tts"] == "Hello"
        assert result.timing_ms == 150


class TestResponsePipelineInit:
    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_init_creates_instance(self, mock_parser, mock_builder):
        from src.soul.response_pipeline import ResponsePipeline

        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        pipeline = ResponsePipeline("luna")

        assert pipeline.entity_id == "luna"
        assert pipeline.context_builder is not None
        assert pipeline.parser is not None
        mock_builder.assert_called_once_with("luna")

    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_init_creates_empty_hooks(self, mock_parser, mock_builder):
        from src.soul.response_pipeline import PipelineStage, ResponsePipeline

        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        pipeline = ResponsePipeline("luna")

        for stage in PipelineStage:
            assert stage in pipeline.hooks
            assert pipeline.hooks[stage] == []

    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_init_no_llm_caller(self, mock_parser, mock_builder):
        from src.soul.response_pipeline import ResponsePipeline

        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        pipeline = ResponsePipeline("luna")

        assert pipeline._llm_caller is None


class TestResponsePipelineHooks:
    @pytest.fixture
    def mock_pipeline(self):
        with (
            patch("src.soul.response_pipeline.get_context_builder") as mock_builder,
            patch("src.soul.response_pipeline.get_parser") as mock_parser,
        ):
            mock_builder.return_value = Mock()
            mock_parser.return_value = Mock()

            from src.soul.response_pipeline import ResponsePipeline

            pipeline = ResponsePipeline("luna")
            return pipeline

    def test_set_llm_caller(self, mock_pipeline):
        def caller(x):
            return "response"

        mock_pipeline.set_llm_caller(caller)

        assert mock_pipeline._llm_caller is caller

    def test_add_hook(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook = Mock()
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook)

        assert hook in mock_pipeline.hooks[PipelineStage.LLM_CALL]

    def test_add_multiple_hooks(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook1 = Mock()
        hook2 = Mock()

        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook1)
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook2)

        assert len(mock_pipeline.hooks[PipelineStage.LLM_CALL]) == 2

    def test_remove_hook(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook = Mock()
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook)
        mock_pipeline.remove_hook(PipelineStage.LLM_CALL, hook)

        assert hook not in mock_pipeline.hooks[PipelineStage.LLM_CALL]

    def test_remove_nonexistent_hook(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook = Mock()
        mock_pipeline.remove_hook(PipelineStage.LLM_CALL, hook)

        assert len(mock_pipeline.hooks[PipelineStage.LLM_CALL]) == 0

    def test_run_hooks_calls_all(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook1 = Mock()
        hook2 = Mock()

        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook1)
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook2)

        mock_pipeline._run_hooks(PipelineStage.LLM_CALL, "test_data")

        hook1.assert_called_once_with("test_data")
        hook2.assert_called_once_with("test_data")
        assert hook1.call_count == 1
        assert hook2.call_count == 1

    def test_run_hooks_handles_error(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        hook1 = Mock(side_effect=Exception("Hook error"))
        hook2 = Mock()

        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook1)
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, hook2)

        mock_pipeline._run_hooks(PipelineStage.LLM_CALL, "test_data")

        hook2.assert_called_once_with("test_data")
        assert hook2.call_count == 1


class TestResponsePipelineProcess:
    @pytest.fixture
    def mock_pipeline(self):
        with (
            patch("src.soul.response_pipeline.get_context_builder") as mock_builder,
            patch("src.soul.response_pipeline.get_parser") as mock_parser,
        ):
            mock_context = Mock()
            mock_context.total_estimated_tokens = 100

            mock_builder_instance = Mock()
            mock_builder_instance.build.return_value = mock_context
            mock_builder_instance.build_prompt.return_value = "Formatted prompt"
            mock_builder.return_value = mock_builder_instance

            mock_parser_instance = Mock()
            mock_parser_instance.parse.return_value = (
                {"fala_tts": "Hello", "animacao": "observando", "log_terminal": "[Luna] Hello"},
                "json",
            )
            mock_parser.return_value = mock_parser_instance

            from src.soul.response_pipeline import ResponsePipeline

            pipeline = ResponsePipeline("luna")
            return pipeline

    def test_process_no_llm_caller(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        result = mock_pipeline.process("Hello")

        assert result.success is False
        assert result.stage == PipelineStage.LLM_CALL
        assert "LLM caller not configured" in result.error

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_process_success(self, mock_memory, mock_pipeline):
        mock_memory.return_value = Mock()
        mock_pipeline.set_llm_caller(lambda x: '{"fala_tts": "Response"}')

        result = mock_pipeline.process("Hello")

        assert result.success is True
        assert result.context is not None
        assert result.raw_response is not None
        assert result.parsed_response is not None
        assert result.timing_ms >= 0

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_process_calls_hooks(self, mock_memory, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        mock_memory.return_value = Mock()
        mock_pipeline.set_llm_caller(lambda x: '{"fala_tts": "Response"}')

        context_hook = Mock()
        llm_hook = Mock()
        parse_hook = Mock()

        mock_pipeline.add_hook(PipelineStage.CONTEXT_BUILD, context_hook)
        mock_pipeline.add_hook(PipelineStage.LLM_CALL, llm_hook)
        mock_pipeline.add_hook(PipelineStage.RESPONSE_PARSE, parse_hook)

        mock_pipeline.process("Hello")

        context_hook.assert_called_once()
        llm_hook.assert_called_once()
        parse_hook.assert_called_once()
        assert context_hook.call_count == 1
        assert llm_hook.call_count == 1
        assert parse_hook.call_count == 1

    def test_process_context_build_failure(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        mock_pipeline.context_builder.build.side_effect = Exception("Context error")

        result = mock_pipeline.process("Hello")

        assert result.success is False
        assert result.stage == PipelineStage.CONTEXT_BUILD
        assert "Context build failed" in result.error

    def test_process_llm_call_failure(self, mock_pipeline):
        from src.soul.response_pipeline import PipelineStage

        mock_pipeline.set_llm_caller(Mock(side_effect=Exception("LLM error")))

        result = mock_pipeline.process("Hello")

        assert result.success is False
        assert result.stage == PipelineStage.LLM_CALL
        assert "LLM call failed" in result.error

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_process_parse_failure_uses_fallback(self, mock_memory, mock_pipeline):
        mock_memory.return_value = Mock()
        mock_pipeline.set_llm_caller(lambda x: "Invalid response")
        mock_pipeline.parser.parse.side_effect = Exception("Parse error")

        result = mock_pipeline.process("Hello")

        assert result.success is True
        assert result.parsed_response is not None
        assert result.parsed_response["animacao"] == "Luna_observando"

    @patch("src.data_memory.smart_memory.get_entity_smart_memory")
    def test_process_memory_failure_continues(self, mock_memory, mock_pipeline):
        mock_memory.side_effect = Exception("Memory error")
        mock_pipeline.set_llm_caller(lambda x: '{"fala_tts": "Response"}')

        result = mock_pipeline.process("Hello")

        assert result.success is True


class TestResponsePipelineStream:
    @pytest.fixture
    def mock_pipeline(self):
        with (
            patch("src.soul.response_pipeline.get_context_builder") as mock_builder,
            patch("src.soul.response_pipeline.get_parser") as mock_parser,
        ):
            mock_context = Mock()
            mock_context.total_estimated_tokens = 100

            mock_builder_instance = Mock()
            mock_builder_instance.build.return_value = mock_context
            mock_builder_instance.build_prompt.return_value = "Formatted prompt"
            mock_builder.return_value = mock_builder_instance

            mock_parser.return_value = Mock()

            from src.soul.response_pipeline import ResponsePipeline

            pipeline = ResponsePipeline("luna")
            return pipeline

    def test_process_stream_yields_context(self, mock_pipeline):
        gen = mock_pipeline.process_stream("Hello")
        first = next(gen)

        assert first["stage"] == "context"
        assert first["tokens"] == 100

    def test_process_stream_yields_complete(self, mock_pipeline):
        mock_pipeline._llm_caller = lambda prompt: "Mocked response"
        mock_pipeline.parser.parse.return_value = ({"fala_tts": "test"}, "simple")

        gen = mock_pipeline.process_stream("Hello")
        results = list(gen)

        assert results[-1]["stage"] == "complete"
        assert results[-1]["success"] is True


class TestGetResponsePipeline:
    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_get_response_pipeline_returns_instance(self, mock_parser, mock_builder):
        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        from src.soul.response_pipeline import _pipelines, get_response_pipeline

        _pipelines.clear()

        pipeline = get_response_pipeline("luna")

        assert pipeline is not None
        assert pipeline.entity_id == "luna"

    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_get_response_pipeline_caches(self, mock_parser, mock_builder):
        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        from src.soul.response_pipeline import _pipelines, get_response_pipeline

        _pipelines.clear()

        pipeline1 = get_response_pipeline("luna")
        pipeline2 = get_response_pipeline("luna")

        assert pipeline1 is pipeline2

    @patch("src.soul.response_pipeline.get_context_builder")
    @patch("src.soul.response_pipeline.get_parser")
    def test_get_response_pipeline_different_entities(self, mock_parser, mock_builder):
        mock_builder.return_value = Mock()
        mock_parser.return_value = Mock()

        from src.soul.response_pipeline import _pipelines, get_response_pipeline

        _pipelines.clear()

        pipeline_luna = get_response_pipeline("luna")
        pipeline_eris = get_response_pipeline("eris")

        assert pipeline_luna is not pipeline_eris
        assert pipeline_luna.entity_id == "luna"
        assert pipeline_eris.entity_id == "eris"
