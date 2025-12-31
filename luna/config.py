import os
import pathlib

from dotenv import load_dotenv

# Cartegra o .env da raiz do projeto
_env_path = pathlib.Path(__file__).parent / ".env"
_env_loaded = load_dotenv(_env_path, override=True)

if not _env_loaded:
    pass

APP_DIR = pathlib.Path(__file__).parent.resolve()

PANTEAO_DIR = APP_DIR / "src" / "assets" / "panteao"
ENTITIES_DIR = PANTEAO_DIR / "entities"

SESSIONS_DIR = APP_DIR / "src" / "sessions"
MANIFEST_FILE = SESSIONS_DIR / "sessions_manifest.json"

DEFAULT_ENTITY = "luna"
LEGACY_SOUL_FILE = ENTITIES_DIR / DEFAULT_ENTITY / "alma.txt"


def get_animations_dir(entity_id: str = None) -> pathlib.Path:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_dir = ENTITIES_DIR / entity_id.lower() / "animations"
    if entity_dir.exists():
        return entity_dir
    return ENTITIES_DIR / DEFAULT_ENTITY / "animations"


def get_soul_path(entity_id: str = None) -> pathlib.Path:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_soul = ENTITIES_DIR / entity_id.lower() / "alma.txt"
    if entity_soul.exists():
        return entity_soul
    return LEGACY_SOUL_FILE


def get_current_entity_id() -> str:
    profile_path = APP_DIR / "src" / "data_memory" / "user" / "profile.json"
    try:
        if profile_path.exists():
            from src.core.file_lock import read_json_safe

            profile = read_json_safe(profile_path)
            return profile.get("active_entity", DEFAULT_ENTITY)
    except Exception:
        pass
    return DEFAULT_ENTITY


ASCII_ART_DIR = get_animations_dir(DEFAULT_ENTITY)
SOUL_FILE_PATH = get_soul_path(DEFAULT_ENTITY)

os.makedirs(SESSIONS_DIR, exist_ok=True)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

TTS_ENGINE = os.getenv("TTS_ENGINE", "coqui")

MODELS_DIR = APP_DIR / "src" / "models"

WHISPER_MODELS_DIR = MODELS_DIR / "whisper"
EMBEDDINGS_MODELS_DIR = MODELS_DIR / "embeddings"
TTS_CACHE_DIR = MODELS_DIR / "tts"
FACE_MODELS_DIR = MODELS_DIR / "face"
os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_MODELS_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)
os.makedirs(FACE_MODELS_DIR, exist_ok=True)

COQUI_MODEL_NAME = os.getenv("COQUI_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")
COQUI_DEVICE = os.getenv("COQUI_DEVICE", "cuda")


def get_entity_voice_path(entity_id: str, provider: str, filename: str) -> pathlib.Path:
    return ENTITIES_DIR / entity_id.lower() / "voice" / provider / filename


def get_coqui_reference_audio(entity_id: str = None) -> str:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_path = get_entity_voice_path(entity_id, "coqui", "reference.wav")
    if entity_path.exists():
        return str(entity_path)
    fallback = get_entity_voice_path(DEFAULT_ENTITY, "coqui", "reference.wav")
    return str(fallback)


def get_coqui_speaker_embedding(entity_id: str = None) -> str:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_path = get_entity_voice_path(entity_id, "coqui", "speaker_embedding.pt")
    if entity_path.exists():
        return str(entity_path)
    fallback = get_entity_voice_path(DEFAULT_ENTITY, "coqui", "speaker_embedding.pt")
    return str(fallback)


def get_chatterbox_reference_audio(entity_id: str = None) -> str:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_path = get_entity_voice_path(entity_id, "chatterbox", "reference.wav")
    if entity_path.exists():
        return str(entity_path)
    fallback = get_entity_voice_path(DEFAULT_ENTITY, "chatterbox", "reference.wav")
    return str(fallback)


COQUI_REFERENCE_AUDIO = get_coqui_reference_audio(DEFAULT_ENTITY)
COQUI_SPEAKER_EMBEDDING = get_coqui_speaker_embedding(DEFAULT_ENTITY)

CHATTERBOX_DEVICE = os.getenv("CHATTERBOX_DEVICE", "cuda")
CHATTERBOX_REFERENCE_AUDIO = get_chatterbox_reference_audio(DEFAULT_ENTITY)
CHATTERBOX_EXAGGERATION = 0.3
CHATTERBOX_CFG_WEIGHT = 0.5


WHISPER_CONFIG = {
    "MODEL": os.getenv("TRANSCRIPTION_MODEL", "whisper"),
    "MODEL_SIZE": os.getenv("WHISPER_MODEL_SIZE", "small"),
    "COMPUTE_TYPE": os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
    "USE_GPU": os.getenv("USE_GPU", "true").lower() == "true",
    "GPU_DEVICE": int(os.getenv("GPU_DEVICE", "0")),
}

AUDIO_CONFIG = {
    "SAMPLE_RATE": int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
    "DEVICE_ID": int(os.getenv("AUDIO_DEVICE_ID", "0")),
    "CHANNELS": int(os.getenv("AUDIO_CHANNELS", "1")),
    "CHUNK_SIZE": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
    "BUFFER_DURATION": float(os.getenv("AUDIO_BUFFER_DURATION", "10.0")),
}

