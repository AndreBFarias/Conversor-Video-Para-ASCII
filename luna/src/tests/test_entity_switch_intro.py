import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestEntitySwitchDialoguesInit:
    def test_creates_empty_steps(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            assert dialogues.steps == {}
            assert dialogues.entity_id == "luna"

    def test_stores_entity_id(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("eris")

            assert dialogues.entity_id == "eris"


class TestEntitySwitchDialoguesParseVariacoes:
    def test_empty_string(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues._parse_variacoes("")

            assert result == [""]

    def test_single_phrase(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues._parse_variacoes("Ola $N")

            assert result == ["Ola $N"]

    def test_multiple_variations(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues._parse_variacoes("Oi $N|Ola $N|E ai $N")

            assert len(result) == 3
            assert "Oi $N" in result
            assert "Ola $N" in result
            assert "E ai $N" in result

    def test_strips_whitespace(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues._parse_variacoes("  Oi  |  Ola  ")

            assert result == ["Oi", "Ola"]

    def test_removes_quotes(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues._parse_variacoes('"Oi mundo"')

            assert result == ["Oi mundo"]


class TestEntitySwitchDialoguesGetFrase:
    def test_returns_empty_for_missing_step(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")

            result = dialogues.get_frase(99)

            assert result == ""

    def test_replaces_name_placeholder(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")
            dialogues.steps[1] = {"variacoes": ["Ola $N, bem-vindo!"], "programa": ""}

            result = dialogues.get_frase(1, "test_user")

            assert "test_user" in result
            assert "$N" not in result

    def test_replaces_nome_dele_placeholder(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")
            dialogues.steps[1] = {"variacoes": ["O nome dele e $NOME_DELE"], "programa": ""}

            result = dialogues.get_frase(1, "test_user")

            assert "test_user" in result
            assert "$NOME_DELE" not in result

    def test_replaces_entity_placeholder(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("eris")
            dialogues.steps[1] = {"variacoes": ["Eu sou $E"], "programa": ""}

            result = dialogues.get_frase(1)

            assert "Eris" in result
            assert "$E" not in result

    def test_replaces_entidade_placeholder(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("juno")
            dialogues.steps[1] = {"variacoes": ["Meu nome e $ENTIDADE"], "programa": ""}

            result = dialogues.get_frase(1)

            assert "Juno" in result
            assert "$ENTIDADE" not in result

    def test_default_name(self):
        with patch("src.soul.entity_switch.SWITCH_CSV_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchDialogues

            dialogues = EntitySwitchDialogues("luna")
            dialogues.steps[1] = {"variacoes": ["Ola $N"], "programa": ""}

            result = dialogues.get_frase(1)

            assert "Viajante" in result


class TestEntitySwitchIntroInit:
    def test_creates_instance(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            app = MagicMock()
            intro = EntitySwitchIntro(app)

            assert intro.app == app
            assert intro.is_running is False

    def test_loads_user_name_default(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            assert intro.user_name == "Viajante"


class TestEntitySwitchIntroGetUserName:
    def test_returns_default_when_no_file(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro._get_user_name()

            assert result == "Viajante"

    def test_returns_name_from_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"nome": "test_user"}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro._get_user_name()

                assert result == "test_user"


class TestEntitySwitchIntroGetLastEntity:
    def test_returns_none_when_no_file(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro._get_last_entity()

            assert result is None

    def test_returns_entity_from_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"active_entity": "eris"}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro._get_last_entity()

                assert result == "eris"


class TestEntitySwitchIntroGetKnownEntities:
    def test_returns_empty_when_no_file(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro._get_known_entities()

            assert result == []

    def test_returns_list_from_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"known_entities": ["luna", "eris"]}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro._get_known_entities()

                assert result == ["luna", "eris"]


class TestEntitySwitchIntroIsFirstMeeting:
    def test_returns_true_for_unknown(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro.is_first_meeting("juno")

            assert result is True

    def test_returns_false_for_known(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"known_entities": ["luna", "eris"]}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro.is_first_meeting("eris")

                assert result is False


class TestEntitySwitchIntroNeedsIntro:
    def test_returns_true_for_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"pending_entity_intro": "juno"}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro.needs_intro("juno")

                assert result is True

    def test_returns_true_for_first_meeting(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro.needs_intro("new_entity")

            assert result is True

    def test_returns_false_for_known_no_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"known_entities": ["luna", "eris"]}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro.needs_intro("luna")

                assert result is False


class TestEntitySwitchIntroGetVoicePreference:
    def test_returns_true_default(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            intro = EntitySwitchIntro(MagicMock())

            result = intro._get_voice_preference()

            assert result is True

    def test_returns_preference_from_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"preferencias": {"permite_voz": False}}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())

                result = intro._get_voice_preference()

                assert result is False


class TestEntitySwitchIntroActivateVoiceMode:
    def test_sets_em_chamada(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            app = MagicMock()
            app.em_chamada = False
            intro = EntitySwitchIntro(app)

            intro._activate_voice_mode()

            assert app.em_chamada is True

    def test_handles_missing_attribute(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import EntitySwitchIntro

            app = MagicMock(spec=[])
            intro = EntitySwitchIntro(app)

            result = intro._activate_voice_mode()
            assert result is None


class TestEntitySwitchIntroSaveKnownEntity:
    def test_saves_new_entity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())
                intro._save_known_entity("juno")

                with open(profile_path) as f:
                    data = json.load(f)

                assert "juno" in data.get("known_entities", [])
                assert data.get("active_entity") == "juno"

    def test_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"known_entities": ["luna"]}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())
                intro._save_known_entity("luna")

                with open(profile_path) as f:
                    data = json.load(f)

                assert data["known_entities"].count("luna") == 1


class TestEntitySwitchIntroClearPendingIntro:
    def test_removes_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            with open(profile_path, "w") as f:
                json.dump({"pending_entity_intro": "eris"}, f)

            with patch("src.soul.entity_switch.PROFILE_PATH", profile_path):
                from src.soul.entity_switch import EntitySwitchIntro

                intro = EntitySwitchIntro(MagicMock())
                intro._clear_pending_intro()

                with open(profile_path) as f:
                    data = json.load(f)

                assert "pending_entity_intro" not in data


class TestGetEntitySwitchIntro:
    def test_returns_instance(self):
        with patch("src.soul.entity_switch.PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False

            from src.soul.entity_switch import get_entity_switch_intro

            app = MagicMock()
            result = get_entity_switch_intro(app)

            assert result is not None
            assert result.app == app
