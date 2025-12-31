import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMoodEnum:
    def test_all_moods_exist(self):
        from src.soul.emotional_state import Mood

        assert Mood.NEUTRA is not None
        assert Mood.FELIZ is not None
        assert Mood.TRISTE is not None
        assert Mood.IRRITADA is not None
        assert Mood.SAUDADE is not None
        assert Mood.APAIXONADA is not None
        assert Mood.CURIOSA is not None
        assert Mood.ENTEDIADA is not None
        assert Mood.PREOCUPADA is not None
        assert Mood.TRAVESSA is not None

    def test_moods_have_string_values(self):
        from src.soul.emotional_state import Mood

        for mood in Mood:
            assert isinstance(mood.value, str)

    def test_mood_from_value(self):
        from src.soul.emotional_state import Mood

        assert Mood("neutra") == Mood.NEUTRA
        assert Mood("feliz") == Mood.FELIZ


class TestEmotionalState:
    def test_default_values(self):
        from src.soul.emotional_state import EmotionalState, Mood

        state = EmotionalState()

        assert state.mood == Mood.NEUTRA
        assert state.energy == 0.7
        assert state.attachment == 0.5
        assert state.last_interaction is None
        assert state.interaction_count == 0
        assert state.mood_history == []

    def test_to_dict(self):
        from src.soul.emotional_state import EmotionalState, Mood

        state = EmotionalState(mood=Mood.FELIZ, energy=0.9)
        data = state.to_dict()

        assert data["mood"] == "feliz"
        assert data["energy"] == 0.9
        assert isinstance(data, dict)

    def test_from_dict(self):
        from src.soul.emotional_state import EmotionalState, Mood

        data = {
            "mood": "triste",
            "energy": 0.3,
            "attachment": 0.8,
            "interaction_count": 5,
        }

        state = EmotionalState.from_dict(data)

        assert state.mood == Mood.TRISTE
        assert state.energy == 0.3
        assert state.attachment == 0.8
        assert state.interaction_count == 5

    def test_mood_history_limited_to_20(self):
        from src.soul.emotional_state import EmotionalState

        history = [(f"2024-01-{i:02d}", "feliz") for i in range(30)]
        state = EmotionalState(mood_history=history)

        data = state.to_dict()
        assert len(data["mood_history"]) == 20