VAD_CONFIG = {
    "SILENCE_DURATION": float(os.getenv("VAD_SILENCE_DURATION", "0.8")),
    "ENERGY_THRESHOLD": int(os.getenv("VAD_ENERGY_THRESHOLD", "6000")),
    "STRATEGY": os.getenv("VAD_STRATEGY", "energy"),
    "MODE": int(os.getenv("VAD_MODE", "2")),
    "FRAME_BUFFER_SIZE": int(os.getenv("VAD_FRAME_BUFFER_SIZE", "4")),
    "SILENCE_FRAME_LIMIT": int(os.getenv("VAD_SILENCE_FRAME_LIMIT", "6")),
    "POST_SPEECH_COOLDOWN_FRAMES": int(os.getenv("VAD_POST_SPEECH_COOLDOWN", "15")),
    "MIN_SPEECH_CHUNKS": int(os.getenv("VAD_MIN_SPEECH_CHUNKS", "3")),
    "MAX_INITIAL_SILENCE": float(os.getenv("VAD_MAX_INITIAL_SILENCE", "2.0")),
    "TARGET_RATE": int(os.getenv("VAD_TARGET_RATE", "16000")),
    "AUTO_ADJUST": os.getenv("VAD_AUTO_ADJUST", "true").lower() == "true",
    "NOISE_MULTIPLIER": float(os.getenv("VAD_NOISE_MULTIPLIER", "2.0")),
    "CALIBRATION_SECONDS": float(os.getenv("VAD_CALIBRATION_SECONDS", "3.0")),
    "MIN_THRESHOLD": int(os.getenv("VAD_MIN_THRESHOLD", "500")),
    "MAX_THRESHOLD": int(os.getenv("VAD_MAX_THRESHOLD", "15000")),
}

GEMINI_CONFIG = {
    "MODEL_NAME": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    "MAX_RETRIES": int(os.getenv("GEMINI_MAX_RETRIES", "5")),
    "RETRY_DELAY": int(os.getenv("GEMINI_RETRY_DELAY", "3")),
    "TIMEOUT": int(os.getenv("GEMINI_TIMEOUT", "30")),
    "CACHE_SIZE": int(os.getenv("GEMINI_CACHE_SIZE", "200")),
}

WHISPER_TRANSCRIPTION = {
    "BEAM_SIZE": int(os.getenv("WHISPER_BEAM_SIZE", "10")),
    "BEST_OF": int(os.getenv("WHISPER_BEST_OF", "5")),
    "NO_SPEECH_THRESHOLD": float(os.getenv("WHISPER_NO_SPEECH_THRESHOLD", "0.6")),
    "LOG_PROB_THRESHOLD": float(os.getenv("WHISPER_LOG_PROB_THRESHOLD", "-0.8")),
    "COMPRESSION_RATIO_THRESHOLD": float(os.getenv("WHISPER_COMPRESSION_RATIO", "2.4")),
    "VAD_FILTER": os.getenv("WHISPER_VAD_FILTER", "true").lower() == "true",
    "VAD_MIN_SILENCE_MS": int(os.getenv("WHISPER_VAD_MIN_SILENCE_MS", "500")),
    "CONDITION_ON_PREVIOUS": os.getenv("WHISPER_CONDITION_ON_PREVIOUS", "false").lower() == "true",
    "KEYWORDS": os.getenv("WHISPER_KEYWORDS", "Luna,oi Luna,ei Luna"),
    "INITIAL_PROMPT": os.getenv(
        "WHISPER_INITIAL_PROMPT", "Conversa em portugues brasileiro com Luna, uma assistente virtual."
    ),
}

WHISPER_HALLUCINATION_FILTERS = [
    "obrigado",
    "obrigada",
    "obrigado por assistir",
    "obrigado a todos",
    "a emissora",
    "legendado",
    "legendas",
    "tradução",
    "tradutor",
    "inscreva",
    "inscreva-se",
    "se inscreva",
    "inscrito",
    "inscrita",
    "gostou",
    "curta",
    "curtir",
    "deixe seu like",
    "deixa o like",
    "compartilhe",
    "compartilhar",
    "manda pra alguem",
    "até a próxima",
    "ate a proxima",
    "até mais",
    "ate mais",
    "tchau",
    "tchauzinho",
    "adeus",
    "bye",
    "bye bye",
    "fui",
    "falou",
    "flw",
    "vlw",
    "valeu",
    "...",
    "♪",
    "♫",
    "música",
    "musica",
    "aplausos",
    "risos",
    "palmas",
    "[música]",
    "[musica]",
    "[aplausos]",
    "[risos]",
    "[silêncio]",
    "canal",
    "no canal",
    "meu canal",
    "nosso canal",
    "link na descrição",
    "link na descricao",
    "descrição do vídeo",
    "ativa o sininho",
    "sininho",
    "notificação",
    "notificacoes",
    "continua comigo",
    "fica comigo",
    "vem comigo",
    "fala galera",
    "fala pessoal",
    "e aí galera",
    "e ai galera",
    "fala turma",
    "e aí pessoal",
    "e ai pessoal",
    "opa pessoal",
    "bom dia",
    "boa tarde",
    "boa noite",
    "boa madrugada",
    "tamo junto",
    "tmj",
    "partiu",
    "bora",
    "bora lá",
    "próximo vídeo",
    "proximo video",
    "próximo episódio",
    "temporada",
    "episódio",
    "capitulo",
    "patrocinador",
    "patrocínio",
    "apoio",
    "parceria",
    "cupom",
    "desconto",
    "promoção",
    "promocao",
    "globo",
    "record",
    "sbt",
    "band",
    "redetv",
    "jornal",
    "telejornal",
    "plantão",
    "plantao",
    "intervalo",
    "comercial",
    "propaganda",
    "voltamos",
    "voltaremos",
    "após o intervalo",
    "aguarde",
    "aguardem",
    "não saia daí",
    "nao saia dai",
    "continue assistindo",
    "fique ligado",
    "fica ligado",
    "acompanhe",
    "acompanha",
    "assista",
    "assiste",
    "muito obrigado",
    "muito obrigada",
    "agradeço",
    "agradeco",
    "beijo",
    "beijinho",
    "abraço",
    "abraco",
    "nos vemos",
    "a gente se vê",
    "a gente se ve",
    "volto já",
    "volto ja",
    "já volto",
    "ja volto",
]

