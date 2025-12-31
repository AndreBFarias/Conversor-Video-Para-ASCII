from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_consciencia():
    mock = MagicMock()
    mock.active_entity_id = "luna"
    mock.smart_memory = MagicMock()
    mock.smart_memory.retrieve.return_value = "contexto de teste"
    mock.smart_memory.get_user_profile_context.return_value = "perfil do usuario"
    mock.smart_memory._memories = []
    mock.global_memory = MagicMock()
    mock.short_term_memory = MagicMock()
    mock.memory_tier_manager = MagicMock()
    mock.memory_tier_manager.promote_all_eligible.return_value = {"short_to_mid": 2}
    mock._interaction_count = 0
    mock.proactive_recall = None
    return mock


class TestMemoryControllerInit:
    def test_creates_controller(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)

        assert controller._consciencia == mock_consciencia
        assert controller._proactive_recall is None

    def test_properties(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)

        assert controller.smart_memory == mock_consciencia.smart_memory
        assert controller.global_memory == mock_consciencia.global_memory


class TestMemoryControllerWarmup:
    def test_warmup_success(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        with patch("src.soul.consciencia.services.memory_controller.run_startup_warmup") as mock_warmup:
            mock_warmup.return_value = {"total_time_ms": 100}
            with patch("src.soul.consciencia.services.memory_controller.get_proactive_recall") as mock_recall:
                mock_recall.return_value = MagicMock()

                controller = MemoryController(mock_consciencia)
                result = controller.warmup()

                assert result["total_time_ms"] == 100
                assert controller._proactive_recall is not None

    def test_warmup_error(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        with patch("src.soul.consciencia.services.memory_controller.run_startup_warmup") as mock_warmup:
            mock_warmup.side_effect = Exception("Erro de warmup")

            controller = MemoryController(mock_consciencia)
            result = controller.warmup()

            assert "error" in result
            assert controller._proactive_recall is None


class TestMemoryControllerBuildContext:
    def test_build_context_basic(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        context = controller.build_context("Qual meu nome?")

        assert "perfil do usuario" in context
        assert "contexto de teste" in context

    def test_build_context_with_proactive(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        controller._proactive_recall = MagicMock()
        controller._proactive_recall.find_relevant_memory.return_value = {"trigger_type": "date"}
        controller._proactive_recall.format_recall_prompt.return_value = "proactive context"

        context = controller.build_context("Qual meu nome?")

        assert "proactive context" in context

    def test_build_context_empty(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        mock_consciencia.smart_memory.retrieve.return_value = ""
        mock_consciencia.smart_memory.get_user_profile_context.return_value = ""

        controller = MemoryController(mock_consciencia)
        context = controller.build_context("Oi")

        assert context == ""

    def test_build_context_error(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        mock_consciencia.smart_memory.retrieve.side_effect = Exception("DB error")

        controller = MemoryController(mock_consciencia)
        context = controller.build_context("test")

        assert context == ""


class TestMemoryControllerSaveInteraction:
    def test_save_interaction_user_text(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        controller.save_interaction("Esta e uma mensagem longa do usuario", {"fala_tts": "Resposta"})

        mock_consciencia.smart_memory.add.assert_called()

    def test_save_interaction_short_text_ignored(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        controller.save_interaction("Oi", {"fala_tts": ""})

        mock_consciencia.smart_memory.add.assert_not_called()

    def test_save_interaction_response(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        controller.save_interaction(
            "Mensagem longa do usuario para teste",
            {"fala_tts": "Esta e uma resposta longa da entidade para salvar"},
        )

        assert mock_consciencia.smart_memory.add.call_count == 2


class TestMemoryControllerUpdateTiers:
    def test_update_tiers_basic(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        controller.update_tiers("user input", {"fala_tts": "response"})

        assert mock_consciencia.short_term_memory.add.call_count == 2

    def test_update_tiers_promotes_at_interval(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        mock_consciencia._interaction_count = 10

        controller = MemoryController(mock_consciencia)
        controller.update_tiers("user input", {"fala_tts": "response"})

        mock_consciencia.memory_tier_manager.promote_all_eligible.assert_called_once()


class TestMemoryControllerReload:
    def test_reload_for_entity(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        with patch("src.soul.consciencia.services.memory_controller.get_entity_smart_memory") as mock_mem:
            with patch("src.soul.consciencia.services.memory_controller.get_smart_memory") as mock_global:
                with patch("src.soul.consciencia.services.memory_controller.get_proactive_recall") as mock_recall:
                    mock_mem.return_value = MagicMock()
                    mock_global.return_value = MagicMock()
                    mock_recall.return_value = MagicMock()

                    controller = MemoryController(mock_consciencia)
                    controller.reload_for_entity("eris")

                    mock_mem.assert_called_with("eris")
                    assert mock_consciencia.active_entity_id == "eris"


class TestMemoryControllerStats:
    def test_get_stats(self, mock_consciencia):
        from src.soul.consciencia.services import MemoryController

        controller = MemoryController(mock_consciencia)
        stats = controller.get_stats()

        assert stats["entity_id"] == "luna"
        assert "smart_memory_size" in stats
        assert stats["proactive_enabled"] is False
