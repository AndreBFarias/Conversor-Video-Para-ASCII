from unittest.mock import MagicMock


class TestAudioChunkDataclass:
    def test_fields(self):
        from src.soul.streaming import AudioChunk

        chunk = AudioChunk(sentence="Hello", audio_data=b"data", index=0, is_last=False)

        assert chunk.sentence == "Hello"
        assert chunk.audio_data == b"data"
        assert chunk.index == 0
        assert chunk.is_last is False

    def test_is_last_flag(self):
        from src.soul.streaming import AudioChunk

        chunk = AudioChunk(sentence="End", audio_data=b"", index=5, is_last=True)

        assert chunk.is_last is True


class TestSentenceStreamerInit:
    def test_default_min_length(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer()

        assert streamer.min_sentence_length == 10

    def test_custom_min_length(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=20)

        assert streamer.min_sentence_length == 20


class TestSentenceStreamerSplit:
    def test_empty_text(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer()

        result = streamer.split_into_sentences("")

        assert result == []

    def test_none_text(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer()

        result = streamer.split_into_sentences(None)

        assert result == []

    def test_short_text(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=20)

        result = streamer.split_into_sentences("Hi!")

        assert result == ["Hi!"]

    def test_single_sentence(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=5)

        result = streamer.split_into_sentences("This is a test sentence.")

        assert len(result) >= 1

    def test_multiple_sentences(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=5)

        result = streamer.split_into_sentences("First sentence. Second sentence! Third one?")

        assert len(result) >= 2

    def test_preserves_question_marks(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=5)

        result = streamer.split_into_sentences("Are you there? Yes I am!")

        assert len(result) >= 1
        assert any("?" in s for s in result)

    def test_merges_short_sentences(self):
        from src.soul.streaming import SentenceStreamer

        streamer = SentenceStreamer(min_sentence_length=30)

        result = streamer.split_into_sentences("Hi. Hello. How are you?")

        assert len(result) <= 2


class TestTTSStreamProcessorInit:
    def test_initialization(self):
        from src.soul.streaming import TTSStreamProcessor

        tts_cb = MagicMock()
        play_cb = MagicMock()

        processor = TTSStreamProcessor(tts_callback=tts_cb, playback_callback=play_cb, max_parallel=3)

        assert processor.tts_callback == tts_cb
        assert processor.playback_callback == play_cb
        assert processor.max_parallel == 3

    def test_default_max_parallel(self):
        from src.soul.streaming import TTSStreamProcessor

        processor = TTSStreamProcessor(tts_callback=MagicMock(), playback_callback=MagicMock())

        assert processor.max_parallel == 2


class TestTTSStreamProcessorProcessText:
    def test_empty_text_returns_early(self):
        from src.soul.streaming import TTSStreamProcessor

        tts_cb = MagicMock()
        play_cb = MagicMock()
        processor = TTSStreamProcessor(tts_callback=tts_cb, playback_callback=play_cb)

        processor.process_text("")

        tts_cb.assert_not_called()

    def test_processes_sentences(self):
        from src.soul.streaming import TTSStreamProcessor

        tts_cb = MagicMock(return_value=b"audio_data")
        play_cb = MagicMock()
        processor = TTSStreamProcessor(tts_callback=tts_cb, playback_callback=play_cb)

        processor.process_text("This is a long test sentence for processing.")

        assert tts_cb.call_count >= 1


class TestTTSStreamProcessorStop:
    def test_stop_sets_event(self):
        from src.soul.streaming import TTSStreamProcessor

        processor = TTSStreamProcessor(tts_callback=MagicMock(), playback_callback=MagicMock())

        processor.stop()

        assert processor._stop_event.is_set()

    def test_stop_clears_queue(self):
        from src.soul.streaming import TTSStreamProcessor

        processor = TTSStreamProcessor(tts_callback=MagicMock(), playback_callback=MagicMock())
        processor._audio_queue.put(MagicMock())
        processor._audio_queue.put(MagicMock())

        processor.stop()

        assert processor._audio_queue.empty()


class TestStreamingLLMAdapterInit:
    def test_with_no_clients(self):
        from src.soul.streaming import StreamingLLMAdapter

        adapter = StreamingLLMAdapter()

        assert adapter.ollama_client is None
        assert adapter.gemini_client is None

    def test_with_clients(self):
        from src.soul.streaming import StreamingLLMAdapter

        ollama = MagicMock()
        gemini = MagicMock()

        adapter = StreamingLLMAdapter(ollama_client=ollama, gemini_client=gemini)

        assert adapter.ollama_client == ollama
        assert adapter.gemini_client == gemini


class TestStreamingLLMAdapterStreamOllama:
    def test_returns_generator_without_client(self):
        from src.soul.streaming import StreamingLLMAdapter

        adapter = StreamingLLMAdapter()

        result = list(adapter.stream_ollama("prompt", "model"))

        assert result == []

    def test_streams_chunks(self):
        from src.soul.streaming import StreamingLLMAdapter

        ollama = MagicMock()
        ollama.generate_stream.return_value = ["chunk1", "chunk2", "chunk3"]

        adapter = StreamingLLMAdapter(ollama_client=ollama)

        result = list(adapter.stream_ollama("test prompt", "test-model"))

        assert result == ["chunk1", "chunk2", "chunk3"]

    def test_handles_exception(self):
        from src.soul.streaming import StreamingLLMAdapter

        ollama = MagicMock()
        ollama.generate_stream.side_effect = Exception("Connection error")

        adapter = StreamingLLMAdapter(ollama_client=ollama)

        result = list(adapter.stream_ollama("test", "model"))

        assert result == []


class TestStreamingLLMAdapterStreamGemini:
    def test_returns_generator_without_client(self):
        from src.soul.streaming import StreamingLLMAdapter

        adapter = StreamingLLMAdapter()

        result = list(adapter.stream_gemini("prompt", "model"))

        assert result == []

    def test_handles_exception(self):
        from src.soul.streaming import StreamingLLMAdapter

        gemini = MagicMock()
        gemini.models.generate_content_stream.side_effect = Exception("API error")

        adapter = StreamingLLMAdapter(gemini_client=gemini)

        result = list(adapter.stream_gemini("test", "model"))

        assert result == []


class TestProviderBaseStreaming:
    def test_base_supports_streaming_default_false(self):
        from src.soul.providers.base import LLMProvider

        class DummyProvider(LLMProvider):
            def generate(self, prompt, system, **kwargs):
                pass

            def is_available(self):
                return True

            def health_check(self):
                pass

            def get_model_name(self):
                return "dummy"

        provider = DummyProvider(name="dummy")
        assert provider.supports_streaming() is False

    def test_base_generate_stream_fallback(self):
        from src.soul.providers.base import LLMProvider, LLMResponse

        class DummyProvider(LLMProvider):
            def generate(self, prompt, system, **kwargs):
                return LLMResponse(text="full response", model="dummy", provider="dummy")

            def is_available(self):
                return True

            def health_check(self):
                pass

            def get_model_name(self):
                return "dummy"

        provider = DummyProvider(name="dummy")
        chunks = list(provider.generate_stream("prompt", "system"))

        assert chunks == ["full response"]


class TestOllamaProviderStreaming:
    def test_supports_streaming(self):
        from unittest.mock import patch

        with patch("src.soul.providers.ollama_provider.OllamaSyncClient"):
            from src.soul.providers.ollama_provider import OllamaProvider

            provider = OllamaProvider()
            assert provider.supports_streaming() is True

    def test_generate_stream_yields_chunks(self):
        from unittest.mock import patch

        mock_client = MagicMock()
        mock_client.stream.return_value = ["chunk1", "chunk2", "chunk3"]

        with patch("src.soul.providers.ollama_provider.OllamaSyncClient", return_value=mock_client):
            from src.soul.providers.ollama_provider import OllamaProvider

            provider = OllamaProvider()
            provider._client = mock_client

            chunks = list(provider.generate_stream("prompt", "system"))

            assert chunks == ["chunk1", "chunk2", "chunk3"]


class TestGeminiProviderStreaming:
    def test_supports_streaming(self):
        from unittest.mock import patch

        with patch("src.soul.providers.gemini_provider.genai"):
            from src.soul.providers.gemini_provider import GeminiProvider

            provider = GeminiProvider(api_key="test_key")
            assert provider.supports_streaming() is True


class TestUniversalLLMStreaming:
    def test_generate_stream_uses_streaming_provider(self):
        from unittest.mock import patch

        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_provider.priority = 0
        mock_provider.is_available.return_value = True
        mock_provider.supports_streaming.return_value = True
        mock_provider.generate_stream.return_value = iter(["a", "b", "c"])

        from src.soul.providers.universal_llm import UniversalLLM

        llm = UniversalLLM(providers=[mock_provider])
        chunks = list(llm.generate_stream("prompt", "system"))

        assert chunks == ["a", "b", "c"]
        mock_provider.generate_stream.assert_called_once()

    def test_generate_stream_fallback_on_error(self):
        mock_primary = MagicMock()
        mock_primary.name = "primary"
        mock_primary.priority = 0
        mock_primary.is_available.return_value = True
        mock_primary.supports_streaming.return_value = True
        mock_primary.generate_stream.side_effect = Exception("Primary failed")

        mock_fallback = MagicMock()
        mock_fallback.name = "fallback"
        mock_fallback.priority = 1
        mock_fallback.is_available.return_value = True
        mock_fallback.supports_streaming.return_value = True
        mock_fallback.generate_stream.return_value = iter(["fallback_chunk"])

        from src.soul.providers.universal_llm import UniversalLLM

        llm = UniversalLLM(providers=[mock_primary, mock_fallback])
        chunks = list(llm.generate_stream("prompt", "system"))

        assert chunks == ["fallback_chunk"]


class TestResponsePipelineProcessStream:
    def test_process_stream_yields_stages(self):
        from unittest.mock import patch

        with patch("src.soul.response_pipeline.get_context_builder") as mock_builder:
            mock_context = MagicMock()
            mock_context.total_estimated_tokens = 100
            mock_builder.return_value.build.return_value = mock_context
            mock_builder.return_value.build_prompt.return_value = "test prompt"

            with patch("src.soul.response_pipeline.get_parser") as mock_parser:
                mock_parser.return_value.parse.return_value = ({"fala_tts": "test"}, "simple")

                from src.soul.response_pipeline import ResponsePipeline

                pipeline = ResponsePipeline("test_entity")

                def mock_stream(prompt):
                    yield "Hello "
                    yield "World"

                results = list(pipeline.process_stream("test input", llm_stream_caller=mock_stream))

                stages = [r["stage"] for r in results]
                assert "context" in stages
                assert "chunk" in stages
                assert "complete" in stages

    def test_process_stream_accumulates_text(self):
        from unittest.mock import patch

        with patch("src.soul.response_pipeline.get_context_builder") as mock_builder:
            mock_context = MagicMock()
            mock_context.total_estimated_tokens = 50
            mock_builder.return_value.build.return_value = mock_context
            mock_builder.return_value.build_prompt.return_value = "prompt"

            with patch("src.soul.response_pipeline.get_parser") as mock_parser:
                mock_parser.return_value.parse.return_value = ({"fala_tts": "Hello World"}, "simple")

                from src.soul.response_pipeline import ResponsePipeline

                pipeline = ResponsePipeline("test_entity")

                def mock_stream(prompt):
                    yield "Hello "
                    yield "World"

                results = list(pipeline.process_stream("input", llm_stream_caller=mock_stream))

                complete = [r for r in results if r["stage"] == "complete"][0]
                assert complete["full_text"] == "Hello World"
                assert complete["success"] is True