RATE_LIMITER_CONFIG = {
    "QUOTA_LIMIT": int(os.getenv("RATE_QUOTA_LIMIT", "15")),
    "SAFETY_MARGIN": int(os.getenv("RATE_SAFETY_MARGIN", "2")),
    "WINDOW_SECONDS": int(os.getenv("RATE_WINDOW_SECONDS", "60")),
    "MAX_REQUESTS_PER_MINUTE": int(os.getenv("RATE_MAX_RPM", "15")),
}

CACHE_CONFIG = {
    "SIMILARITY_THRESHOLD": float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.80")),
    "MAX_SIZE": int(os.getenv("CACHE_MAX_SIZE", "200")),
    "TTL_SECONDS": int(os.getenv("CACHE_TTL_SECONDS", "7200")),
}

QUEUE_CONFIG = {
    "AUDIO_INPUT": int(os.getenv("QUEUE_AUDIO_INPUT", "100")),
    "TRANSCRIPTION": int(os.getenv("QUEUE_TRANSCRIPTION", "50")),
    "PROCESSING": int(os.getenv("QUEUE_PROCESSING", "20")),
    "RESPONSE": int(os.getenv("QUEUE_RESPONSE", "10")),
    "TTS": int(os.getenv("QUEUE_TTS", "30")),
    "ANIMATION": int(os.getenv("QUEUE_ANIMATION", "20")),
    "VISION": int(os.getenv("QUEUE_VISION", "5")),
    "WAKE_WORD": int(os.getenv("QUEUE_WAKE_WORD", "50")),
}

WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
WAKE_WORD_COOLDOWN = float(os.getenv("WAKE_WORD_COOLDOWN", "2.0"))


def get_wake_word_patterns(entity_id: str = None) -> list:
    if entity_id is None:
        entity_id = get_current_entity_id()
    name = entity_id.lower()
    return [
        name,
        f"{name}inha",
        f"o {name}",
        f"ei {name}",
        f"oi {name}",
        f"{name} esta ai",
        f"{name} pode",
        f"{name} tenho",
        f"fala {name}",
        f"{name} me ajuda",
        f"{name} ajuda",
    ]


def get_tray_icon_path(entity_id: str = None) -> pathlib.Path:
    if entity_id is None:
        entity_id = get_current_entity_id()
    entity_icon = APP_DIR / "src" / "assets" / "icons" / f"{entity_id.lower()}_tray.png"
    if entity_icon.exists():
        return entity_icon
    return APP_DIR / "src" / "assets" / "icons" / f"{DEFAULT_ENTITY}_tray.png"


WAKE_WORD_PATTERNS = get_wake_word_patterns(DEFAULT_ENTITY)

DAEMON_MODE = os.getenv("DAEMON_MODE", "false").lower() == "true"
TRAY_ICON_PATH = get_tray_icon_path(DEFAULT_ENTITY)
MINIMIZE_TO_TRAY = os.getenv("MINIMIZE_TO_TRAY", "true").lower() == "true"
START_MINIMIZED = os.getenv("START_MINIMIZED", "false").lower() == "true"

DESKTOP_INTEGRATION = {
    "enabled": os.getenv("DESKTOP_INTEGRATION", "true").lower() == "true",
    "notifications": os.getenv("DESKTOP_NOTIFICATIONS", "true").lower() == "true",
    "clipboard": os.getenv("DESKTOP_CLIPBOARD", "true").lower() == "true",
    "active_window": os.getenv("DESKTOP_ACTIVE_WINDOW", "true").lower() == "true",
    "idle_detection": os.getenv("DESKTOP_IDLE", "true").lower() == "true",
    "proactivity": os.getenv("DESKTOP_PROACTIVITY", "true").lower() == "true",
    "idle_threshold": int(os.getenv("DESKTOP_IDLE_THRESHOLD", "300")),
    "proactive_interval": int(os.getenv("DESKTOP_PROACTIVE_INTERVAL", "30")),
}

DATA_MEMORY_DIR = APP_DIR / "src" / "data_memory"
USER_DATA_DIR = DATA_MEMORY_DIR / "user"
VOICE_SIMILARITY_THRESHOLD = float(os.getenv("VOICE_SIMILARITY_THRESHOLD", "0.75"))
ENABLE_SPEAKER_ID = os.getenv("ENABLE_SPEAKER_ID", "true").lower() == "true"

os.makedirs(USER_DATA_DIR, exist_ok=True)

MONITOR_CONFIG = {
    "INTERVAL": float(os.getenv("MONITOR_INTERVAL", "30.0")),
    "THREAD_TIMEOUT": float(os.getenv("THREAD_TIMEOUT", "5.0")),
}

FRAME_RATE = float(os.getenv("LUNA_ANIM_FPS", "24.0"))
ANIM_FPS_OBSERVANDO = float(os.getenv("LUNA_ANIM_FPS_OBSERVANDO", "24.0"))
ANIM_FPS_VER = float(os.getenv("LUNA_ANIM_FPS_VER", "24.0"))

