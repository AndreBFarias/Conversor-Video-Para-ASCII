import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def check_ollama():
    print("\n" + "=" * 60)
    print("1. VERIFICANDO OLLAMA")
    print("=" * 60)

    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"[OK] Ollama rodando com {len(models)} modelos:")
            for m in models:
                print(f"     - {m['name']}")
            return True
        else:
            print(f"[ERRO] Ollama retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERRO] Ollama nao acessivel: {e}")
        print("       Execute: ollama serve")
        return False


def check_config():
    print("\n" + "=" * 60)
    print("2. VERIFICANDO CONFIG")
    print("=" * 60)

    try:
        import config

        print(f"[OK] CHAT_PROVIDER: {config.CHAT_PROVIDER}")
        print(f"[OK] CHAT_LOCAL model: {config.CHAT_LOCAL.get('model', 'N/A')}")
        print(f"[OK] TTS_PROVIDER: {config.TTS_PROVIDER}")
        print(f"[OK] STT_PROVIDER: {config.STT_PROVIDER}")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao carregar config: {e}")
        return False


def check_consciencia():
    print("\n" + "=" * 60)
    print("3. TESTANDO CONSCIENCIA (LLM)")
    print("=" * 60)

    try:
        from src.soul.consciencia import Consciencia

        class MockApp:
            pass

        print("[INFO] Inicializando Consciencia...")
        consciencia = Consciencia(MockApp())

        print(f"[OK] Provider: {consciencia.provider}")
        print(f"[OK] Model: {consciencia.model_name}")

        if consciencia.ollama_client:
            print("[OK] Ollama client inicializado")
        else:
            print("[WARN] Ollama client NAO inicializado")

        print("\n[TEST] Enviando mensagem de teste...")

        response = consciencia.process_interaction("oi, tudo bem?")

        print("\n[RESULTADO]")
        print(f"  fala_tts: {response.get('fala_tts', 'N/A')[:80]}...")
        print(f"  animacao: {response.get('animacao', 'N/A')}")
        print(f"  comando_visao: {response.get('comando_visao', 'N/A')}")

        if response.get("fala_tts") and "problema tecnico" not in response.get("fala_tts", "").lower():
            print("\n[OK] Consciencia funcionando!")
            return True
        else:
            print("\n[WARN] Consciencia retornou fallback ou erro")
            return False

    except Exception as e:
        print(f"[ERRO] Falha na Consciencia: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_whisper():
    print("\n" + "=" * 60)
    print("4. VERIFICANDO WHISPER")
    print("=" * 60)

    try:
        import config

        whisper_dir = config.WHISPER_MODELS_DIR
        print(f"[INFO] Diretorio de modelos: {whisper_dir}")

        if whisper_dir.exists():
            models = list(whisper_dir.iterdir())
            print(f"[OK] {len(models)} arquivos/pastas encontrados")
        else:
            print("[WARN] Diretorio de modelos nao existe")

        from faster_whisper import WhisperModel

        print("[INFO] Tentando carregar modelo small (teste rapido)...")

        model = WhisperModel("small", device="cpu", compute_type="int8", download_root=str(whisper_dir))
        print("[OK] Modelo small carregado com sucesso")

        import numpy as np

        dummy_audio = np.zeros(16000, dtype=np.float32)
        segments, _ = model.transcribe(dummy_audio, language="pt")
        list(segments)
        print("[OK] Transcricao teste OK")

        return True

    except Exception as e:
        print(f"[ERRO] Falha no Whisper: {e}")
        return False


def check_tts():
    print("\n" + "=" * 60)
    print("5. VERIFICANDO TTS")
    print("=" * 60)

    try:
        import config

        print(f"[INFO] TTS_PROVIDER: {config.TTS_PROVIDER}")

        if config.TTS_PROVIDER == "local":
            from src.soul.boca import Boca

            boca = Boca()

            if boca.engine:
                print(f"[OK] Engine TTS inicializado: {type(boca.engine).__name__}")
            else:
                print("[WARN] Engine TTS NAO inicializado")

            print("[INFO] Testando geracao de audio...")
            audio_path = boca.gerar_audio("Teste de voz.")

            if audio_path and os.path.exists(audio_path):
                size = os.path.getsize(audio_path)
                print(f"[OK] Audio gerado: {audio_path} ({size} bytes)")
                os.remove(audio_path)
                return True
            else:
                print("[ERRO] Falha ao gerar audio")
                return False
        else:
            print(f"[INFO] TTS via cloud ({config.TTS_PROVIDER})")
            return True

    except Exception as e:
        print(f"[ERRO] Falha no TTS: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_json_parsing():
    print("\n" + "=" * 60)
    print("6. TESTANDO PARSING JSON DO LLM")
    print("=" * 60)

    try:
        import config
        from src.core.ollama_client import OllamaSyncClient

        client = OllamaSyncClient()
        model = config.CHAT_LOCAL.get("model", "dolphin-mistral")

        prompt = """Responda em JSON valido com exatamente estes campos:
{"fala_tts": "sua resposta aqui", "animacao": "Luna_observando", "comando_visao": false}

Usuario disse: oi"""

        system = """Voce e Luna, assistente gotica. Responda SEMPRE em JSON valido.
Exemplo: {"fala_tts": "E ai mortal", "animacao": "Luna_sarcastica", "comando_visao": false}"""

        print(f"[INFO] Testando modelo {model}...")
        response = client.generate(prompt=prompt, model=model, system=system, max_tokens=256)

        print("\n[RAW RESPONSE]")
        print(response.text[:500])

        import json
        import re

        text = response.text.strip()
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            json_str = text[start : end + 1]
            try:
                data = json.loads(json_str)
                print("\n[PARSED JSON]")
                print(f"  fala_tts: {data.get('fala_tts', 'N/A')}")
                print(f"  animacao: {data.get('animacao', 'N/A')}")
                print("[OK] JSON parsing funcionando!")
                return True
            except json.JSONDecodeError as e:
                print(f"[ERRO] JSON invalido: {e}")
                print(f"[JSON STRING]: {json_str[:200]}")
                return False
        else:
            print("[ERRO] Nenhum JSON encontrado na resposta")
            return False

    except Exception as e:
        print(f"[ERRO] Falha no teste: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("DIAGNOSTICO COMPLETO - LUNA OFFLINE")
    print("=" * 60)

    results = {}

    results["ollama"] = check_ollama()
    results["config"] = check_config()
    results["consciencia"] = check_consciencia()
    results["json_parsing"] = check_json_parsing()

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    all_ok = True
    for name, ok in results.items():
        status = "[OK]" if ok else "[FALHA]"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n[SUCESSO] Todos os componentes estao funcionando!")
        print("Se a Luna ainda nao responde, verifique:")
        print("  1. Se o modo de chamada esta ativo (botao de voz)")
        print("  2. Se o listening_event esta setado")
        print("  3. Se ha audio chegando no microfone")
    else:
        print("\n[ATENCAO] Alguns componentes falharam. Corrija antes de continuar.")

    return all_ok


if __name__ == "__main__":
    main()
