import re
import time


def test_config() -> str:
    import config

    checks = []

    if config.GOOGLE_API_KEY:
        checks.append("GOOGLE_API_KEY: configurada")
    else:
        checks.append("GOOGLE_API_KEY: NAO CONFIGURADA")

    checks.append(f"CHAT_PROVIDER: {config.CHAT_PROVIDER}")
    checks.append(f"TTS_ENGINE: {config.TTS_ENGINE}")
    checks.append(f"WHISPER_MODEL: {config.WHISPER_CONFIG.get('MODEL_SIZE', 'N/A')}")

    return " | ".join(checks)


def test_threading_manager() -> str:
    from src.soul.threading_manager import LunaThreadingManager, RingBuffer

    manager = LunaThreadingManager()

    rb = RingBuffer(maxsize=10, name="test")
    for i in range(15):
        rb.put(i)

    stats = rb.get_stats()
    assert stats["drops"] == 5, f"RingBuffer drops incorreto: {stats['drops']}"

    assert manager.audio_input_queue is not None
    assert manager.transcription_queue is not None
    assert manager.response_queue is not None

    return f"Filas: {len(manager.get_queue_sizes())} | RingBuffer: {stats}"


def test_profiler() -> str:
    from src.core.profiler import get_pipeline_logger, get_profiler

    profiler = get_profiler()
    plog = get_pipeline_logger()

    interaction_id = plog.new_interaction("teste diagnostico")
    with profiler.span("test.span1"):
        time.sleep(0.1)

    with profiler.span("test.span2"):
        time.sleep(0.05)

    plog.end_interaction("resposta teste")

    summary = profiler.get_stage_summary()
    assert "test.span1" in summary, "Span1 nao registrado"
    assert "test.span2" in summary, "Span2 nao registrado"

    return f"Spans: {len(summary)} | Interaction ID: {interaction_id}"


def test_whisper_load() -> str:
    import config

    model_size = config.WHISPER_CONFIG.get("MODEL_SIZE", "tiny")
    compute_type = config.WHISPER_CONFIG.get("COMPUTE_TYPE", "float16")

    start = time.time()
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device="cuda", compute_type=compute_type)
        load_time = time.time() - start
        del model
        return f"Modelo '{model_size}' carregado em {load_time:.2f}s (CUDA)"
    except Exception as e:
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            load_time = time.time() - start
            del model
            return f"Modelo '{model_size}' carregado em {load_time:.2f}s (CPU fallback)"
        except Exception as e2:
            raise Exception(f"Whisper falhou: CUDA={e}, CPU={e2}")


def test_audio_devices() -> str:
    import pyaudio

    p = pyaudio.PyAudio()
    devices = []

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append(f"{i}: {info['name'][:30]}")

    p.terminate()

    if not devices:
        raise Exception("Nenhum dispositivo de entrada encontrado")

    return f"{len(devices)} dispositivos de audio: {devices[:3]}"


def test_tts_engine() -> str:
    import config

    engine = config.TTS_ENGINE

    if engine == "piper":
        return "Piper configurado (lightweight)"
    elif engine == "elevenlabs":
        if config.ELEVENLABS_API_KEY:
            return "ElevenLabs configurado com API key"
        else:
            raise Exception("ElevenLabs sem API key")
    elif engine == "coqui":
        return f"Coqui XTTS configurado (device: {config.COQUI_DEVICE})"
    else:
        return f"Engine: {engine}"


def test_gemini_connection() -> str:
    import config

    if not config.GOOGLE_API_KEY:
        return "GOOGLE_API_KEY nao configurada (pulando teste)"

    from google import genai

    client = genai.Client(api_key=config.GOOGLE_API_KEY)

    start = time.time()
    response = client.models.generate_content(
        model=config.GEMINI_CONFIG.get("MODEL_NAME", "gemini-2.0-flash"), contents="Diga apenas: OK"
    )
    latency = time.time() - start

    return f"Gemini respondeu em {latency:.2f}s: '{response.text[:30]}...'"