UI_CONFIG = {
    "FRAME_RATE": FRAME_RATE,
    "FPS_OBSERVANDO": ANIM_FPS_OBSERVANDO,
    "FPS_VER": ANIM_FPS_VER,
    "VIZ_FPS": int(os.getenv("VIZ_FPS", "24")),
    "VIZ_INTERVAL": float(os.getenv("VIZ_UPDATE_INTERVAL", "0.1")),
    "FONT_FAMILY": os.getenv("LUNA_ANIM_FONT_FAMILY", "Fira Code"),
    "FONT_SIZE": int(os.getenv("LUNA_ANIM_FONT_SIZE", "6")),
}

RESPONSE_MAX_CHARS = int(os.getenv("RESPONSE_MAX_CHARS", "3000"))
CODE_MAX_CHARS = int(os.getenv("CODE_MAX_CHARS", "3000"))
DOC_RESPONSE_MAX_CHARS = int(os.getenv("DOC_RESPONSE_MAX_CHARS", "3000"))

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LUNA_COLORS = ["#bd93f9", "#ff79c9", "#8be9fd", "#50fa7b", "#f1fa8c", "#ffb86c"]
DENSITY_MAP_CHARS = "@%#*+=-:. "
COLOR_MAP = {char: LUNA_COLORS[i % len(LUNA_COLORS)] for i, char in enumerate(DENSITY_MAP_CHARS)}


VOICE_SETTINGS = {"ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID", "")}

ELEVENLABS_VOICE_ID = VOICE_SETTINGS["ELEVENLABS_VOICE_ID"]

webcam_index_str = os.getenv("WEBCAM_INDEX", "0")
try:
    webcam_index_from_env = int(webcam_index_str)
except ValueError:
    webcam_index_from_env = 0

DEVICE_SETTINGS = {"WEBCAM_INDEX": webcam_index_from_env}

VISION_CONFIG = {"CAMERA_INDEX": webcam_index_from_env}


EMOTIONS = [
    "apaixonada",
    "curiosa",
    "feliz",
    "flertando",
    "neutra",
    "irritada",
    "medrosa",
    "observando",
    "obssecada",
    "sarcastica",
    "sensualizando",
    "travessa",
    "triste",
    "piscando",
]

EMOTION_ALIASES = {
    "indiferente": "neutra",
    "obcecada": "obssecada",
    "sarcástica": "sarcastica",
    "seduzindo": "sensualizando",
}


def get_emotion_map(entity_name: str = None) -> dict:
    if entity_name is None:
        entity_name = get_current_entity_id().capitalize()

    entity_anim_dir = ENTITIES_DIR / entity_name.lower() / "animations"
    fallback_dir = ENTITIES_DIR / DEFAULT_ENTITY / "animations"

    emotion_map = {}
    emotion_labels = {
        "apaixonada": "apaixonada",
        "curiosa": "curiosa",
        "feliz": "feliz",
        "flertando": "flertando",
        "indiferente": "neutra",
        "irritada": "irritada",
        "medrosa": "medrosa",
        "observando": "observando",
        "obcecada": "obssecada",
        "sarcástica": "sarcastica",
        "seduzindo": "sensualizando",
        "travessa": "travessa",
        "triste": "triste",
    }

    for emotion_key, file_suffix in emotion_labels.items():
        entity_file = entity_anim_dir / f"{entity_name}_{file_suffix}.txt"
        entity_file_gz = entity_anim_dir / f"{entity_name}_{file_suffix}.txt.gz"
        fallback_file = fallback_dir / f"{DEFAULT_ENTITY.capitalize()}_{file_suffix}.txt"
        fallback_file_gz = fallback_dir / f"{DEFAULT_ENTITY.capitalize()}_{file_suffix}.txt.gz"

        if entity_file.exists():
            emotion_map[emotion_key] = entity_file
        elif entity_file_gz.exists():
            emotion_map[emotion_key] = entity_file_gz
        elif fallback_file.exists():
            emotion_map[emotion_key] = fallback_file
        elif fallback_file_gz.exists():
            emotion_map[emotion_key] = fallback_file_gz
        else:
            emotion_map[emotion_key] = fallback_dir / f"{DEFAULT_ENTITY.capitalize()}_{file_suffix}.txt"

    return emotion_map


def get_animation_to_emotion(entity_name: str = None) -> dict:
    if entity_name is None:
        entity_name = get_current_entity_id().capitalize()
    emotions = [
        ("apaixonada", "apaixonada"),
        ("curiosa", "curiosa"),
        ("feliz", "feliz"),
        ("flertando", "flertando"),
        ("neutra", "indiferente"),
        ("irritada", "irritada"),
        ("medrosa", "medrosa"),
        ("observando", "observando"),
        ("obssecada", "obcecada"),
        ("sarcastica", "sarcástica"),
        ("sensualizando", "seduzindo"),
        ("travessa", "travessa"),
        ("triste", "triste"),
    ]
    return {f"{entity_name}_{anim}": emotion for anim, emotion in emotions}


