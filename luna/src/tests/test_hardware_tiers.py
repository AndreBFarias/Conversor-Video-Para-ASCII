from unittest.mock import MagicMock, patch


class TestHardwareTier:
    def test_all_tiers_exist(self):
        from src.core.hardware_tiers import HardwareTier

        assert HardwareTier.PREMIUM is not None
        assert HardwareTier.BALANCED is not None
        assert HardwareTier.LIGHT is not None
        assert HardwareTier.MINIMAL is not None

    def test_tier_values(self):
        from src.core.hardware_tiers import HardwareTier

        assert HardwareTier.PREMIUM.value == "premium"
        assert HardwareTier.BALANCED.value == "balanced"
        assert HardwareTier.LIGHT.value == "light"
        assert HardwareTier.MINIMAL.value == "minimal"


class TestHardwareInfo:
    def test_default_values(self):
        from src.core.hardware_tiers import HardwareInfo

        info = HardwareInfo()

        assert info.gpu_name is None
        assert info.gpu_vram_gb == 0.0
        assert info.ram_gb == 0.0
        assert info.cpu_cores == 1
        assert info.has_cuda is False

    def test_custom_values(self):
        from src.core.hardware_tiers import HardwareInfo

        info = HardwareInfo(
            gpu_name="RTX 3050",
            gpu_vram_gb=4.0,
            ram_gb=16.0,
            cpu_cores=8,
            has_cuda=True,
        )

        assert info.gpu_name == "RTX 3050"
        assert info.gpu_vram_gb == 4.0
        assert info.has_cuda is True

    def test_to_dict(self):
        from src.core.hardware_tiers import HardwareInfo

        info = HardwareInfo(gpu_name="RTX 3050", gpu_vram_gb=4.0, ram_gb=16.0)
        data = info.to_dict()

        assert data["gpu_name"] == "RTX 3050"
        assert data["gpu_vram_gb"] == 4.0
        assert data["ram_gb"] == 16.0


class TestTierConfig:
    def test_creation(self):
        from src.core.hardware_tiers import HardwareTier, TierConfig

        config = TierConfig(
            tier=HardwareTier.PREMIUM,
            llm_model="mistral:7b",
            llm_provider="ollama",
            tts_engine="xtts",
            stt_model="medium",
            use_gpu=True,
            max_context=8192,
        )

        assert config.tier == HardwareTier.PREMIUM
        assert config.llm_model == "mistral:7b"
        assert config.use_gpu is True

    def test_to_dict(self):
        from src.core.hardware_tiers import HardwareTier, TierConfig

        config = TierConfig(
            tier=HardwareTier.BALANCED,
            llm_model="phi3:mini",
            llm_provider="ollama",
            tts_engine="xtts",
            stt_model="small",
            use_gpu=True,
            max_context=4096,
        )

        data = config.to_dict()

        assert data["tier"] == "balanced"
        assert data["llm"]["model"] == "phi3:mini"
        assert data["tts"]["engine"] == "xtts"


class TestTierConfigs:
    def test_all_tiers_have_config(self):
        from src.core.hardware_tiers import TIER_CONFIGS, HardwareTier

        for tier in HardwareTier:
            assert tier in TIER_CONFIGS
            assert TIER_CONFIGS[tier].tier == tier

    def test_premium_config(self):
        from src.core.hardware_tiers import TIER_CONFIGS, HardwareTier

        config = TIER_CONFIGS[HardwareTier.PREMIUM]

        assert config.llm_model == "dolphin-mistral"
        assert config.tts_engine == "xtts"
        assert config.max_context == 8192

    def test_minimal_config(self):
        from src.core.hardware_tiers import TIER_CONFIGS, HardwareTier

        config = TIER_CONFIGS[HardwareTier.MINIMAL]

        assert config.llm_model == "llama3.2:3b"
        assert config.tts_engine == "piper"
        assert config.use_gpu is False


class TestHardwareDetectorDetectRam:
    def test_detect_ram_with_psutil(self):
        from src.core.hardware_tiers import HardwareDetector

        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 16 * 1024**3

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            detector = HardwareDetector.__new__(HardwareDetector)
            ram = detector._detect_ram()

            assert 15.9 <= ram <= 16.1

    def test_detect_ram_fallback(self):
        from src.core.hardware_tiers import HardwareDetector

        with patch.dict("sys.modules", {"psutil": None}):
            with patch("builtins.open", side_effect=Exception("no file")):
                detector = HardwareDetector.__new__(HardwareDetector)
                ram = detector._detect_ram()

                assert ram == 8.0


class TestHardwareDetectorDetectGpu:
    def test_detect_gpu_nvidia(self):
        from src.core.hardware_tiers import HardwareDetector

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NVIDIA GeForce RTX 3050, 4096"

        with patch("subprocess.run", return_value=mock_result):
            detector = HardwareDetector.__new__(HardwareDetector)
            gpu = detector._detect_gpu()

            assert gpu["name"] == "NVIDIA GeForce RTX 3050"
            assert gpu["vram_gb"] == 4.0
            assert gpu["has_cuda"] is True

    def test_detect_gpu_not_found(self):
        from src.core.hardware_tiers import HardwareDetector

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            detector = HardwareDetector.__new__(HardwareDetector)
            gpu = detector._detect_gpu()

            assert gpu["name"] is None
            assert gpu["has_cuda"] is False

    def test_detect_gpu_timeout(self):
        import subprocess

        from src.core.hardware_tiers import HardwareDetector

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            detector = HardwareDetector.__new__(HardwareDetector)
            gpu = detector._detect_gpu()

            assert gpu["has_cuda"] is False


