import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np


class TestMemoriaDeRostosInit:
    def test_creates_with_custom_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            assert len(memoria.known_faces) == 0
            assert memoria.db_path == db_path

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir" / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(subdir))

            assert subdir.parent.exists()


class TestMemoriaDeRostosLoad:
    def test_loads_empty_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            assert len(memoria.known_faces) == 0

    def test_loads_existing_faces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"
            data = {
                "test_user_1": {
                    "embeddings": [[0.1, 0.2, 0.3]],
                    "primeiro_encontro": "2024-01-01T00:00:00",
                    "ultimo_encontro": "2024-01-01T00:00:00",
                    "encontros": 1,
                }
            }
            with open(db_path, "w") as f:
                json.dump(data, f)

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            assert "test_user_1" in memoria.known_faces
            assert memoria.known_faces["test_user_1"]["encontros"] == 1

    def test_handles_corrupt_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"
            with open(db_path, "w") as f:
                f.write("invalid json{")

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            assert len(memoria.known_faces) == 0


class TestMemoriaDeRostosSave:
    def test_saves_faces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.known_faces["test_user_1"] = {
                "embeddings": [np.array([0.1, 0.2, 0.3])],
                "primeiro_encontro": "2024-01-01T00:00:00",
                "ultimo_encontro": "2024-01-01T00:00:00",
                "encontros": 1,
            }

            memoria.save()

            with open(db_path) as f:
                data = json.load(f)

            assert "test_user_1" in data

    def test_converts_numpy_to_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.known_faces["test_user_1"] = {
                "embeddings": [np.array([0.1, 0.2, 0.3])],
                "primeiro_encontro": "2024-01-01",
                "ultimo_encontro": "2024-01-01",
                "encontros": 1,
            }

            memoria.save()

            with open(db_path) as f:
                data = json.load(f)

            assert isinstance(data["test_user_1"]["embeddings"][0], list)


class TestMemoriaDeRostosRegistrarRosto:
    def test_registers_new_face(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            embedding = np.array([0.1, 0.2, 0.3])

            result = memoria.registrar_rosto("test_user_1", embedding)

            assert result is True
            assert "test_user_1" in memoria.known_faces
            assert memoria.known_faces["test_user_1"]["encontros"] == 1

    def test_updates_existing_face(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            embedding1 = np.array([0.1, 0.2, 0.3])
            embedding2 = np.array([0.4, 0.5, 0.6])

            memoria.registrar_rosto("test_user_1", embedding1)
            result = memoria.registrar_rosto("test_user_1", embedding2)

            assert result is False
            assert memoria.known_faces["test_user_1"]["encontros"] == 2
            assert len(memoria.known_faces["test_user_1"]["embeddings"]) == 2

    def test_limits_embeddings_to_five(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            for i in range(7):
                embedding = np.array([0.1 * i, 0.2 * i, 0.3 * i])
                memoria.registrar_rosto("test_user_1", embedding)

            assert len(memoria.known_faces["test_user_1"]["embeddings"]) == 5


class TestMemoriaDeRostosIdentificarRosto:
    def test_returns_none_when_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            embedding = np.array([0.1, 0.2, 0.3])

            name, distance = memoria.identificar_rosto(embedding)

            assert name is None
            assert distance == 1.0

    def test_identifies_known_face(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            original = np.array([0.1, 0.2, 0.3])
            memoria.registrar_rosto("test_user_1", original)

            similar = np.array([0.11, 0.21, 0.31])
            name, distance = memoria.identificar_rosto(similar, tolerance=0.5)

            assert name == "test_user_1"
            assert distance < 0.5

    def test_returns_none_for_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            original = np.array([0.1, 0.2, 0.3])
            memoria.registrar_rosto("test_user_1", original)

            different = np.array([10.0, 20.0, 30.0])
            name, distance = memoria.identificar_rosto(different, tolerance=0.5)

            assert name is None

    def test_increments_encontros(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            original = np.array([0.1, 0.2, 0.3])
            memoria.registrar_rosto("test_user_1", original)

            similar = np.array([0.11, 0.21, 0.31])
            memoria.identificar_rosto(similar, tolerance=0.5)

            assert memoria.known_faces["test_user_1"]["encontros"] == 2


class TestMemoriaDeRostosListarConhecidos:
    def test_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            result = memoria.listar_conhecidos()

            assert result == []

    def test_returns_list_of_known(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.registrar_rosto("test_user_1", np.array([0.1, 0.2, 0.3]))
            memoria.registrar_rosto("test_user_2", np.array([0.4, 0.5, 0.6]))

            result = memoria.listar_conhecidos()

            assert len(result) == 2
            names = [r["nome"] for r in result]
            assert "test_user_1" in names
            assert "test_user_2" in names

    def test_returns_correct_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.registrar_rosto("test_user_1", np.array([0.1, 0.2, 0.3]))

            result = memoria.listar_conhecidos()

            assert "nome" in result[0]
            assert "encontros" in result[0]
            assert "primeiro_encontro" in result[0]
            assert "ultimo_encontro" in result[0]


class TestMemoriaDeRostosEsquecerPessoa:
    def test_removes_known_person(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.registrar_rosto("test_user_1", np.array([0.1, 0.2, 0.3]))

            result = memoria.esquecer_pessoa("test_user_1")

            assert result is True
            assert "test_user_1" not in memoria.known_faces

    def test_returns_false_for_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))

            result = memoria.esquecer_pessoa("unknown_person")

            assert result is False

    def test_saves_after_removal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rostos.json"

            from src.soul.memoria import MemoriaDeRostos

            memoria = MemoriaDeRostos(db_path=str(db_path))
            memoria.registrar_rosto("test_user_1", np.array([0.1, 0.2, 0.3]))
            memoria.esquecer_pessoa("test_user_1")

            with open(db_path) as f:
                data = json.load(f)

            assert "test_user_1" not in data


class TestExtrairEmbeddingsDoFrame:
    def test_returns_empty_when_not_available(self):
        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", False):
            from src.soul.memoria import extrair_embeddings_do_frame

            result = extrair_embeddings_do_frame(np.zeros((100, 100, 3)))

            assert result == []

    def test_returns_empty_on_error(self):
        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", True):
            with patch("src.soul.memoria.face_recognition") as mock_fr:
                mock_fr.face_locations.side_effect = Exception("Test error")

                from src.soul.memoria import extrair_embeddings_do_frame

                result = extrair_embeddings_do_frame(np.zeros((100, 100, 3)))

                assert result == []

    def test_returns_empty_when_no_faces(self):
        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", True):
            with patch("src.soul.memoria.face_recognition") as mock_fr:
                mock_fr.face_locations.return_value = []

                from src.soul.memoria import extrair_embeddings_do_frame

                result = extrair_embeddings_do_frame(np.zeros((100, 100, 3)))

                assert result == []

    def test_returns_embeddings_when_faces_found(self):
        with patch("src.soul.memoria.FACE_RECOGNITION_AVAILABLE", True):
            with patch("src.soul.memoria.face_recognition") as mock_fr:
                mock_fr.face_locations.return_value = [(10, 20, 30, 40)]
                mock_fr.face_encodings.return_value = [np.array([0.1, 0.2, 0.3])]

                from src.soul.memoria import extrair_embeddings_do_frame

                result = extrair_embeddings_do_frame(np.zeros((100, 100, 3)))

                assert len(result) == 1
                assert isinstance(result[0], tuple)