def get_personality_prompts(entity_name: str = None) -> dict:
    if entity_name is None:
        entity_name = get_current_entity_id().capitalize()
    return {
        "observando": f"Voce e {entity_name}. Responda de forma neutra, observadora e concisa.",
        "feliz": f"Voce e {entity_name}. Responda de uma maneira muito entusiasmada e otimista.",
        "triste": f"Voce e {entity_name}. Responda de forma melancolica e breve.",
        "irritada": f"Voce e {entity_name}. Responda de forma curta, rispida e com um sarcasmo afiado.",
        "curiosa": f"Voce e {entity_name}. Responda sempre com uma pergunta.",
        "seduzindo": f"Voce e {entity_name}. Responda com um tom charmoso e sugestivo.",
        "apaixonada": f"Voce e {entity_name}. Responda de forma calorosa e afetuosa.",
        "flertando": f"Voce e {entity_name}. Responda de forma leve e brincalhona.",
        "indiferente": f"Voce e {entity_name}. Responda de forma apatica e desinteressada.",
        "obcecada": f"Voce e {entity_name}. Responda com um foco intenso no usuario ou no topico.",
        "sarcástica": f"Voce e {entity_name}. Responda com ironia e inteligencia.",
        "medrosa": f"Voce e {entity_name}. Responda com receio, hesitacao e vulnerabilidade.",
        "travessa": f"Voce e {entity_name}. Responda de forma provocadora, maliciosa e brincalhona.",
    }


EMOTION_MAP = get_emotion_map(DEFAULT_ENTITY.capitalize())
PERSONALITY_PROMPTS = get_personality_prompts(DEFAULT_ENTITY.capitalize())

TTS_EMOTION_DEFAULTS = {
    "feliz": {"speed": 1.1, "stability": 0.4},
    "triste": {"speed": 0.9, "stability": 0.7},
    "irritada": {"speed": 1.2, "stability": 0.3},
    "sarcástica": {"speed": 1.05, "stability": 0.5},
    "flertando": {"speed": 0.95, "stability": 0.4},
    "apaixonada": {"speed": 0.9, "stability": 0.6},
    "curiosa": {"speed": 1.1, "stability": 0.5},
    "observando": {"speed": 1.0, "stability": 0.6},
    "indiferente": {"speed": 0.95, "stability": 0.8},
    "obcecada": {"speed": 1.15, "stability": 0.3},
    "seduzindo": {"speed": 0.85, "stability": 0.5},
    "medrosa": {"speed": 0.9, "stability": 0.4},
    "travessa": {"speed": 1.1, "stability": 0.35},
}

ANIMATION_TO_EMOTION = get_animation_to_emotion(DEFAULT_ENTITY.capitalize())


def get_action_animations(entity_name: str = None) -> dict:
    if entity_name is None:
        entity_name = get_current_entity_id().capitalize()

    entity_anim_dir = ENTITIES_DIR / entity_name.lower() / "animations"
    fallback_dir = ENTITIES_DIR / DEFAULT_ENTITY / "animations"

    entity_file = entity_anim_dir / f"{entity_name}_piscando.txt"
    entity_file_gz = entity_anim_dir / f"{entity_name}_piscando.txt.gz"
    fallback_file = fallback_dir / f"{DEFAULT_ENTITY.capitalize()}_piscando.txt"
    fallback_file_gz = fallback_dir / f"{DEFAULT_ENTITY.capitalize()}_piscando.txt.gz"

    if entity_file.exists():
        piscando_path = entity_file
    elif entity_file_gz.exists():
        piscando_path = entity_file_gz
    elif fallback_file.exists():
        piscando_path = fallback_file
    elif fallback_file_gz.exists():
        piscando_path = fallback_file_gz
    else:
        piscando_path = fallback_file

    return {"piscando": piscando_path}


ACTION_ANIMATIONS = get_action_animations(DEFAULT_ENTITY.capitalize())


# ============================================
# CONFIGURACOES DE EFEITOS VISUAIS (GLITCH)
# ============================================

GLITCH_CONFIG = {
    "PISCANDO_FPS": float(os.getenv("GLITCH_PISCANDO_FPS", "24.0")),
    "TV_TRANSITION_DURATION": float(os.getenv("GLITCH_TV_DURATION", "1.2")),
    "EFFECT_DURATION_AVG": float(os.getenv("GLITCH_EFFECT_DURATION", "0.3")),
    "EFFECT_INTERVAL": float(os.getenv("GLITCH_EFFECT_INTERVAL", "0.15")),
    "BANNER_TRIGGER": float(os.getenv("GLITCH_BANNER_TRIGGER", "0.94")),
    "BUTTON_TRIGGER": float(os.getenv("GLITCH_BUTTON_TRIGGER", "0.92")),
}

GLITCH_PALETTES = {
    "dracula": {
        "tv_base": ["#333333", "#444444", "#555555", "#666666"],
        "tv_accent": "#bd93f9",
        "text_primary": "#ff79c6",
        "text_secondary": "#8be9fd",
    },
    "neon": {
        "tv_base": ["#0a0a0a", "#1a1a1a", "#2a2a2a", "#3a3a3a"],
        "tv_accent": "#00ff00",
        "text_primary": "#ff00ff",
        "text_secondary": "#00ffff",
    },
    "monokai": {
        "tv_base": ["#272822", "#383830", "#49483e", "#5a5950"],
        "tv_accent": "#a6e22e",
        "text_primary": "#f92672",
        "text_secondary": "#66d9ef",
    },
    "blood": {
        "tv_base": ["#1a0000", "#2a0000", "#3a0000", "#4a0000"],
        "tv_accent": "#ff0000",
        "text_primary": "#ff3333",
        "text_secondary": "#ff6666",
    },
}

GLITCH_PALETTE = os.getenv("GLITCH_PALETTE", "dracula")
GLITCH_COLORS = GLITCH_PALETTES.get(GLITCH_PALETTE, GLITCH_PALETTES["dracula"])


# ============================================
# VALIDAÇÕES
# ============================================

