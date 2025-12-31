import time
from unittest.mock import MagicMock, patch

import numpy as np

TEST_USER = "test_user"


class TestVisaoInit:
    def test_initializes_stats(self):
        with patch("src.soul.visao.core.config") as mock_config:
            mock_config.VISION_CONFIG = {"CAMERA_INDEX": 0}
            mock_config.VISION_PROVIDER = "gemini"
            mock_config.GOOGLE_API_KEY = None
            mock_config.VISION_LOCAL = {"model": "llava"}
            mock_config.GEMINI_CONFIG = {"MODEL_NAME": "gemini-pro-vision"}
            with patch("src.soul.visao.core.get_metrics"):
                with patch("src.soul.visao.core.MemoriaDeRostos"):
                    with patch("src.soul.visao.core.VisionProviderFactory") as mock_factory:
                        mock_factory.create.return_value = (None, None, "No API key")

                        from src.soul.visao import Visao

                        visao = Visao()

                        assert visao.stats["total_captures"] == 0
                        assert visao.stats["api_calls"] == 0
                        assert visao.stats["cache_hits"] == 0

    def test_sets_default_intervals(self):
        with patch("src.soul.visao.core.config") as mock_config:
            mock_config.VISION_CONFIG = {"CAMERA_INDEX": 0}
            mock_config.VISION_PROVIDER = "gemini"
            mock_config.GOOGLE_API_KEY = None
            mock_config.VISION_LOCAL = {"model": "llava"}
            mock_config.GEMINI_CONFIG = {"MODEL_NAME": "gemini-pro-vision"}
            with patch("src.soul.visao.core.get_metrics"):
                with patch("src.soul.visao.core.MemoriaDeRostos"):
                    with patch("src.soul.visao.core.VisionProviderFactory") as mock_factory:
                        mock_factory.create.return_value = (None, None, "No API key")

                        from src.soul.visao import Visao

                        visao = Visao()

                        assert visao._min_vision_interval == 3.0
                        assert visao._min_api_interval == 10.0


class TestHealthCheck:
    def test_returns_status_dict(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.vision_ready = True
        visao.provider_name = "gemini"
        visao.provider = MagicMock()
        visao.provider.model_name = "gemini-pro-vision"
        visao.vision_error = None

        with patch("src.soul.visao.core.FACE_RECOGNITION_AVAILABLE", False):
            status = visao.health_check()

            assert status["ready"] is True
            assert status["provider"] == "gemini"
            assert status["model"] == "gemini-pro-vision"
            assert status["error"] is None

    def test_includes_ollama_health_for_local(self):
        from src.soul.visao import Visao
        from src.soul.visao.providers import OllamaVisionProvider

        visao = Visao.__new__(Visao)
        visao.vision_ready = True
        visao.provider_name = "local"
        visao.vision_error = None

        mock_provider = MagicMock(spec=OllamaVisionProvider)
        mock_provider.model_name = "llava"
        mock_provider.client = MagicMock()
        mock_provider.client.check_health.return_value = True
        visao.provider = mock_provider

        with patch("src.soul.visao.core.FACE_RECOGNITION_AVAILABLE", False):
            with patch("src.soul.visao.core.OllamaVisionProvider", OllamaVisionProvider):
                status = visao.health_check()

                assert status["ollama_healthy"] is True


class TestFrameToBase64:
    def test_converts_frame_to_base64(self):
        from src.soul.visao.providers import frame_to_base64

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = frame_to_base64(frame)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_resizes_large_frames(self):
        from src.soul.visao.providers import frame_to_base64

        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        result = frame_to_base64(frame)

        assert isinstance(result, str)


class TestImageAnalyzerHash:
    def test_returns_none_without_imagehash(self):
        from src.soul.visao import ImageAnalyzer

        analyzer = ImageAnalyzer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch("src.soul.visao.image_analysis.IMAGEHASH_AVAILABLE", False):
            result = analyzer.calcular_hash_perceptual(frame)

            assert result is None

    def test_returns_hash_with_imagehash(self):
        from src.soul.visao import ImageAnalyzer

        analyzer = ImageAnalyzer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch("src.soul.visao.image_analysis.IMAGEHASH_AVAILABLE", True):
            with patch("src.soul.visao.image_analysis.imagehash") as mock_ih:
                mock_ih.phash.return_value = "abcd1234"

                result = analyzer.calcular_hash_perceptual(frame)

                assert result == "abcd1234"


class TestImageAnalyzerHistogram:
    def test_returns_correlation(self):
        from src.soul.visao import ImageAnalyzer

        analyzer = ImageAnalyzer()
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)

        result = analyzer.calcular_diferenca_histograma(frame1, frame2)

        assert isinstance(result, float)
        assert result == 1.0

    def test_different_frames_lower_correlation(self):
        from src.soul.visao import ImageAnalyzer

        analyzer = ImageAnalyzer()
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 255

        result = analyzer.calcular_diferenca_histograma(frame1, frame2)

        assert result < 1.0


