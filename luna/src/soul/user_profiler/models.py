from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NameAnalysis:
    nome_original: str
    nome_normalizado: str
    genero_provavel: str
    confianca_genero: float
    possiveis_origens: list[str]
    diminutivos_comuns: list[str]
    tratamento_sugerido: str
    silabas: int
    fonetica: str


@dataclass
class VisualAnalysis:
    genero_aparente: str
    idade_estimada: str
    faixa_etaria: str
    caracteristicas_fisicas: dict[str, str]
    estilo_vestimenta: str
    acessorios: list[str]
    expressao_facial: str
    cor_predominante: str
    descricao_completa: str
    confianca: float


@dataclass
class VoiceAnalysis:
    tipo_voz: str
    tom_predominante: str
    velocidade_fala: str
    sotaque_detectado: str
    caracteristicas: list[str]


@dataclass
class UserProfile:
    nome: str
    nome_completo: str
    nome_analise: NameAnalysis | None = None
    visual_analise: VisualAnalysis | None = None
    voz_analise: VoiceAnalysis | None = None
    preferencias: dict[str, Any] = field(default_factory=dict)
    primeiro_contato: str = ""
    ultima_atualizacao: str = ""
    versao: int = 1

    def to_dict(self) -> dict:
        data = {
            "nome": self.nome,
            "nome_completo": self.nome_completo,
            "preferencias": self.preferencias,
            "primeiro_contato": self.primeiro_contato,
            "ultima_atualizacao": self.ultima_atualizacao,
            "versao": self.versao,
        }
        if self.nome_analise:
            data["nome_analise"] = asdict(self.nome_analise)
        if self.visual_analise:
            data["visual_analise"] = asdict(self.visual_analise)
        if self.voz_analise:
            data["voz_analise"] = asdict(self.voz_analise)
        return data
