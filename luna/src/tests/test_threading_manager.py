import queue
import threading
from unittest.mock import MagicMock, patch

import pytest


class TestRingBuffer:
    def test_init_default(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer()

        assert buf.maxsize == 100
        assert buf.name == "buffer"
        assert buf.qsize() == 0

    def test_init_custom(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=50, name="test_buf")

        assert buf.maxsize == 50
        assert buf.name == "test_buf"

    def test_put_get(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=10)

        buf.put("item1")
        buf.put("item2")

        assert buf.qsize() == 2
        assert buf.get() == "item1"
        assert buf.get() == "item2"

    def test_put_nowait(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=10)

        result = buf.put_nowait("item")

        assert result is True
        assert buf.qsize() == 1

    def test_get_nowait_empty(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer()

        with pytest.raises(queue.Empty):
            buf.get_nowait()

    def test_overflow_drops_oldest(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=3)

        buf.put("a")
        buf.put("b")
        buf.put("c")
        result = buf.put("d")

        assert result is False
        assert buf.qsize() == 3

        stats = buf.get_stats()
        assert stats["drops"] == 1

    def test_empty(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer()

        assert buf.empty() is True
        buf.put("item")
        assert buf.empty() is False

    def test_full(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=2)

        assert buf.full() is False
        buf.put("a")
        buf.put("b")
        assert buf.full() is True

    def test_clear(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer()
        buf.put("a")
        buf.put("b")

        count = buf.clear()

        assert count == 2
        assert buf.qsize() == 0

    def test_get_stats(self):
        from src.soul.threading_manager import RingBuffer

        buf = RingBuffer(maxsize=5, name="test")
        buf.put("a")
        buf.put("b")

        stats = buf.get_stats()

        assert stats["name"] == "test"
        assert stats["size"] == 2
        assert stats["maxsize"] == 5
        assert stats["total_puts"] == 2


class TestBackpressureQueue:
    def test_init_default(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue()

        assert q.maxsize == 50
        assert q.name == "queue"
        assert q.drop_oldest is True

    def test_put_get(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue()

        q.put("item1")
        q.put("item2")

        assert q.qsize() == 2
        assert q.get() == "item1"

    def test_drops_oldest_when_full(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=2, drop_oldest=True)

        q.put("a")
        q.put("b")
        q.put("c")

        assert q.qsize() == 2
        assert q.get() == "b"

    def test_drops_newest_when_configured(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=2, drop_oldest=False)

        q.put("a")
        q.put("b")
        result = q.put("c")

        assert result is False
        assert q.qsize() == 2

    def test_backpressure_activation(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=10)

        for i in range(9):
            q.put(i)

        assert q.is_backpressure_active() is True

    def test_backpressure_deactivation(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=10)

        for i in range(9):
            q.put(i)

        while q.qsize() > 4:
            q.get()

        assert q.is_backpressure_active() is False

    def test_empty_full(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=2)

        assert q.empty() is True
        assert q.full() is False

        q.put("a")
        q.put("b")

        assert q.empty() is False
        assert q.full() is True

    def test_clear(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue()
        q.put("a")
        q.put("b")

        count = q.clear()

        assert count == 2
        assert q.qsize() == 0
        assert q.is_backpressure_active() is False

    def test_get_stats(self):
        from src.soul.threading_manager import BackpressureQueue

        q = BackpressureQueue(maxsize=10, name="test")
        q.put("a")

        stats = q.get_stats()

        assert stats["name"] == "test"
        assert stats["size"] == 1
        assert stats["maxsize"] == 10
        assert "high_watermark" in stats
        assert "low_watermark" in stats


class TestThreadState:
    def test_all_states_exist(self):
        from src.soul.threading_manager import ThreadState

        assert ThreadState.STOPPED.value == "stopped"
        assert ThreadState.STARTING.value == "starting"
        assert ThreadState.RUNNING.value == "running"
        assert ThreadState.STOPPING.value == "stopping"
        assert ThreadState.ERROR.value == "error"


class TestDataclasses:
    def test_audio_chunk(self):
        from src.soul.threading_manager import AudioChunk

        chunk = AudioChunk(data=b"test", sample_rate=16000, timestamp=1.0)

        assert chunk.data == b"test"
        assert chunk.sample_rate == 16000

    def test_transcription_result(self):
        from src.soul.threading_manager import TranscriptionResult

        result = TranscriptionResult(text="hello", confidence=0.95, timestamp=1.0)

        assert result.text == "hello"
        assert result.confidence == 0.95

    def test_processing_request(self):
        from src.soul.threading_manager import ProcessingRequest

        req = ProcessingRequest(user_text="hello", visual_context="room")

        assert req.user_text == "hello"
        assert req.visual_context == "room"

    def test_luna_response(self):
        from src.soul.threading_manager import LunaResponse

        resp = LunaResponse(
            fala_tts="Ola",
            log_terminal="[Luna] Ola",
            animacao="feliz",
            tts_config={},
            metadata={},
        )

        assert resp.fala_tts == "Ola"
        assert resp.animacao == "feliz"

    def test_tts_chunk(self):
        from src.soul.threading_manager import TTSChunk

        chunk = TTSChunk(audio_data=b"audio", chunk_index=0, total_chunks=3)

        assert chunk.chunk_index == 0
        assert chunk.format == "wav"


class TestLunaThreadingManager:
    def test_init_creates_queues(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()

            assert manager.audio_input_queue is not None
            assert manager.transcription_queue is not None
            assert manager.processing_queue is not None

    def test_init_creates_events(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()

            assert isinstance(manager.interrupt_event, threading.Event)
            assert isinstance(manager.shutdown_event, threading.Event)
            assert isinstance(manager.listening_event, threading.Event)

    def test_register_thread(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager, ThreadState

            manager = LunaThreadingManager()
            mock_target = MagicMock()

            thread = manager.register_thread("test_thread", mock_target)

            assert "test_thread" in manager.threads
            assert manager.thread_states["test_thread"] == ThreadState.STOPPED

    def test_get_queue_sizes(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()
            manager.transcription_queue.put("test")

            sizes = manager.get_queue_sizes()

            assert sizes["transcription"] == 1
            assert sizes["processing"] == 0

    def test_trigger_interrupt(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()
            manager.transcription_queue.put("test")

            manager.trigger_interrupt()

            assert manager.interrupt_event.is_set()
            assert manager.transcription_queue.empty()

    def test_clear_interrupt(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()
            manager.interrupt_event.set()

            manager.clear_interrupt()

            assert not manager.interrupt_event.is_set()

    def test_get_thread_status(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()
            mock_target = MagicMock()
            manager.register_thread("test", mock_target)

            status = manager.get_thread_status()

            assert "test" in status
            assert status["test"]["state"] == "stopped"

    def test_record_init_time(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()

            manager.record_init_time("whisper", 2.5)

            times = manager.get_init_times()
            assert "whisper" in times
            assert times["whisper"]["duration"] == 2.5

    def test_get_ring_buffer_stats(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()

            stats = manager.get_ring_buffer_stats()

            assert "name" in stats
            assert stats["name"] == "audio_input"


class TestMonitorThread:
    def test_init(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager, MonitorThread

            manager = LunaThreadingManager()
            monitor = MonitorThread(manager, interval=1.0)

            assert monitor.manager is manager
            assert monitor.interval == 1.0

    def test_run_stops_on_shutdown(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager, MonitorThread

            manager = LunaThreadingManager()
            monitor = MonitorThread(manager, interval=0.1)

            manager.shutdown_event.set()

            monitor.run()

            assert manager.shutdown_event.is_set()


class TestHealthCheck:
    def test_returns_health_dict(self):
        with patch("src.soul.threading_manager.manager.config") as mock_config:
            mock_config.QUEUE_CONFIG = {
                "AUDIO_INPUT": 100,
                "TRANSCRIPTION": 50,
                "PROCESSING": 20,
                "RESPONSE": 10,
                "TTS": 30,
                "ANIMATION": 20,
                "VISION": 5,
                "WAKE_WORD": 50,
            }

            from src.soul.threading_manager import LunaThreadingManager

            manager = LunaThreadingManager()

            health = manager.health_check()

            assert "healthy" in health
            assert "threads" in health
            assert "queues" in health
            assert "warnings" in health
