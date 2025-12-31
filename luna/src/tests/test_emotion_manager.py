import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestGenderForms(unittest.TestCase):
    def test_gender_forms_exist(self):
        from src.ui.emotion_manager import GENDER_FORMS

        self.assertIsInstance(GENDER_FORMS, dict)
        self.assertGreater(len(GENDER_FORMS), 0)
        assert len(GENDER_FORMS) > 0

    def test_gender_forms_structure(self):
        from src.ui.emotion_manager import GENDER_FORMS

        for key, value in GENDER_FORMS.items():
            self.assertIsInstance(value, tuple)
            self.assertEqual(len(value), 2)
            feminine, masculine = value
            self.assertIsInstance(feminine, str)
            self.assertIsInstance(masculine, str)
            assert len(value) == 2

    def test_gender_forms_contains_required(self):
        from src.ui.emotion_manager import GENDER_FORMS

        required = ["observando", "curiosa", "sarcastica", "feliz", "irritada", "triste"]
        for emotion in required:
            self.assertIn(emotion, GENDER_FORMS)
            assert emotion in GENDER_FORMS


class TestGenderInflection(unittest.TestCase):
    def test_feminine_form_curiosa(self):
        from src.ui.emotion_manager import GENDER_FORMS

        fem, masc = GENDER_FORMS["curiosa"]
        self.assertEqual(fem, "curiosa")
        self.assertEqual(masc, "curioso")
        assert fem != masc

    def test_masculine_form_curioso(self):
        from src.ui.emotion_manager import GENDER_FORMS

        fem, masc = GENDER_FORMS["curiosa"]
        gender = "masculine"
        result = masc if gender == "masculine" else fem
        self.assertEqual(result, "curioso")
        assert result == "curioso"

    def test_feminine_form_irritada(self):
        from src.ui.emotion_manager import GENDER_FORMS

        fem, masc = GENDER_FORMS["irritada"]
        gender = "feminine"
        result = masc if gender == "masculine" else fem
        self.assertEqual(result, "irritada")
        assert result == "irritada"

    def test_neutral_form_feliz(self):
        from src.ui.emotion_manager import GENDER_FORMS

        fem, masc = GENDER_FORMS["feliz"]
        self.assertEqual(fem, masc)
        self.assertEqual(fem, "feliz")
        assert fem == masc


class TestPrefixStripping(unittest.TestCase):
    def test_strip_luna_prefix(self):
        sentiment = "Luna_curiosa"
        prefixes = ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]

        emotion = sentiment
        for prefix in prefixes:
            if sentiment.startswith(f"{prefix}_"):
                emotion = sentiment[len(prefix) + 1 :]
                break

        self.assertEqual(emotion, "curiosa")
        assert emotion == "curiosa"

    def test_strip_mars_prefix(self):
        sentiment = "Mars_curiosa"
        prefixes = ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]

        emotion = sentiment
        for prefix in prefixes:
            if sentiment.startswith(f"{prefix}_"):
                emotion = sentiment[len(prefix) + 1 :]
                break

        self.assertEqual(emotion, "curiosa")
        assert emotion == "curiosa"

    def test_strip_juno_prefix(self):
        sentiment = "Juno_obssecada"
        prefixes = ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]

        emotion = sentiment
        for prefix in prefixes:
            if sentiment.startswith(f"{prefix}_"):
                emotion = sentiment[len(prefix) + 1 :]
                break

        self.assertEqual(emotion, "obssecada")
        assert emotion == "obssecada"

    def test_no_prefix_unchanged(self):
        sentiment = "curiosa"
        prefixes = ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]

        emotion = sentiment
        for prefix in prefixes:
            if sentiment.startswith(f"{prefix}_"):
                emotion = sentiment[len(prefix) + 1 :]
                break

        self.assertEqual(emotion, "curiosa")
        assert emotion == "curiosa"


class TestFormatSentimentText(unittest.TestCase):
    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_luna_feminine(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "luna"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Luna", "gender": "feminine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Luna_curiosa")

        self.assertEqual(result, "Luna está curiosa")
        assert "curiosa" in result

    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_mars_masculine(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "mars"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Mars", "gender": "masculine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Mars_curiosa")

        self.assertEqual(result, "Mars está curioso")
        self.assertNotIn("Mars_", result)
        assert "curioso" in result

    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_lars_masculine_irritado(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "lars"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Lars", "gender": "masculine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Lars_irritada")

        self.assertEqual(result, "Lars está irritado")
        assert "irritado" in result

    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_juno_feminine_apaixonada(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "juno"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Juno", "gender": "feminine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Juno_apaixonada")

        self.assertEqual(result, "Juno está apaixonada")
        assert "apaixonada" in result

    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_unknown_emotion_passthrough(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "luna"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Luna", "gender": "feminine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Luna_meditando")

        self.assertEqual(result, "Luna está meditando")
        assert "meditando" in result


class TestNoNameDuplication(unittest.TestCase):
    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_no_mars_duplication(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "mars"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Mars", "gender": "masculine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Mars_curiosa")

        mars_count = result.count("Mars")
        self.assertEqual(mars_count, 1)
        self.assertNotIn("Mars Mars", result)
        self.assertNotIn("Mars_", result)
        assert mars_count == 1

    @patch("src.ui.emotion_manager.get_active_entity")
    @patch("src.ui.emotion_manager.EntityLoader")
    def test_no_luna_duplication(self, mock_loader_class, mock_get_entity):
        from src.ui.emotion_manager import EmotionLabelManager

        mock_get_entity.return_value = "luna"
        mock_loader = MagicMock()
        mock_loader.get_config.return_value = {"name": "Luna", "gender": "feminine"}
        mock_loader_class.return_value = mock_loader

        manager = EmotionLabelManager(MagicMock())
        result = manager._format_sentiment_text("Luna_feliz")

        luna_count = result.count("Luna")
        self.assertEqual(luna_count, 1)
        assert luna_count == 1


class TestEmotionLabelManagerInit(unittest.TestCase):
    def test_init(self):
        from src.ui.emotion_manager import EmotionLabelManager

        app = MagicMock()
        manager = EmotionLabelManager(app)

        self.assertEqual(manager.app, app)
        self.assertEqual(manager._current_sentiment, "observando")
        self.assertIsNone(manager._widget)
        assert manager._current_sentiment == "observando"

    def test_update_sentiment_same_no_change(self):
        from src.ui.emotion_manager import EmotionLabelManager

        app = MagicMock()
        manager = EmotionLabelManager(app)
        manager._current_sentiment = "curiosa"

        with patch.object(manager, "_format_sentiment_text") as mock_format:
            manager.update_sentiment("curiosa")
            mock_format.assert_not_called()
            assert not mock_format.called


if __name__ == "__main__":
    unittest.main()