class TestHardwareDetectorDetermineTier:
    def test_premium_tier(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=True, gpu_vram_gb=8.0)

        tier = detector.determine_tier()

        assert tier == HardwareTier.PREMIUM

    def test_balanced_tier(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=True, gpu_vram_gb=4.0)

        tier = detector.determine_tier()

        assert tier == HardwareTier.BALANCED

    def test_light_tier(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=True, gpu_vram_gb=2.0)

        tier = detector.determine_tier()

        assert tier == HardwareTier.LIGHT

    def test_minimal_tier_no_gpu(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=False, ram_gb=4.0)

        tier = detector.determine_tier()

        assert tier == HardwareTier.MINIMAL

    def test_light_tier_high_ram_no_gpu(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=False, ram_gb=16.0)

        tier = detector.determine_tier()

        assert tier == HardwareTier.LIGHT


class TestHardwareDetectorGetConfig:
    def test_returns_tier_config(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, HardwareTier

        detector = HardwareDetector.__new__(HardwareDetector)
        detector.info = HardwareInfo(has_cuda=True, gpu_vram_gb=8.0)

        config = detector.get_config()

        assert config.tier == HardwareTier.PREMIUM


class TestGetHardwareDetector:
    def test_returns_singleton(self):
        import src.core.hardware_tiers as module
        from src.core.hardware_tiers import get_hardware_detector

        module._cached_detector = None

        d1 = get_hardware_detector()
        d2 = get_hardware_detector()

        assert d1 is d2


class TestGetHardwareConfig:
    def test_returns_config(self):
        from src.core.hardware_tiers import HardwareDetector, HardwareInfo, TierConfig

        with patch("src.core.hardware_tiers.get_hardware_detector") as mock_get:
            mock_detector = MagicMock(spec=HardwareDetector)
            mock_detector.info = HardwareInfo(has_cuda=True, gpu_vram_gb=8.0)
            mock_detector.get_config.return_value = TierConfig(
                tier=MagicMock(value="premium"),
                llm_model="test",
                llm_provider="ollama",
                tts_engine="xtts",
                stt_model="medium",
                use_gpu=True,
                max_context=8192,
            )
            mock_get.return_value = mock_detector

            from src.core.hardware_tiers import get_hardware_config

            config = get_hardware_config()

            assert config is not None


class TestApplyHardwareConfig:
    def test_applies_config(self):
        from src.core.hardware_tiers import HardwareTier, TierConfig, apply_hardware_config

        config = TierConfig(
            tier=HardwareTier.BALANCED,
            llm_model="phi3:mini",
            llm_provider="ollama",
            tts_engine="xtts",
            stt_model="small",
            use_gpu=True,
            max_context=4096,
        )

        mock_cfg = MagicMock()
        mock_cfg.WHISPER_CONFIG = {"MODEL_SIZE": "base", "USE_GPU": False}
        mock_cfg.CHAT_PROVIDER = "gemini"
        mock_cfg.CHAT_LOCAL = {"model": "old", "context_length": 2048}
        mock_cfg.TTS_ENGINE = "piper"

        with patch.dict("sys.modules", {"config": mock_cfg}):
            apply_hardware_config(config)

            assert mock_cfg.WHISPER_CONFIG["MODEL_SIZE"] == "small"
            assert mock_cfg.WHISPER_CONFIG["USE_GPU"] is True


class TestGetTierForVram:
    def test_premium(self):
        from src.core.hardware_tiers import HardwareTier, get_tier_for_vram

        assert get_tier_for_vram(8.0) == HardwareTier.PREMIUM
        assert get_tier_for_vram(6.0) == HardwareTier.PREMIUM

    def test_balanced(self):
        from src.core.hardware_tiers import HardwareTier, get_tier_for_vram

        assert get_tier_for_vram(4.0) == HardwareTier.BALANCED
        assert get_tier_for_vram(5.0) == HardwareTier.BALANCED

    def test_light(self):
        from src.core.hardware_tiers import HardwareTier, get_tier_for_vram

        assert get_tier_for_vram(2.0) == HardwareTier.LIGHT
        assert get_tier_for_vram(3.0) == HardwareTier.LIGHT

    def test_minimal(self):
        from src.core.hardware_tiers import HardwareTier, get_tier_for_vram

        assert get_tier_for_vram(1.0) == HardwareTier.MINIMAL
        assert get_tier_for_vram(0.0) == HardwareTier.MINIMAL


class TestGetTierDescription:
    def test_all_tiers_have_description(self):
        from src.core.hardware_tiers import HardwareTier, get_tier_description

        for tier in HardwareTier:
            desc = get_tier_description(tier)
            assert isinstance(desc, str)
            assert len(desc) > 10
