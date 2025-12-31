"""
Boca - Sistema de Text-to-Speech.

Gerencia sintese de voz usando Coqui TTS ou Chatterbox:
- Sintese de voz local via daemon ou inline
- Suporte a multiplas vozes por entidade
- Cache de audio para performance
- Fallback entre engines TTS

Classes principais:
    Boca: Classe principal de TTS

Dependencias:
    - src.core.audio_utils: Descompressao de arquivos de referencia
    - src.core.entity_loader: Configuracao de voz por entidade

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/boca/
"""

from src.soul.boca import (
    Boca,
    TextSanitizer,
    TTS_SOCKET_PATH,
    check_chatterbox,
    check_coqui,
    check_daemon,
    check_elevenlabs,
    falar_chatterbox,
    falar_coqui,
    falar_elevenlabs,
    gerar_chatterbox,
    gerar_coqui,
    gerar_elevenlabs,
    gerar_via_daemon,
    get_effective_engine,
    parar,
    play_audio_file,
    sanitize_text,
)

__all__ = [
    "Boca",
    "TextSanitizer",
    "sanitize_text",
    "TTS_SOCKET_PATH",
    "check_daemon",
    "check_elevenlabs",
    "check_coqui",
    "check_chatterbox",
    "get_effective_engine",
    "gerar_via_daemon",
    "gerar_coqui",
    "falar_coqui",
    "gerar_chatterbox",
    "falar_chatterbox",
    "gerar_elevenlabs",
    "falar_elevenlabs",
    "play_audio_file",
    "parar",
]
