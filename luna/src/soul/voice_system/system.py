import hashlib
import logging
import re
import tempfile
import time

import config

from .engines import CHATTERBOX_AVAILABLE, ChatterboxEngine, CoquiTTSEngine
from .manager import VoiceManager
from .models import LunaResponse

try:
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs

    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LunaVoiceSystem:
    def __init__(self, device: str = "cuda"):
        self.voices_dir = config.APP_DIR / "src" / "assets" / "voices"
        self.output_dir = config.APP_DIR / "src" / "temp" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.coqui_engine = CoquiTTSEngine()
        self.chatterbox_engine = ChatterboxEngine(device=device)
        self.voice_manager = VoiceManager(self.voices_dir)

        self.elevenlabs_client = None
        if ELEVENLABS_AVAILABLE and config.ELEVENLABS_API_KEY:
            try:
                self.elevenlabs_client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
                logger.info("ElevenLabs client initialized.")
            except Exception as e:
                logger.error(f"ElevenLabs init failed: {e}")

        self.emotion_voice_map = {
            "neutral": "luna_neutral",
            "seductive": "luna_seductive",
            "playful": "luna_playful",
            "serious": "luna_serious",
            "passionate": "luna_passionate",
            "happy": "luna_playful",
            "sad": "luna_serious",
            "angry": "luna_serious",
        }

        self.setup_default_voices()

    def setup_default_voices(self) -> None:
        defaults = [
            ("luna_neutral", "neutral.wav", 0.5, 0.5, 0.8, "Neutral"),
            ("luna_seductive", "seductive.wav", 0.7, 0.4, 0.9, "Seductive"),
            ("luna_playful", "playful.wav", 0.6, 0.5, 0.85, "Playful"),
            ("luna_serious", "serious.wav", 0.4, 0.6, 0.75, "Serious"),
        ]
        for name, file, exag, cfg, temp, desc in defaults:
            if name not in self.voice_manager.profiles:
                path = str(self.voices_dir / file)
                self.voice_manager.add_profile(name, path, exag, cfg, temp, desc)

    def _select_voice_for_emotion(self, emotion: str) -> str:
        if "feliz" in emotion.lower():
            emotion = "happy"
        if "triste" in emotion.lower():
            emotion = "sad"
        if "irritada" in emotion.lower():
            emotion = "angry"
        if "neutra" in emotion.lower() or "observando" in emotion.lower():
            emotion = "neutral"
        if "flertando" in emotion.lower() or "sensual" in emotion.lower():
            emotion = "seductive"

        return self.emotion_voice_map.get(emotion, "luna_neutral")

    def _generate_coqui_tts(self, text: str, emotion: str) -> str | None:
        if not self.coqui_engine.is_available():
            return None

        voice_name = self._select_voice_for_emotion(emotion)
        profile = self.voice_manager.get_profile(voice_name)

        if not profile:
            profile = self.voice_manager.get_profile("luna_neutral")

        reference_audio = profile.audio_path if profile else None

        return self.coqui_engine.generate(text, reference_audio=reference_audio, speed=1.0)

    def _generate_chatterbox(self, text: str, emotion: str) -> str | None:
        if not self.chatterbox_engine.model:
            return None

        voice_name = self._select_voice_for_emotion(emotion)
        profile = self.voice_manager.get_profile(voice_name)

        if not profile:
            profile = self.voice_manager.get_profile("luna_neutral")

        exag = profile.exaggeration if profile else 0.5
        cfg = profile.cfg_weight if profile else 0.5
        temp = profile.temperature if profile else 0.8
        path = profile.audio_path if profile else None

        wav = self.chatterbox_engine.generate(
            text, voice_sample=path, exaggeration=exag, cfg_weight=cfg, temperature=temp
        )

        if wav is not None:
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"luna_{emotion}_{text_hash}.wav"
            output_path = str(self.output_dir / filename)
            self.chatterbox_engine.save_audio(wav, output_path)
            return output_path
        return None

    def _generate_elevenlabs(self, text: str, stability: float = 0.5, style: float = 0.0) -> str | None:
        if not self.elevenlabs_client:
            return None

        try:
            voice_id = config.VOICE_SETTINGS.get("ELEVENLABS_VOICE_ID", "")
            if not voice_id:
                logger.warning("ELEVENLABS_VOICE_ID not configured")
                return None
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=stability, similarity_boost=0.75, style=style, use_speaker_boost=True
                ),
            )
            audio_bytes = b"".join(audio_generator)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=str(self.output_dir)) as tmp_mp3:
                tmp_mp3.write(audio_bytes)
                return tmp_mp3.name
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}")
            return None

    def _sanitize_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"[\*_]{1,3}", "", text)
        text = re.sub(r"`+", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
        text = re.sub(r"#+\s", "", text)
        text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def synthesize(self, text: str, emotion: str = "neutral", metatags: dict = None) -> LunaResponse:
        start_time = time.time()

        text = self._sanitize_text(text)
        if not text.strip():
            logger.warning("Texto vazio apos sanitizacao, ignorando TTS.")
            return LunaResponse(text, None, emotion, None, 0, "none")

        audio_path = self._generate_coqui_tts(text, emotion)
        engine_used = "coqui-tts"

        if not audio_path:
            logger.info("Coqui TTS falhou, tentando Chatterbox...")
            audio_path = self._generate_chatterbox(text, emotion)
            engine_used = "chatterbox"

        if not audio_path:
            logger.info("Chatterbox falhou, tentando ElevenLabs...")
            stability = metatags.get("stability", 0.5) if metatags else 0.5
            style = metatags.get("style", 0.0) if metatags else 0.0
            audio_path = self._generate_elevenlabs(text, stability, style)
            engine_used = "elevenlabs"

        generation_time = time.time() - start_time

        return LunaResponse(
            text=text,
            audio_path=audio_path,
            emotion=emotion,
            voice_profile=self._select_voice_for_emotion(emotion),
            generation_time=generation_time,
            engine=engine_used,
        )

    def cleanup(self) -> None:
        self.chatterbox_engine.cleanup()