_missing_vars = []
if not GOOGLE_API_KEY:
    _missing_vars.append("GOOGLE_API_KEY")
if TTS_ENGINE == "elevenlabs" and not ELEVENLABS_API_KEY:
    _missing_vars.append("ELEVENLABS_API_KEY")


def reload_config():
    """Recarrega todas as configuracoes do .env."""
    global GOOGLE_API_KEY, ELEVENLABS_API_KEY, TTS_ENGINE
    global COQUI_DEVICE, CHATTERBOX_DEVICE
    global WHISPER_CONFIG, AUDIO_CONFIG, VAD_CONFIG, GEMINI_CONFIG
    global RATE_LIMITER_CONFIG, CACHE_CONFIG, FRAME_RATE, UI_CONFIG
    global DEBUG_MODE, VOICE_SETTINGS, ELEVENLABS_VOICE_ID
    global DEVICE_SETTINGS, VISION_CONFIG
    global TTS_PROVIDER, TTS_LOCAL, TTS_ELEVENLABS
    global STT_PROVIDER, STT_LOCAL
    global VISION_PROVIDER, VISION_LOCAL, VISION_GEMINI
    global CHAT_PROVIDER, CHAT_LOCAL, CHAT_GEMINI
    global CODE_PROVIDER, CODE_LOCAL, CODE_API, OLLAMA_CONFIG
    global GLITCH_CONFIG, GLITCH_PALETTE, GLITCH_COLORS

    load_dotenv(_env_path, override=True)

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    TTS_ENGINE = os.getenv("TTS_ENGINE", "coqui")

    COQUI_DEVICE = os.getenv("COQUI_DEVICE", "cuda")
    CHATTERBOX_DEVICE = os.getenv("CHATTERBOX_DEVICE", "cuda")

    WHISPER_CONFIG.update(
        {
            "MODEL_SIZE": os.getenv("WHISPER_MODEL_SIZE", "small"),
            "COMPUTE_TYPE": os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
            "USE_GPU": os.getenv("USE_GPU", "true").lower() == "true",
        }
    )

    AUDIO_CONFIG.update(
        {
            "DEVICE_ID": int(os.getenv("AUDIO_DEVICE_ID", "0")),
        }
    )

    VAD_CONFIG.update(
        {
            "SILENCE_DURATION": float(os.getenv("VAD_SILENCE_DURATION", "0.8")),
            "ENERGY_THRESHOLD": int(os.getenv("VAD_ENERGY_THRESHOLD", "6000")),
            "STRATEGY": os.getenv("VAD_STRATEGY", "energy"),
            "AUTO_ADJUST": os.getenv("VAD_AUTO_ADJUST", "true").lower() == "true",
            "NOISE_MULTIPLIER": float(os.getenv("VAD_NOISE_MULTIPLIER", "2.0")),
            "CALIBRATION_SECONDS": float(os.getenv("VAD_CALIBRATION_SECONDS", "3.0")),
            "MIN_THRESHOLD": int(os.getenv("VAD_MIN_THRESHOLD", "500")),
            "MAX_THRESHOLD": int(os.getenv("VAD_MAX_THRESHOLD", "15000")),
        }
    )

    GEMINI_CONFIG.update(
        {
            "MODEL_NAME": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            "TIMEOUT": int(os.getenv("GEMINI_TIMEOUT", "30")),
        }
    )

    RATE_LIMITER_CONFIG.update(
        {
            "MAX_REQUESTS_PER_MINUTE": int(os.getenv("RATE_MAX_RPM", "15")),
        }
    )

    CACHE_CONFIG.update(
        {
            "TTL_SECONDS": int(os.getenv("CACHE_TTL_SECONDS", "7200")),
        }
    )

    FRAME_RATE = float(os.getenv("LUNA_ANIM_FPS", "24.0"))
    UI_CONFIG["FRAME_RATE"] = FRAME_RATE

    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

    VOICE_SETTINGS["ELEVENLABS_VOICE_ID"] = os.getenv("ELEVENLABS_VOICE_ID", "")
    ELEVENLABS_VOICE_ID = VOICE_SETTINGS["ELEVENLABS_VOICE_ID"]

    webcam_idx = int(os.getenv("WEBCAM_INDEX", "0"))
    DEVICE_SETTINGS["WEBCAM_INDEX"] = webcam_idx
    VISION_CONFIG["CAMERA_INDEX"] = webcam_idx

    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "local")
    TTS_LOCAL.update(
        {
            "engine": os.getenv("TTS_LOCAL_ENGINE", "coqui"),
            "coqui": {"reference_audio": COQUI_REFERENCE_AUDIO, "device": COQUI_DEVICE},
            "chatterbox": {"reference_audio": CHATTERBOX_REFERENCE_AUDIO},
        }
    )
    TTS_ELEVENLABS.update(
        {
            "api_key": ELEVENLABS_API_KEY,
            "voice_id": ELEVENLABS_VOICE_ID,
        }
    )

    CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "gemini")
    CHAT_LOCAL.update(
        {
            "model": os.getenv("CHAT_LOCAL_MODEL", "dolphin-mistral"),
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        }
    )
    CHAT_GEMINI.update(
        {
            "api_key": GOOGLE_API_KEY,
            "model": GEMINI_CONFIG["MODEL_NAME"],
        }
    )

    VISION_PROVIDER = os.getenv("VISION_PROVIDER", "gemini")
    VISION_LOCAL.update(
        {
            "model": os.getenv("VISION_LOCAL_MODEL", "minicpm-v"),
        }
    )

    CODE_PROVIDER = os.getenv("CODE_PROVIDER", "local")
    CODE_LOCAL.update(
        {
            "model": os.getenv("CODE_LOCAL_MODEL", "qwen2.5-coder:7b"),
        }
    )

    OLLAMA_CONFIG.update(
        {
            "BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "MODELS": {
                "chat": CHAT_LOCAL["model"],
                "code": CODE_LOCAL["model"],
                "vision": VISION_LOCAL["model"],
            },
        }
    )

    GLITCH_CONFIG.update(
        {
            "PISCANDO_FPS": float(os.getenv("GLITCH_PISCANDO_FPS", "24.0")),
            "TV_TRANSITION_DURATION": float(os.getenv("GLITCH_TV_DURATION", "1.2")),
            "EFFECT_DURATION_AVG": float(os.getenv("GLITCH_EFFECT_DURATION", "0.3")),
            "EFFECT_INTERVAL": float(os.getenv("GLITCH_EFFECT_INTERVAL", "0.15")),
            "BANNER_TRIGGER": float(os.getenv("GLITCH_BANNER_TRIGGER", "0.94")),
            "BUTTON_TRIGGER": float(os.getenv("GLITCH_BUTTON_TRIGGER", "0.92")),
        }
    )

    GLITCH_PALETTE = os.getenv("GLITCH_PALETTE", "dracula")
    GLITCH_COLORS = GLITCH_PALETTES.get(GLITCH_PALETTE, GLITCH_PALETTES["dracula"])

    global RESPONSE_MAX_CHARS, CODE_MAX_CHARS, DOC_RESPONSE_MAX_CHARS
    RESPONSE_MAX_CHARS = int(os.getenv("RESPONSE_MAX_CHARS", "3000"))
    CODE_MAX_CHARS = int(os.getenv("CODE_MAX_CHARS", "3000"))
    DOC_RESPONSE_MAX_CHARS = int(os.getenv("DOC_RESPONSE_MAX_CHARS", "3000"))


