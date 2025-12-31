from unittest.mock import patch


class TestEntityMarkers:
    def test_luna_markers_exist(self):
        from src.soul.personality_guard import ENTITY_MARKERS

        assert "luna" in ENTITY_MARKERS
        assert "positive" in ENTITY_MARKERS["luna"]
        assert "negative" in ENTITY_MARKERS["luna"]
        assert "forbidden_phrases" in ENTITY_MARKERS["luna"]

    def test_all_entities_have_markers(self):
        from src.soul.personality_guard import ENTITY_MARKERS

        expected_entities = ["luna", "eris", "juno", "lars", "mars", "somn"]
        for entity in expected_entities:
            assert entity in ENTITY_MARKERS, f"Missing markers for {entity}"

    def test_luna_positive_markers(self):
        from src.soul.personality_guard import ENTITY_MARKERS

        luna_positive = ENTITY_MARKERS["luna"]["positive"]
        assert "sombra" in luna_positive
        assert "gotic" in luna_positive


class TestPersonalityGuardInit:
    @patch("src.soul.personality_guard.EntityLoader")
    def test_init_luna(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        assert guard.entity_id == "luna"
        assert guard._violation_count == 0
        assert guard.markers is not None

    @patch("src.soul.personality_guard.EntityLoader")
    def test_init_unknown_entity(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("unknown_entity")
        assert guard.entity_id == "unknown_entity"
        assert guard.markers == {}

    @patch("src.soul.personality_guard.EntityLoader")
    def test_init_eris(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("eris")
        assert guard.entity_id == "eris"
        assert "caos" in guard.markers.get("positive", [])


class TestPersonalityGuardCheckResponse:
    @patch("src.soul.personality_guard.EntityLoader")
    def test_check_response_clean(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        result = guard.check_response("Uma resposta normal e gotica nas sombras")

        assert "score" in result
        assert "issues" in result
        assert result["score"] > 0

    @patch("src.soul.personality_guard.EntityLoader")
    def test_check_response_forbidden_phrase(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        result = guard.check_response("chaos e minha natureza")

        assert result["score"] < 1.0
        assert len(result["issues"]) > 0
        assert any("Forbidden phrase" in issue for issue in result["issues"])

    @patch("src.soul.personality_guard.EntityLoader")
    def test_check_response_negative_markers(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        result = guard.check_response("Sou uma diva narcisista do caos guerreira alpha")

        assert result["score"] < 1.0
        assert any("foreign markers" in issue.lower() for issue in result["issues"])

    @patch("src.soul.personality_guard.EntityLoader")
    def test_check_response_no_positive_markers(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        long_text = "a" * 150
        result = guard.check_response(long_text)

        assert any("No personality markers" in issue for issue in result["issues"])

    @patch("src.soul.personality_guard.EntityLoader")
    def test_check_response_with_positive_markers(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        result = guard.check_response("Nas sombras do misterio gotico, sussurro segredos sedutores")

        assert result["score"] >= 0.9
        assert len(result["issues"]) == 0

    @patch("src.soul.personality_guard.EntityLoader")
    def test_violation_count_increments(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        assert guard._violation_count == 0

        guard.check_response("chaos e minha natureza sou a mais poderosa")
        assert guard._violation_count == 1


class TestPersonalityGuardMethods:
    @patch("src.soul.personality_guard.EntityLoader")
    def test_fix_response_exists(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard = PersonalityGuard("luna")
        assert hasattr(guard, "check_response")

    @patch("src.soul.personality_guard.EntityLoader")
    def test_different_entity_markers(self, mock_loader):
        from src.soul.personality_guard import PersonalityGuard

        guard_luna = PersonalityGuard("luna")
        guard_eris = PersonalityGuard("eris")

        assert guard_luna.markers != guard_eris.markers
        assert "sombra" in guard_luna.markers.get("positive", [])
        assert "caos" in guard_eris.markers.get("positive", [])


class TestGetPersonalityGuard:
    @patch("src.soul.personality_guard.EntityLoader")
    def test_get_personality_guard_returns_instance(self, mock_loader):
        from src.soul.personality_guard import get_personality_guard

        guard = get_personality_guard("luna")
        assert guard is not None
        assert guard.entity_id == "luna"

    @patch("src.soul.personality_guard.EntityLoader")
    def test_get_personality_guard_caches_instance(self, mock_loader):
        from src.soul.personality_guard import get_personality_guard

        guard1 = get_personality_guard("luna")
        guard2 = get_personality_guard("luna")

        assert guard1 is guard2
