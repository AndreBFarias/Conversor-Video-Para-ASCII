import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
    logger.info("face_recognition disponivel")
except ImportError:
    logger.warning("face_recognition nao instalado. Reconhecimento facial desabilitado.")
    logger.warning("Instale com: pip install face_recognition")


class MemoriaDeRostos:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data_memory" / "rostos.json"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.known_faces = {}
        self.load()

        logger.info(f"Memoria de rostos inicializada. {len(self.known_faces)} pessoas conhecidas.")

    def load(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, encoding="utf-8") as f:
                    data = json.load(f)

                self.known_faces = {}
                for nome, info in data.items():
                    self.known_faces[nome] = {
                        "embeddings": [np.array(e) for e in info.get("embeddings", [])],
                        "primeiro_encontro": info.get("primeiro_encontro"),
                        "ultimo_encontro": info.get("ultimo_encontro"),
                        "encontros": info.get("encontros", 0),
                    }

                logger.info(f"Carregados {len(self.known_faces)} rostos do banco")
            except Exception as e:
                logger.error(f"Erro ao carregar rostos: {e}")
                self.known_faces = {}
        else:
            logger.info("Nenhum banco de rostos encontrado. Criando novo.")
            self.known_faces = {}

    def save(self):
        try:
            data = {}
            for nome, info in self.known_faces.items():
                data[nome] = {
                    "embeddings": [e.tolist() for e in info.get("embeddings", [])],
                    "primeiro_encontro": info.get("primeiro_encontro"),
                    "ultimo_encontro": info.get("ultimo_encontro"),
                    "encontros": info.get("encontros", 0),
                }

            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Salvos {len(self.known_faces)} rostos no banco")
        except Exception as e:
            logger.error(f"Erro ao salvar rostos: {e}")

    def registrar_rosto(self, nome: str, embedding: np.ndarray) -> bool:
        agora = datetime.now().isoformat()

        if nome in self.known_faces:
            if len(self.known_faces[nome]["embeddings"]) < 5:
                self.known_faces[nome]["embeddings"].append(embedding)
            self.known_faces[nome]["ultimo_encontro"] = agora
            self.known_faces[nome]["encontros"] += 1
            logger.info(f"Atualizado rosto de '{nome}' ({self.known_faces[nome]['encontros']} encontros)")
            self.save()
            return False
        else:
            self.known_faces[nome] = {
                "embeddings": [embedding],
                "primeiro_encontro": agora,
                "ultimo_encontro": agora,
                "encontros": 1,
            }
            logger.info(f"Novo rosto registrado: '{nome}'")
            self.save()
            return True

    def identificar_rosto(self, embedding: np.ndarray, tolerance: float = 0.6) -> tuple[str | None, float]:
        if not self.known_faces:
            return None, 1.0

        melhor_match = None
        menor_distancia = float("inf")

        for nome, info in self.known_faces.items():
            for known_embedding in info.get("embeddings", []):
                distancia = np.linalg.norm(embedding - known_embedding)

                if distancia < menor_distancia:
                    menor_distancia = distancia
                    melhor_match = nome

        if menor_distancia <= tolerance:
            info = self.known_faces[melhor_match]
            info["ultimo_encontro"] = datetime.now().isoformat()
            info["encontros"] += 1
            logger.debug(f"Identificado: '{melhor_match}' (distancia: {menor_distancia:.3f})")
            return melhor_match, menor_distancia

        return None, menor_distancia

    def listar_conhecidos(self) -> list[dict]:
        return [
            {
                "nome": nome,
                "encontros": info.get("encontros", 0),
                "primeiro_encontro": info.get("primeiro_encontro"),
                "ultimo_encontro": info.get("ultimo_encontro"),
            }
            for nome, info in self.known_faces.items()
        ]

    def esquecer_pessoa(self, nome: str) -> bool:
        if nome in self.known_faces:
            del self.known_faces[nome]
            self.save()
            logger.info(f"Pessoa '{nome}' removida da memoria")
            return True
        return False


def extrair_embeddings_do_frame(frame_rgb) -> list[tuple[np.ndarray, tuple]]:
    if not FACE_RECOGNITION_AVAILABLE:
        return []

    try:
        face_locations = face_recognition.face_locations(frame_rgb, model="hog")

        if not face_locations:
            return []

        face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

        return list(zip(face_encodings, face_locations, strict=False))

    except Exception as e:
        logger.error(f"Erro ao extrair embeddings: {e}")
        return []