def reload_entity_config(entity_name: str) -> None:
    global EMOTION_MAP, ANIMATION_TO_EMOTION, PERSONALITY_PROMPTS, ACTION_ANIMATIONS
    global SOUL_FILE_PATH, ASCII_ART_DIR, WAKE_WORD_PATTERNS, TRAY_ICON_PATH
    global COQUI_REFERENCE_AUDIO, COQUI_SPEAKER_EMBEDDING, CHATTERBOX_REFERENCE_AUDIO

    entity_id = entity_name.lower()

    EMOTION_MAP = get_emotion_map(entity_name)
    ANIMATION_TO_EMOTION = get_animation_to_emotion(entity_name)
    PERSONALITY_PROMPTS = get_personality_prompts(entity_name)
    ACTION_ANIMATIONS = get_action_animations(entity_name)
    SOUL_FILE_PATH = get_soul_path(entity_id)
    ASCII_ART_DIR = get_animations_dir(entity_id)
    WAKE_WORD_PATTERNS = get_wake_word_patterns(entity_id)
    TRAY_ICON_PATH = get_tray_icon_path(entity_id)
    COQUI_REFERENCE_AUDIO = get_coqui_reference_audio(entity_id)
    COQUI_SPEAKER_EMBEDDING = get_coqui_speaker_embedding(entity_id)
    CHATTERBOX_REFERENCE_AUDIO = get_chatterbox_reference_audio(entity_id)

    try:
        from src.ui.colors import invalidate_color_cache

        invalidate_color_cache()
    except ImportError:
        pass


def print_config_debug(entity_name: str = None):
    if entity_name is None:
        entity_name = get_current_entity_id().capitalize()
    print(f"\n=== CONFIGURACAO {entity_name.upper()} ===")
    print(f"TTS_ENGINE: {TTS_ENGINE}")
    print(f"WHISPER_MODEL: {WHISPER_CONFIG['MODEL_SIZE']}")
    print(f"AUDIO_DEVICE: {AUDIO_CONFIG['DEVICE_ID']}")
    print(f"SAMPLE_RATE: {AUDIO_CONFIG['SAMPLE_RATE']}")
    print(f"USE_GPU: {WHISPER_CONFIG['USE_GPU']}")
    print(f"GEMINI_MODEL: {GEMINI_CONFIG['MODEL_NAME']}")
    print(f"WEBCAM_INDEX: {VISION_CONFIG['CAMERA_INDEX']}")
    print(f"SOUL_FILE: {SOUL_FILE_PATH}")
    print("========================\n")


# ═══════════════════════════════════════════════════════════════
# CONFIGURACAO DE PROVIDERS - LOCAL vs PAGO
# ═══════════════════════════════════════════════════════════════
# Cada funcionalidade pode usar modelo local (gratis) ou API paga
# Para usar local: defina PROVIDER=local no .env
# Para usar API: defina PROVIDER=<nome_servico> e configure a API key

# ─────────────────────────────────────────────────────────────────
# VOZ (TTS) - Text to Speech
# ─────────────────────────────────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "local")

TTS_LOCAL = {
    "engine": os.getenv("TTS_LOCAL_ENGINE", "coqui"),
    "coqui": {
        "model": COQUI_MODEL_NAME,
        "reference_audio": COQUI_REFERENCE_AUDIO,
        "speaker_embedding": COQUI_SPEAKER_EMBEDDING,
        "device": COQUI_DEVICE,
    },
    "chatterbox": {
        "reference_audio": CHATTERBOX_REFERENCE_AUDIO,
        "device": CHATTERBOX_DEVICE,
    },
    "fallback_order": ["coqui", "chatterbox"],
}