def test_ollama_connection() -> str:
    from src.core.ollama_client import OllamaSyncClient

    client = OllamaSyncClient()

    if not client.check_health():
        return "Ollama nao disponivel (pulando teste)"

    models = client.list_models()
    return f"Ollama OK. Modelos: {len(models)}"


def test_animation_frames() -> str:
    import config

    anim_dir = config.ASCII_ART_DIR
    if not anim_dir.exists():
        raise Exception(f"Diretorio de animacoes nao existe: {anim_dir}")

    anim_files = list(anim_dir.glob("Luna_*.txt"))
    if not anim_files:
        raise Exception("Nenhum arquivo de animacao encontrado")

    emotions = [f.stem for f in anim_files]

    total_frames = 0
    for f in anim_files:
        content = f.read_text()
        frames = content.count("[FRAME]") or 1
        total_frames += frames

    return f"{len(emotions)} emocoes, {total_frames} frames: {emotions[:5]}"


def test_react_pattern() -> str:
    pattern = re.compile(r"/(rea[cç]?[aã]?o?|react)\s+(Luna_\w+)", re.IGNORECASE)

    tests = [
        ("/react Luna_feliz ola", True, "Luna_feliz"),
        ("/reacao Luna_triste teste", True, "Luna_triste"),
        ("/reação Luna_irritada x", True, "Luna_irritada"),
        ("ola mundo", False, None),
        ("[Reação:Luna_feliz]", False, None),
    ]

    for text, should_match, expected_anim in tests:
        m = pattern.search(text)
        matched = m is not None
        if matched != should_match:
            raise Exception(f"Falha em '{text}': esperava match={should_match}, obteve {matched}")
        if matched and m.group(2) != expected_anim:
            raise Exception(f"Animacao errada em '{text}': esperava {expected_anim}, obteve {m.group(2)}")

    return f"Todos {len(tests)} testes OK"


def test_emotion_mapping() -> str:
    import config

    issues = []

    for anim_key, emotion_val in config.ANIMATION_TO_EMOTION.items():
        if emotion_val not in config.EMOTION_MAP:
            issues.append(f"{anim_key} -> {emotion_val} NAO EXISTE em EMOTION_MAP")
        else:
            path = config.EMOTION_MAP[emotion_val]
            if not path.exists():
                issues.append(f"{emotion_val} -> {path} NAO EXISTE")

    if issues:
        raise Exception(f"{len(issues)} problemas: {issues[:3]}")

    return f"Todas {len(config.ANIMATION_TO_EMOTION)} animacoes mapeadas corretamente"


def test_consciencia() -> str:
    from src.soul.consciencia import Consciencia

    c = Consciencia(app=None)
    provider = c.provider
    has_provider = c._has_provider()

    if not has_provider:
        return f"Provider: {provider} (offline - pulando teste)"

    result = c.process_interaction("diagnostico rapido", forced_animation="Luna_curiosa")

    if not result:
        raise Exception("Consciencia retornou None")

    fala = result.get("fala_tts", "")[:40]
    anim = result.get("animacao")

    if anim != "Luna_curiosa":
        raise Exception(f"forced_animation ignorado: esperava Luna_curiosa, obteve {anim}")

    return f"Provider: {provider} | Animacao: {anim} | Fala: {fala}..."


def test_tts_full() -> str:
    import config

    from src.soul.boca import Boca

    engine = config.TTS_ENGINE
    boca = Boca()

    if not boca._ready:
        return f"Boca ({engine}) nao inicializada (lazy load)"

    text = "Teste de voz"
    audio = boca.sintetizar(text)

    if audio is None:
        raise Exception("TTS retornou None")

    return f"Engine: {engine} | Audio gerado: {len(audio)} bytes"


def test_vad_config() -> str:
    import config

    vad_cfg = config.VAD_CONFIG

    checks = []
    checks.append(f"ENERGY_THRESHOLD: {vad_cfg.get('ENERGY_THRESHOLD', 'N/A')}")
    checks.append(f"SILENCE_FRAME_LIMIT: {vad_cfg.get('SILENCE_FRAME_LIMIT', 'N/A')}")
    checks.append(f"SMOOTHING_WINDOW: {vad_cfg.get('SMOOTHING_WINDOW', 'N/A')}")

    return " | ".join(checks)
