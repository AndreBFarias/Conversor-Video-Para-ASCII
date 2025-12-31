from unittest.mock import MagicMock


class TestUIController:
    def test_get_widget_returns_none_on_missing(self):
        from src.controllers.ui_controller import UIController

        mock_app = MagicMock()
        mock_app.query_one.side_effect = Exception("Not found")

        controller = UIController(mock_app)
        result = controller.get_widget("#nonexistent")

        assert result is None

    def test_update_status_calls_widget(self):
        from src.controllers.ui_controller import UIController

        mock_app = MagicMock()
        mock_widget = MagicMock()
        mock_app.query_one.return_value = mock_widget

        controller = UIController(mock_app)
        controller.update_status("Test Status")

        mock_widget.update.assert_called_once_with("Test Status")

    def test_update_emotion_label(self):
        from src.controllers.ui_controller import UIController

        mock_app = MagicMock()
        mock_widget = MagicMock()
        mock_app.query_one.return_value = mock_widget

        controller = UIController(mock_app)
        controller.update_emotion_label("curiosa", "Luna")

        mock_widget.update.assert_called_once_with("[Luna esta curiosa]")

    def test_toggle_fullscreen_ascii_add_class(self):
        from src.controllers.ui_controller import UIController

        mock_app = MagicMock()
        mock_widget = MagicMock()
        mock_app.query_one.return_value = mock_widget

        controller = UIController(mock_app)
        controller.toggle_fullscreen_ascii(True)

        mock_widget.add_class.assert_called_once_with("fullscreen")

    def test_toggle_fullscreen_ascii_remove_class(self):
        from src.controllers.ui_controller import UIController

        mock_app = MagicMock()
        mock_widget = MagicMock()
        mock_app.query_one.return_value = mock_widget

        controller = UIController(mock_app)
        controller.toggle_fullscreen_ascii(False)

        mock_widget.remove_class.assert_called_once_with("fullscreen")


class TestThreadingController:
    def test_queue_sizes_returns_dict(self):
        from src.controllers.threading_controller import ThreadingController

        mock_app = MagicMock()

        controller = ThreadingController(mock_app)
        sizes = controller.get_queue_sizes()

        assert isinstance(sizes, dict)
        assert "audio_input" in sizes
        assert "tts" in sizes
        assert "transcription" in sizes
        assert "processing" in sizes

    def test_queues_work_correctly(self):
        from src.controllers.threading_controller import ThreadingController

        mock_app = MagicMock()

        controller = ThreadingController(mock_app)
        controller.audio_input_queue.put("test_audio")
        controller.tts_queue.put("test_tts")

        sizes = controller.get_queue_sizes()
        assert sizes["audio_input"] == 1
        assert sizes["tts"] == 1

    def test_clear_queues(self):
        from src.controllers.threading_controller import ThreadingController

        mock_app = MagicMock()

        controller = ThreadingController(mock_app)
        controller.audio_input_queue.put("test1")
        controller.audio_input_queue.put("test2")
        controller.transcription_queue.put("test3")

        controller.clear_queues()

        sizes = controller.get_queue_sizes()
        assert sizes["audio_input"] == 0
        assert sizes["transcription"] == 0

    def test_is_running_returns_false_initially(self):
        from src.controllers.threading_controller import ThreadingController

        mock_app = MagicMock()

        controller = ThreadingController(mock_app)

        assert not controller.is_running("audio_capture")
        assert not controller.is_running("nonexistent")


class TestAudioController:
    def test_initial_state(self):
        from src.controllers.audio_controller import AudioController

        mock_app = MagicMock()

        controller = AudioController(mock_app)

        assert controller.em_chamada == False
        assert controller.is_recording() == False

    def test_toggle_voice_mode(self):
        from src.controllers.audio_controller import AudioController

        mock_app = MagicMock()

        controller = AudioController(mock_app)
        assert controller.em_chamada == False

        result = controller.toggle_voice_mode()
        assert result == True
        assert controller.em_chamada == True

        result = controller.toggle_voice_mode()
        assert result == False
        assert controller.em_chamada == False

    def test_em_chamada_setter(self):
        from src.controllers.audio_controller import AudioController

        mock_app = MagicMock()

        controller = AudioController(mock_app)
        controller.em_chamada = True

        assert controller._em_chamada == True

    def test_start_stop_recording(self):
        from src.controllers.audio_controller import AudioController

        mock_app = MagicMock()

        controller = AudioController(mock_app)

        assert controller.is_recording() == False
        controller.start_recording()
        assert controller.is_recording() == True
        controller.stop_recording()
        assert controller.is_recording() == False

    def test_enable_wake_word(self):
        from src.controllers.audio_controller import AudioController

        mock_app = MagicMock()

        controller = AudioController(mock_app)

        controller.enable_wake_word(False)
        assert controller._wake_word_enabled == False

        controller.enable_wake_word(True)
        assert controller._wake_word_enabled == True