TTS_ELEVENLABS = {
    "api_key": ELEVENLABS_API_KEY,
    "voice_id": ELEVENLABS_VOICE_ID,
    "model_id": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
}

# ─────────────────────────────────────────────────────────────────
# OUVIDO (STT) - Speech to Text
# ─────────────────────────────────────────────────────────────────
STT_PROVIDER = os.getenv("STT_PROVIDER", "local")

STT_LOCAL = {
    "engine": "faster-whisper",
    "model": WHISPER_CONFIG["MODEL_SIZE"],
    "language": os.getenv("STT_LANGUAGE", "pt"),
    "compute_type": WHISPER_CONFIG["COMPUTE_TYPE"],
    "use_gpu": WHISPER_CONFIG["USE_GPU"],
}

STT_OPENAI = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "whisper-1",
}

# ─────────────────────────────────────────────────────────────────
# VISAO - Analise de imagens
# ─────────────────────────────────────────────────────────────────
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "gemini")

VISION_LOCAL = {
    "engine": "ollama",
    "model": os.getenv("VISION_LOCAL_MODEL", "minicpm-v"),
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
}

VISION_GEMINI = {
    "api_key": GOOGLE_API_KEY,
    "model": os.getenv("VISION_GEMINI_MODEL", "gemini-1.5-flash"),
}

# ─────────────────────────────────────────────────────────────────
# CONVERSA (Persona Luna) - Chat principal
# ─────────────────────────────────────────────────────────────────
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "gemini")

CHAT_LOCAL = {
    "engine": "ollama",
    "model": os.getenv("CHAT_LOCAL_MODEL", "dolphin-mistral"),
    "fallback_model": os.getenv("CHAT_FALLBACK_MODEL", "llama3.2:3b"),
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "temperature": float(os.getenv("CHAT_LOCAL_TEMPERATURE", "0.85")),
    "max_tokens": int(os.getenv("CHAT_LOCAL_MAX_TOKENS", "1024")),
    "context_length": int(os.getenv("CHAT_LOCAL_CONTEXT", "8192")),
    "timeout": int(os.getenv("CHAT_LOCAL_TIMEOUT", "60")),
}

CHAT_GEMINI = {
    "api_key": GOOGLE_API_KEY,
    "model": GEMINI_CONFIG["MODEL_NAME"],
    "temperature": float(os.getenv("CHAT_GEMINI_TEMPERATURE", "0.9")),
}

# ─────────────────────────────────────────────────────────────────
# GEMINI LIVE - Streaming de audio bidirecional
# ─────────────────────────────────────────────────────────────────
GEMINI_LIVE_CONFIG = {
    "ENABLED": os.getenv("GEMINI_LIVE_ENABLED", "false").lower() == "true",
    "MODEL": os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp"),
    "VOICE_NAME": os.getenv("GEMINI_LIVE_VOICE", "Aoede"),
    "SAMPLE_RATE": int(os.getenv("GEMINI_LIVE_SAMPLE_RATE", "16000")),
}

# ─────────────────────────────────────────────────────────────────
# CODIGO - Geracao e analise de codigo
# ─────────────────────────────────────────────────────────────────
CODE_PROVIDER = os.getenv("CODE_PROVIDER", "local")

CODE_LOCAL = {
    "engine": "ollama",
    "model": os.getenv("CODE_LOCAL_MODEL", "qwen2.5-coder:7b"),
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "temperature": float(os.getenv("CODE_LOCAL_TEMPERATURE", "0.3")),
    "max_tokens": int(os.getenv("CODE_LOCAL_MAX_TOKENS", "4096")),
}

CODE_API = {
    "provider": os.getenv("CODE_API_PROVIDER", "deepseek"),
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "model": os.getenv("CODE_API_MODEL", "deepseek-coder"),
}

# ─────────────────────────────────────────────────────────────────
# OLLAMA - Configuracao geral
# ─────────────────────────────────────────────────────────────────
OLLAMA_CONFIG = {
    "BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "TIMEOUT": int(os.getenv("OLLAMA_TIMEOUT", "120")),
    "NUM_CTX": int(os.getenv("OLLAMA_NUM_CTX", "8192")),
    "NUM_GPU": int(os.getenv("OLLAMA_NUM_GPU", "-1")),
    "KEEP_ALIVE": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
    "MODELS": {
        "chat": CHAT_LOCAL["model"],
        "code": CODE_LOCAL["model"],
        "vision": VISION_LOCAL["model"],
    },
}


def init_entity_config() -> str:
    profile_path = APP_DIR / "src" / "data_memory" / "user" / "profile.json"
    entity_id = "luna"

    if profile_path.exists():
        try:
            from src.core.file_lock import read_json_safe

            profile = read_json_safe(profile_path)
            entity_id = profile.get("active_entity", "luna")
        except Exception:
            pass

    entity_name = entity_id.capitalize()
    reload_entity_config(entity_name)
    return entity_id


ACTIVE_ENTITY_ID = init_entity_config()


def has_premium_tts() -> bool:
    return bool(ELEVENLABS_API_KEY)


def has_premium_vision() -> bool:
    return bool(GOOGLE_API_KEY)


def has_premium_chat() -> bool:
    return bool(GOOGLE_API_KEY)


def get_available_providers() -> dict:
    return {
        "tts": {
            "elevenlabs": has_premium_tts(),
            "coqui": True,
            "chatterbox": True,
        },
        "vision": {
            "gemini": has_premium_vision(),
            "local": True,
        },
        "chat": {
            "gemini": has_premium_chat(),
            "local": True,
        },
    }
