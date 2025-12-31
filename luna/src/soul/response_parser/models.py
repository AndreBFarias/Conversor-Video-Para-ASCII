from dataclasses import dataclass, field

from .helpers import get_entity_prefix


@dataclass
class LunaResponseData:
    fala_tts: str = ""
    leitura: str = "Normal"
    log_terminal: str = ""
    animacao: str = ""
    comando_visao: bool = False
    tts_config: dict = field(default_factory=lambda: {"speed": 1.0, "stability": 0.5, "style": 0.3})
    registrar_rosto: str | None = None
    filesystem_ops: list = field(default_factory=list)

    def __post_init__(self):
        if not self.animacao:
            self.animacao = f"{get_entity_prefix()}_observando"

    def to_dict(self) -> dict:
        return {
            "fala_tts": self.fala_tts,
            "leitura": self.leitura,
            "log_terminal": self.log_terminal,
            "animacao": self.animacao,
            "comando_visao": self.comando_visao,
            "tts_config": self.tts_config,
            "registrar_rosto": self.registrar_rosto,
            "filesystem_ops": self.filesystem_ops,
        }