class TestChangeDetector:
    def test_first_frame_always_significant(self):
        from src.soul.visao import ChangeDetector, ImageAnalyzer

        image_analyzer = ImageAnalyzer()
        face_analyzer = MagicMock()
        face_analyzer.analisar_rostos.return_value = []

        detector = ChangeDetector(image_analyzer, face_analyzer)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("src.soul.visao.image_analysis.IMAGEHASH_AVAILABLE", False):
            mudou, tipo, pessoas = detector.detectar_mudanca_significativa(frame)

            assert mudou is True
            assert tipo == "primeiro_frame"
            assert pessoas == []

    def test_no_change_detected(self):
        from src.soul.visao import ChangeDetector, ImageAnalyzer

        image_analyzer = ImageAnalyzer()
        face_analyzer = MagicMock()
        face_analyzer.analisar_rostos.return_value = []

        detector = ChangeDetector(image_analyzer, face_analyzer)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detector.last_frame = frame.copy()
        detector.last_face_count = 0
        detector.last_pessoas = []
        detector.last_frame_hash = None
        detector.frame_count = 1

        with patch("src.soul.visao.image_analysis.IMAGEHASH_AVAILABLE", False):
            mudou, tipo, pessoas = detector.detectar_mudanca_significativa(frame)

            assert mudou is False
            assert tipo == "sem_mudanca"

    def test_updates_state(self):
        from src.soul.visao import ChangeDetector, ImageAnalyzer

        image_analyzer = ImageAnalyzer()
        face_analyzer = MagicMock()
        face_analyzer.analisar_rostos.return_value = []

        detector = ChangeDetector(image_analyzer, face_analyzer)
        detector.last_frame = None
        detector.last_face_count = 0
        detector.last_pessoas = []
        detector.last_frame_hash = None

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        pessoas = [{"nome": TEST_USER, "eh_novo": False}]

        with patch("src.soul.visao.image_analysis.IMAGEHASH_AVAILABLE", False):
            detector._atualizar_estado(frame, pessoas)

            assert detector.last_frame is not None
            assert detector.last_face_count == 1
            assert detector.last_pessoas == [TEST_USER]


class TestFaceAnalyzer:
    def test_returns_empty_without_face_recognition(self):
        from src.soul.visao import FaceAnalyzer

        memoria = MagicMock()
        analyzer = FaceAnalyzer(memoria)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", False):
            result = analyzer.analisar_rostos(frame)

            assert result == []

    def test_identifies_faces(self):
        from src.soul.visao import FaceAnalyzer

        memoria = MagicMock()
        memoria.identificar_rosto.return_value = (TEST_USER, 0.3)
        analyzer = FaceAnalyzer(memoria)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        embedding = np.array([0.1, 0.2])
        posicao = (10, 20, 30, 40)

        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", True):
            with patch(
                "src.soul.memoria.extrair_embeddings_do_frame",
                return_value=[(embedding, posicao)],
            ):
                result = analyzer.analisar_rostos(frame)

                assert len(result) == 1
                assert result[0]["nome"] == TEST_USER
                assert result[0]["distancia"] == 0.3


class TestVisaoRegistrarPessoa:
    def test_delegates_to_memoria(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.memoria = MagicMock()
        visao.memoria.registrar_rosto.return_value = True

        embedding = np.array([0.1, 0.2, 0.3])

        result = visao.registrar_pessoa(TEST_USER, embedding)

        assert result is True
        visao.memoria.registrar_rosto.assert_called_once_with(TEST_USER, embedding)


class TestVisionCache:
    def test_removes_expired_entries(self):
        from src.soul.visao import VisionCache

        cache = VisionCache(ttl=120, max_entries=20)
        cache.cache = {
            "hash1": {"timestamp": time.time() - 200, "description": "old"},
            "hash2": {"timestamp": time.time() - 10, "description": "new"},
        }

        cache._cleanup()

        assert "hash1" not in cache.cache
        assert "hash2" in cache.cache

    def test_limits_cache_size(self):
        from src.soul.visao import VisionCache

        cache = VisionCache(ttl=120, max_entries=2)
        now = time.time()
        cache.cache = {
            "hash1": {"timestamp": now - 30, "description": "oldest"},
            "hash2": {"timestamp": now - 20, "description": "middle"},
            "hash3": {"timestamp": now - 10, "description": "newest"},
        }

        cache._cleanup()

        assert len(cache.cache) <= 2


class TestGetVisionStats:
    def test_returns_stats_dict(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.stats = {
            "total_captures": 100,
            "api_calls": 50,
            "cache_hits": 30,
            "local_detections": 20,
        }

        result = visao.get_vision_stats()

        assert result["total_captures"] == 100
        assert result["api_calls"] == 50
        assert result["cache_hits"] == 30
        assert result["quota_reduction_pct"] == 30.0

    def test_handles_zero_total(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.stats = {
            "total_captures": 0,
            "api_calls": 0,
            "cache_hits": 0,
            "local_detections": 0,
        }

        result = visao.get_vision_stats()

        assert result["quota_reduction_pct"] == 0
        assert result["api_call_rate"] == 0


class TestVisaoRelease:
    def test_cleanup_completes(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)

        result = visao.release()

        assert result is None


class TestOlharAgora:
    def test_throttled_returns_cached(self):
        from src.soul.visao import Visao, VisionCache

        visao = Visao.__new__(Visao)
        visao.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}
        visao._last_vision_time = time.time()
        visao._min_vision_interval = 3.0

        cache = VisionCache()
        cache.set("test", "cached result")
        visao.vision_cache = cache

        result = visao.olhar_agora()

        assert result == "cached result"

    def test_no_camera(self):
        from src.soul.visao import Visao, VisionCache

        visao = Visao.__new__(Visao)
        visao.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}
        visao._last_vision_time = 0
        visao._min_vision_interval = 3.0
        visao.vision_cache = VisionCache()

        visao.capturar_frame = MagicMock(return_value=None)

        result = visao.olhar_agora()

        assert "erro na camera" in result.lower() or "camera" in result.lower()

    def test_no_provider(self):
        from src.soul.visao import Visao, VisionCache

        visao = Visao.__new__(Visao)
        visao.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}
        visao._last_vision_time = 0
        visao._min_vision_interval = 3.0
        visao.vision_cache = VisionCache()
        visao.provider = None

        visao.capturar_frame = MagicMock(return_value=np.zeros((100, 100, 3), dtype=np.uint8))

        result = visao.olhar_agora()

        assert "API" in result