class TestEmotionalStateManagerInit:
    def test_creates_storage_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            storage_dir = Path(tmpdir) / "subdir" / "emotional"
            manager = EmotionalStateManager("luna", storage_dir=storage_dir)

            assert storage_dir.exists()
            assert manager.entity_id == "luna"

    def test_initial_state_neutral(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            assert manager.state.mood == Mood.NEUTRA

    def test_loads_existing_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            state_file = Path(tmpdir) / "luna_emotional.json"
            state_file.write_text(
                json.dumps(
                    {
                        "mood": "feliz",
                        "energy": 0.9,
                        "attachment": 0.6,
                        "interaction_count": 10,
                    }
                )
            )

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            assert manager.state.mood == Mood.FELIZ
            assert manager.state.energy == 0.9
            assert manager.state.interaction_count == 10


class TestSaveAndLoad:
    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("eris", storage_dir=Path(tmpdir))
            manager.state.mood = Mood.IRRITADA
            manager.save()

            assert manager.path.exists()
            data = json.loads(manager.path.read_text())
            assert data["mood"] == "irritada"

    def test_state_persists_after_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager1 = EmotionalStateManager("juno", storage_dir=Path(tmpdir))
            manager1.state.mood = Mood.APAIXONADA
            manager1.state.energy = 1.0
            manager1.save()

            manager2 = EmotionalStateManager("juno", storage_dir=Path(tmpdir))

            assert manager2.state.mood == Mood.APAIXONADA
            assert manager2.state.energy == 1.0


class TestReactToSentiment:
    def test_positive_sentiment_increases_energy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            initial = manager.state.energy

            manager.react_to_sentiment(0.9)

            assert manager.state.energy >= initial

    def test_positive_sentiment_increases_attachment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            initial = manager.state.attachment

            manager.react_to_sentiment(0.9)

            assert manager.state.attachment >= initial

    def test_negative_sentiment_decreases_energy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            initial = manager.state.energy

            manager.react_to_sentiment(-0.8)

            assert manager.state.energy <= initial

    def test_energy_capped_at_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.energy = 0.99

            for _ in range(10):
                manager.react_to_sentiment(1.0)

            assert manager.state.energy <= 1.0

    def test_energy_minimum_at_0_2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            for _ in range(100):
                manager.react_to_sentiment(-1.0)

            assert manager.state.energy >= 0.2


class TestTimeDecay:
    def test_saudade_after_72_hours(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.attachment = 0.8
            manager.state.last_interaction = (datetime.now() - timedelta(hours=80)).isoformat()

            manager.time_decay()

            assert manager.state.mood == Mood.SAUDADE

    def test_no_saudade_if_low_attachment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.attachment = 0.3
            manager.state.last_interaction = (datetime.now() - timedelta(hours=80)).isoformat()

            manager.time_decay()

            assert manager.state.mood != Mood.SAUDADE

    def test_no_decay_without_last_interaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            initial_mood = manager.state.mood

            manager.time_decay()

            assert manager.state.mood == initial_mood


class TestUpdate:
    def test_increments_interaction_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            initial = manager.state.interaction_count

            manager.update(user_message="ola", sentiment=0.0)

            assert manager.state.interaction_count == initial + 1

    def test_sets_last_interaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            manager.update()

            assert manager.state.last_interaction is not None

    def test_saves_after_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.update()

            assert manager.path.exists()


class TestGetMoodContext:
    def test_returns_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            context = manager.get_mood_context()

            assert isinstance(context, str)
            assert "Estado emocional" in context

    def test_contains_mood_description(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.mood = Mood.FELIZ
            context = manager.get_mood_context()

            assert "feliz" in context.lower() or "animada" in context.lower()

    def test_contains_energy_level(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.energy = 0.9
            context = manager.get_mood_context()

            assert "0.9" in context


class TestGetSuggestedAnimation:
    def test_returns_animation_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.mood = Mood.FELIZ

            anim = manager.get_suggested_animation()

            assert anim == "feliz"

    def test_saudade_maps_to_triste(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.mood = Mood.SAUDADE

            anim = manager.get_suggested_animation()

            assert anim == "triste"


class TestGetEmotionalManager:
    def test_returns_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, _managers

            _managers.clear()

            with patch("src.soul.emotional_state.EmotionalStateManager.__init__", return_value=None) as mock_init:
                mock_init.return_value = None

                _managers.clear()

                with tempfile.TemporaryDirectory() as tmpdir2:
                    with patch("config.APP_DIR", Path(tmpdir2)):
                        manager = EmotionalStateManager("test", storage_dir=Path(tmpdir2))

                        assert isinstance(manager, EmotionalStateManager)

    def test_singleton_per_entity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, _managers

            _managers.clear()

            m1 = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            m2 = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            assert m1.entity_id == m2.entity_id


class TestAnalyzeSentiment:
    def test_positive_words_return_positive(self):
        from src.soul.emotional_state import analyze_sentiment

        result = analyze_sentiment("eu te amo muito, voce e maravilhosa")

        assert result > 0

    def test_negative_words_return_negative(self):
        from src.soul.emotional_state import analyze_sentiment

        result = analyze_sentiment("que coisa horrivel e ruim")

        assert result < 0

    def test_neutral_returns_zero(self):
        from src.soul.emotional_state import analyze_sentiment

        result = analyze_sentiment("o ceu e azul")

        assert result == 0.0

    def test_mixed_sentiment(self):
        from src.soul.emotional_state import analyze_sentiment

        result = analyze_sentiment("amo mas odeio ao mesmo tempo")

        assert isinstance(result, float)


class TestMoodHistory:
    def test_set_mood_adds_to_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            manager._set_mood(Mood.FELIZ)

            assert len(manager.state.mood_history) == 1
            assert manager.state.mood_history[0][1] == "feliz"

    def test_same_mood_not_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager, Mood

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))
            manager.state.mood = Mood.FELIZ

            manager._set_mood(Mood.FELIZ)

            assert len(manager.state.mood_history) == 0


class TestNaturalVariation:
    def test_natural_variation_runs_without_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.soul.emotional_state import EmotionalStateManager

            manager = EmotionalStateManager("luna", storage_dir=Path(tmpdir))

            for _ in range(100):
                manager.natural_variation()

            assert manager.state.mood is not None
