from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestMood:
    def test_mood_values(self):
        from src.soul.personality_anchor import Mood

        assert Mood.NEUTRAL.value == "neutral"
        assert Mood.HAPPY.value == "happy"
        assert Mood.SAD.value == "sad"
        assert Mood.TIRED.value == "tired"


class TestPersonalityState:
    def test_default_values(self):
        from src.soul.personality_anchor import Mood, PersonalityState

        state = PersonalityState()

        assert state.mood == Mood.NEUTRAL
        assert state.energy == 0.8
        assert state.interaction_count == 0
        assert state.drift_score == 0.0


class TestPersonalityAnchor:
    @patch("src.soul.personality_anchor.EntityLoader")
    def test_initialization(self, mock_loader):
        from src.soul.personality_anchor import Mood, PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")

        assert anchor.entity_id == "luna"
        assert anchor.state.mood == Mood.NEUTRAL
        assert anchor.state.energy == 0.8

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_needs_reinforcement_initial(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.last_reinforcement = datetime.now() - timedelta(minutes=15)

        assert anchor.needs_reinforcement() is True

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_needs_reinforcement_recent(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.last_reinforcement = datetime.now()

        assert anchor.needs_reinforcement() is False

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_get_anchor_injection_when_needed(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.last_reinforcement = datetime.now() - timedelta(minutes=15)

        injection = anchor.get_anchor_injection()

        assert len(injection) > 0
        assert "Luna" in injection or "IDENTIDADE" in injection

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_get_anchor_injection_when_not_needed(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.last_reinforcement = datetime.now()

        injection = anchor.get_anchor_injection()

        assert injection == ""

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_check_response_drift_clean(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")

        result = anchor.check_response_drift("Oi, mortal. O que deseja?")

        assert result["drifted"] is False
        assert len(result["violations"]) == 0

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_check_response_drift_violation(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")

        result = anchor.check_response_drift("Como IA, nao posso fazer isso.")

        assert result["drifted"] is True
        assert len(result["violations"]) > 0

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_update_from_interaction_energy_decay(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        initial_energy = anchor.state.energy

        anchor.update_from_interaction()
        anchor.update_from_interaction()
        anchor.update_from_interaction()

        assert anchor.state.energy < initial_energy
        assert anchor.state.interaction_count == 3

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_update_from_interaction_mood_change(self, mock_loader):
        from src.soul.personality_anchor import Mood, PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")

        anchor.update_from_interaction(user_sentiment=0.8)
        assert anchor.state.mood == Mood.HAPPY

        anchor.update_from_interaction(user_sentiment=-0.8)
        assert anchor.state.mood == Mood.SAD

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_restore_energy(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.energy = 0.5

        anchor.restore_energy(0.3)

        assert anchor.state.energy == 0.8

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_restore_energy_max(self, mock_loader):
        from src.soul.personality_anchor import PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.energy = 0.9

        anchor.restore_energy(0.5)

        assert anchor.state.energy == 1.0

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_reset(self, mock_loader):
        from src.soul.personality_anchor import Mood, PersonalityAnchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        anchor = PersonalityAnchor("luna")
        anchor.state.energy = 0.3
        anchor.state.mood = Mood.TIRED
        anchor.state.interaction_count = 50

        anchor.reset()

        assert anchor.state.energy == 0.8
        assert anchor.state.mood == Mood.NEUTRAL
        assert anchor.state.interaction_count == 0


class TestGetPersonalityAnchor:
    @patch("src.soul.personality_anchor.EntityLoader")
    def test_returns_same_instance(self, mock_loader):
        from src.soul.personality_anchor import _anchors, get_personality_anchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        _anchors.clear()

        a1 = get_personality_anchor("test_luna")
        a2 = get_personality_anchor("test_luna")

        assert a1 is a2

    @patch("src.soul.personality_anchor.EntityLoader")
    def test_different_entities(self, mock_loader):
        from src.soul.personality_anchor import _anchors, get_personality_anchor

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Entity", "persona": {}}
        mock_loader.return_value = mock_instance

        _anchors.clear()

        luna = get_personality_anchor("test_luna2")
        eris = get_personality_anchor("test_eris")

        assert luna is not eris
        assert luna.entity_id == "test_luna2"
        assert eris.entity_id == "test_eris"


class TestSwitchPersonalityAnchor:
    @patch("src.soul.personality_anchor.EntityLoader")
    def test_switch_returns_anchor(self, mock_loader):
        from src.soul.personality_anchor import (
            PersonalityAnchor,
            _anchors,
            switch_personality_anchor,
        )

        mock_instance = MagicMock()
        mock_instance.get_config.return_value = {"name": "Luna", "persona": {}}
        mock_loader.return_value = mock_instance

        _anchors.clear()

        anchor = switch_personality_anchor("test_switch")

        assert isinstance(anchor, PersonalityAnchor)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
