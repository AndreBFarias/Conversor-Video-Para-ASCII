from pathlib import Path
from unittest.mock import MagicMock, patch


class TestEntityHotSwapInit:
    def test_creates_instance(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()

            assert hotswap.current_entity is None
            assert hotswap._loaders == {}
            assert hotswap._swap_history == []

    def test_initializes_cross_memory(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_instance = MagicMock()
            mock_mem.return_value = mock_instance

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()

            assert hotswap.cross_memory == mock_instance


class TestEntityHotSwapInitialize:
    def test_sets_current_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_loader.return_value = MagicMock()

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()
                hotswap.initialize("luna")

                assert hotswap.current_entity == "luna"

    def test_creates_loader(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_loader.return_value = MagicMock()

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()
                hotswap.initialize("eris")

                assert "eris" in hotswap._loaders


class TestEntityHotSwapGetLoader:
    def test_caches_loader(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()

                loader1 = hotswap._get_loader("luna")
                loader2 = hotswap._get_loader("luna")

                assert loader1 is loader2
                mock_loader.assert_called_once()


class TestEntityHotSwapEntityDir:
    def test_returns_none_without_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()

            assert hotswap.entity_dir is None


class TestEntityHotSwapConfig:
    def test_returns_none_without_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()

            assert hotswap.config is None


class TestEntityHotSwapCanSwapTo:
    def test_returns_dict_with_checks(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_instance.entity_data = {"animations_dir": Path("/tmp/test")}
                mock_instance.get_soul_prompt.return_value = "Test prompt"
                mock_instance.get_config.return_value = {"name": "Test"}
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()

                result = hotswap.can_swap_to("luna")

                assert "can_swap" in result
                assert "checks" in result
                assert "target" in result

    def test_checks_entity_exists(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_instance.entity_data = {"animations_dir": None}
                mock_instance.get_soul_prompt.return_value = None
                mock_instance.get_config.return_value = None
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()

                result = hotswap.can_swap_to("nonexistent")

                assert result["can_swap"] is False


class TestEntityHotSwapSwap:
    def test_returns_success_if_same_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()
            hotswap.current_entity = "luna"

            result = hotswap.swap("luna")

            assert result["success"] is True
            assert "Already" in result["message"]

    def test_returns_error_if_cannot_swap(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_instance.entity_data = {"animations_dir": None}
                mock_instance.get_soul_prompt.return_value = None
                mock_instance.get_config.return_value = None
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()
                hotswap.current_entity = "luna"

                result = hotswap.swap("nonexistent")

                assert result["success"] is False

    def test_successful_swap(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                with patch("src.soul.entity_hotswap.update_json_safe"):
                    with patch("src.soul.entity_hotswap.PROFILE_PATH", Path("/tmp/test_profile.json")):
                        mock_mem.return_value = MagicMock()
                        mock_instance = MagicMock()
                        mock_instance.entity_data = {"animations_dir": Path("/tmp")}
                        mock_instance.get_soul_prompt.return_value = "Test"
                        mock_instance.get_config.return_value = {"name": "Test"}
                        mock_loader.return_value = mock_instance

                        from src.soul.entity_hotswap import EntityHotSwap

                        hotswap = EntityHotSwap()
                        hotswap.current_entity = "luna"

                        result = hotswap.swap("eris", reason="test")

                        assert result["success"] is True
                        assert result["from"] == "luna"
                        assert result["to"] == "eris"


class TestEntityHotSwapGetTransitionPrompt:
    def test_returns_prompt(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_instance.get_config.return_value = {"name": "Test Entity"}
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()

                result = hotswap.get_transition_prompt("luna", "eris")

                assert "Test Entity" in result
                assert "despede" in result


class TestEntityHotSwapGetCurrentLoader:
    def test_returns_none_without_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()

            assert hotswap.get_current_loader() is None

    def test_returns_loader_with_entity(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_instance = MagicMock()
                mock_loader.return_value = mock_instance

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()
                hotswap.initialize("luna")

                result = hotswap.get_current_loader()

                assert result is not None


class TestEntityHotSwapGetSwapHistory:
    def test_returns_copy(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            from src.soul.entity_hotswap import EntityHotSwap

            hotswap = EntityHotSwap()
            hotswap._swap_history = [{"test": "data"}]

            result = hotswap.get_swap_history()

            assert result == [{"test": "data"}]
            assert result is not hotswap._swap_history


class TestEntityHotSwapPreloadEntity:
    def test_preloads_without_error(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            with patch("src.soul.entity_hotswap.EntityLoader") as mock_loader:
                mock_mem.return_value = MagicMock()
                mock_loader.return_value = MagicMock()

                from src.soul.entity_hotswap import EntityHotSwap

                hotswap = EntityHotSwap()

                hotswap.preload_entity("juno")

                assert "juno" in hotswap._loaders


class TestGetEntityHotswapSingleton:
    def test_returns_singleton(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            import src.soul.entity_hotswap as module

            module._hotswap_instance = None

            from src.soul.entity_hotswap import get_entity_hotswap

            h1 = get_entity_hotswap()
            h2 = get_entity_hotswap()

            assert h1 is h2


class TestResetHotswap:
    def test_resets_singleton(self):
        with patch("src.soul.entity_hotswap.get_cross_entity_memory") as mock_mem:
            mock_mem.return_value = MagicMock()

            import src.soul.entity_hotswap as module

            module._hotswap_instance = MagicMock()

            from src.soul.entity_hotswap import reset_hotswap

            reset_hotswap()

            assert module._hotswap_instance is None
