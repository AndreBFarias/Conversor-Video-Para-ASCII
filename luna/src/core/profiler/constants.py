PIPELINE_STAGES = [
    "audio_capture",
    "vad",
    "stt.whisper",
    "stt.preprocess",
    "stt.inference",
    "llm.process",
    "llm.request",
    "tts.generate",
    "tts.playback",
    "animation",
    "ui.update",
]

LATENCY_THRESHOLDS = {
    "audio_capture": 50,
    "vad": 30,
    "stt.whisper": 2000,
    "stt.preprocess": 100,
    "stt.inference": 1500,
    "llm.process": 3000,
    "llm.request": 2500,
    "tts.generate": 2000,
    "tts.playback": 5000,
    "animation": 50,
    "ui.update": 100,
    "pipeline": 8000,
}

RECOMMENDATIONS = {
    "stt.whisper": "Considere usar modelo menor (tiny/base) ou habilitar GPU",
    "stt.inference": "Whisper lento: verifique GPU/compute_type no config",
    "llm.process": "LLM lento: considere cache semantico ou modelo local",
    "llm.request": "API lenta: verifique conexao ou use Ollama local",
    "tts.generate": "TTS lento: considere Piper (mais leve) ou pre-cache",
    "tts.playback": "Playback lento: verifique dispositivo de audio",
    "vad": "VAD lento: ajuste threshold de energia",
    "pipeline": "Pipeline total lento: analise estagios individuais",
}
