from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.core.file_lock import read_json_safe, write_json_safe

from .models import NameAnalysis, UserProfile, VisualAnalysis, VoiceAnalysis

logger = logging.getLogger(__name__)


class ProfileStorage:
    def __init__(self, user_dir: Path, events_dir: Path, faces_dir: Path):
        self.user_dir = user_dir
        self.events_dir = events_dir
        self.faces_dir = faces_dir
        self.profile_path = user_dir / "profile.json"

        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.faces_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile: UserProfile):
        profile.ultima_atualizacao = datetime.now().isoformat()

        if not profile.primeiro_contato:
            profile.primeiro_contato = profile.ultima_atualizacao

        try:
            write_json_safe(self.profile_path, profile.to_dict())
            logger.info(f"Perfil salvo: {self.profile_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar perfil: {e}")

    def load_profile(self) -> UserProfile | None:
        if not self.profile_path.exists():
            return None

        try:
            data = read_json_safe(self.profile_path)

            profile = UserProfile(
                nome=data.get("nome", ""),
                nome_completo=data.get("nome_completo", ""),
                preferencias=data.get("preferencias", {}),
                primeiro_contato=data.get("primeiro_contato", ""),
                ultima_atualizacao=data.get("ultima_atualizacao", ""),
                versao=data.get("versao", 1),
            )

            if "nome_analise" in data:
                profile.nome_analise = NameAnalysis(**data["nome_analise"])
            if "visual_analise" in data:
                profile.visual_analise = VisualAnalysis(**data["visual_analise"])
            if "voz_analise" in data:
                profile.voz_analise = VoiceAnalysis(**data["voz_analise"])

            return profile

        except Exception as e:
            logger.error(f"Erro ao carregar perfil: {e}")
            return None

    def save_event(self, event_type: str, data: dict):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        event_file = self.events_dir / f"{event_type}_{timestamp}.json"

        event = {"type": event_type, "timestamp": datetime.now().isoformat(), "data": data}

        try:
            write_json_safe(event_file, event)
            logger.debug(f"Evento salvo: {event_file.name}")
        except Exception as e:
            logger.error(f"Erro ao salvar evento: {e}")

    def save_face(self, name: str, image_data: bytes, metadata: dict = None):
        name_normalized = self._normalize_name(name)
        face_dir = self.faces_dir / name_normalized
        face_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = face_dir / f"photo_{timestamp}.jpg"
        meta_path = face_dir / "metadata.json"

        try:
            with open(photo_path, "wb") as f:
                f.write(image_data)

            if meta_path.exists():
                existing_meta = read_json_safe(meta_path)
            else:
                existing_meta = {"name": name, "photos": [], "created_at": datetime.now().isoformat()}

            existing_meta["photos"].append(
                {"path": str(photo_path), "timestamp": datetime.now().isoformat(), "metadata": metadata or {}}
            )
            existing_meta["updated_at"] = datetime.now().isoformat()

            write_json_safe(meta_path, existing_meta)

            logger.info(f"Rosto salvo: {photo_path}")

        except Exception as e:
            logger.error(f"Erro ao salvar rosto: {e}")

    def _normalize_name(self, text: str) -> str:
        replacements = {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "è": "e",
            "í": "i",
            "ì": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ò": "o",
            "ú": "u",
            "ù": "u",
            "ü": "u",
            "ç": "c",
            "ñ": "n",
        }
        result = text.lower().strip()
        for k, v in replacements.items():
            result = result.replace(k, v)
        return result