class TestOlharInteligente:
    def test_camera_unavailable(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}
        visao.capturar_frame = MagicMock(return_value=None)

        mudou, tipo, desc, pessoas = visao.olhar_inteligente()

        assert mudou is False
        assert "indisponivel" in desc.lower()

    def test_no_change_saves_api(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.stats = {"total_captures": 0, "api_calls": 0, "cache_hits": 0, "local_detections": 0}
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        visao.capturar_frame = MagicMock(return_value=frame)
        visao.detectar_mudanca_significativa = MagicMock(return_value=(False, "sem_mudanca", []))

        mudou, tipo, desc, pessoas = visao.olhar_inteligente()

        assert mudou is False
        assert visao.stats["local_detections"] == 1


class TestPersonProfileManager:
    def test_saves_profile(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.person_profile = MagicMock()
        visao.person_profile.salvar_perfil_visual.return_value = True

        result = visao.salvar_perfil_visual(TEST_USER, "Descricao teste")

        assert result is True
        visao.person_profile.salvar_perfil_visual.assert_called_once()

    def test_saves_with_photo(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.person_profile = MagicMock()
        visao.person_profile.salvar_perfil_visual.return_value = True
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        result = visao.salvar_perfil_visual(TEST_USER, "Descricao", frame)

        assert result is True


class TestRegistrarRostoImediato:
    def test_no_frame_captures(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        visao.capturar_frame = MagicMock(return_value=None)

        result = visao.registrar_rosto_imediato(TEST_USER)

        assert result is False

    def test_no_face_found(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        visao.capturar_frame = MagicMock(return_value=frame)

        with patch("src.soul.memoria.extrair_embeddings_do_frame", return_value=[]):
            result = visao.registrar_rosto_imediato(TEST_USER)

            assert result is False

    def test_registers_first_face(self):
        from src.soul.visao import Visao

        visao = Visao.__new__(Visao)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        visao.capturar_frame = MagicMock(return_value=frame)
        visao.memoria = MagicMock()
        visao.memoria.registrar_rosto.return_value = True

        embedding = np.array([0.1, 0.2])
        posicao = (10, 20, 30, 40)

        with patch(
            "src.soul.memoria.extrair_embeddings_do_frame",
            return_value=[(embedding, posicao)],
        ):
            result = visao.registrar_rosto_imediato(TEST_USER)

            assert result is True
            visao.memoria.registrar_rosto.assert_called_once()


class TestCameraManager:
    def test_opens_camera(self):
        from src.soul.visao import CameraManager

        manager = CameraManager(0)

        with patch("src.soul.visao.camera.cv2.VideoCapture") as mock_cap:
            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.read.return_value = (True, np.zeros((480, 640, 3)))

            cap = manager.abrir()

            assert cap is not None

    def test_returns_none_on_failure(self):
        from src.soul.visao import CameraManager

        manager = CameraManager(0)

        with patch("src.soul.visao.camera.cv2.VideoCapture") as mock_cap:
            mock_cap.return_value.isOpened.return_value = False

            cap = manager.abrir()

            assert cap is None

    def test_releases_camera(self):
        from src.soul.visao import CameraManager

        manager = CameraManager(0)
        mock_cap = MagicMock()

        manager.fechar(mock_cap)

        mock_cap.release.assert_called_once()

    def test_handles_none_camera(self):
        from src.soul.visao import CameraManager

        manager = CameraManager(0)

        result = manager.fechar(None)

        assert result is None
