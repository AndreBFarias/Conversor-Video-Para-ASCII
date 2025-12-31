from __future__ import annotations

import config

from .models import NameAnalysis, UserProfile, VisualAnalysis
from .name_analyzer import NameAnalyzer
from .photo_analyzer import PhotoAnalyzer
from .storage import ProfileStorage


class UserProfiler:
    def __init__(self):
        self.user_dir = config.APP_DIR / "src" / "data_memory" / "user"
        self.events_dir = config.APP_DIR / "src" / "data_memory" / "events"
        self.faces_dir = config.APP_DIR / "src" / "data_memory" / "faces"

        self.storage = ProfileStorage(self.user_dir, self.events_dir, self.faces_dir)
        self.name_analyzer = NameAnalyzer()
        self.photo_analyzer = PhotoAnalyzer()

        self._profile: UserProfile | None = None

    def analyze_name(self, nome: str) -> NameAnalysis:
        return self.name_analyzer.analyze(nome)

    async def analyze_photo_with_gemini(self, image_base64: str) -> VisualAnalysis | None:
        return await self.photo_analyzer.analyze_with_gemini(image_base64)

    def save_profile(self, profile: UserProfile):
        self._profile = profile
        self.storage.save_profile(profile)

    def load_profile(self) -> UserProfile | None:
        profile = self.storage.load_profile()
        if profile:
            self._profile = profile
        return profile

    def save_event(self, event_type: str, data: dict):
        self.storage.save_event(event_type, data)

    def save_face(self, name: str, image_data: bytes, metadata: dict = None):
        self.storage.save_face(name, image_data, metadata)

    def get_profile_summary(self) -> str:
        profile = self._profile or self.load_profile()
        if not profile:
            return "Nenhum perfil encontrado."

        lines = [f"Nome: {profile.nome}"]

        if profile.nome_analise:
            na = profile.nome_analise
            lines.append(f"Genero (pelo nome): {na.genero_provavel} ({na.confianca_genero:.0%})")
            if na.possiveis_origens:
                lines.append(f"Origem cultural: {', '.join(na.possiveis_origens)}")

        if profile.visual_analise:
            va = profile.visual_analise
            lines.append(f"Idade estimada: {va.idade_estimada}")
            lines.append(f"Genero aparente: {va.genero_aparente}")
            if va.descricao_completa:
                lines.append(f"Descricao: {va.descricao_completa}")

        return "\n".join(lines)
