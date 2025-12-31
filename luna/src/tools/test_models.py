import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from ollama import Client
except ImportError:
    print("ERRO: ollama nao instalado. Execute: pip install ollama")
    sys.exit(1)


MODELS_TO_TEST = {"chat": ["dolphin-mistral", "llama3.2:3b"], "vision": ["moondream"], "code": ["qwen2.5-coder:7b"]}

PERSONALITY_PROMPT = """Voce e Luna, uma engenheira de dados gotica e sarcastica.
Responda APENAS em JSON valido com esta estrutura:
{"fala_tts": "texto para falar", "log_terminal": "[Luna acao] texto", "animacao": "observando"}

Agora responda como Luna: Ola, quem e voce?"""

VISION_PROMPT = "Descreva esta imagem em portugues brasileiro de forma breve."

CODE_PROMPT = """Analise este codigo Python e retorne JSON:
{"problema": "descricao", "sugestao": "correcao"}

Codigo: def soma(a, b): return a + b"""


def test_chat_model(client: Client, model: str) -> dict:
    start = time.time()
    try:
        response = client.generate(
            model=model, prompt=PERSONALITY_PROMPT, options={"temperature": 0.7, "num_ctx": 4096}
        )
        elapsed = time.time() - start
        text = response.get("response", "")

        try:
            json.loads(text)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False

        return {
            "modelo": model,
            "tempo_s": round(elapsed, 2),
            "json_valido": json_valid,
            "resposta": text[:200],
            "status": "OK" if json_valid else "JSON_INVALIDO",
        }
    except Exception as e:
        return {"modelo": model, "status": "ERRO", "erro": str(e)}


def test_vision_model(client: Client, model: str) -> dict:
    test_image = Path(__file__).parent.parent / "assets" / "icons" / "luna_icon.png"
    if not test_image.exists():
        return {"modelo": model, "status": "SKIP", "motivo": "imagem teste nao encontrada"}

    start = time.time()
    try:
        import base64

        with open(test_image, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        response = client.generate(model=model, prompt=VISION_PROMPT, images=[img_b64], options={"temperature": 0.3})
        elapsed = time.time() - start
        text = response.get("response", "")

        return {
            "modelo": model,
            "tempo_s": round(elapsed, 2),
            "resposta": text[:200],
            "status": "OK" if len(text) > 10 else "RESPOSTA_CURTA",
        }
    except Exception as e:
        return {"modelo": model, "status": "ERRO", "erro": str(e)}


def test_code_model(client: Client, model: str) -> dict:
    start = time.time()
    try:
        response = client.generate(model=model, prompt=CODE_PROMPT, options={"temperature": 0.2})
        elapsed = time.time() - start
        text = response.get("response", "")

        try:
            json.loads(text)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False

        return {
            "modelo": model,
            "tempo_s": round(elapsed, 2),
            "json_valido": json_valid,
            "resposta": text[:200],
            "status": "OK",
        }
    except Exception as e:
        return {"modelo": model, "status": "ERRO", "erro": str(e)}


def main():
    print("\n" + "=" * 60)
    print("TESTE DE MODELOS OLLAMA PARA LUNA")
    print("=" * 60)

    client = Client()
    results = []

    print("\n[CHAT/ROLEPLAY]")
    print("-" * 40)
    for model in MODELS_TO_TEST["chat"]:
        print(f"  Testando {model}...", end=" ", flush=True)
        result = test_chat_model(client, model)
        results.append(result)
        print(f"{result['status']} ({result.get('tempo_s', '?')}s)")
        if result.get("resposta"):
            print(f"    Resposta: {result['resposta'][:80]}...")

    print("\n[VISAO]")
    print("-" * 40)
    for model in MODELS_TO_TEST["vision"]:
        print(f"  Testando {model}...", end=" ", flush=True)
        result = test_vision_model(client, model)
        results.append(result)
        print(f"{result['status']} ({result.get('tempo_s', '?')}s)")
        if result.get("resposta"):
            print(f"    Resposta: {result['resposta'][:80]}...")

    print("\n[CODIGO]")
    print("-" * 40)
    for model in MODELS_TO_TEST["code"]:
        print(f"  Testando {model}...", end=" ", flush=True)
        result = test_code_model(client, model)
        results.append(result)
        print(f"{result['status']} ({result.get('tempo_s', '?')}s)")

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    ok_count = sum(1 for r in results if r.get("status") == "OK")
    total = len(results)

    print(f"\nModelos OK: {ok_count}/{total}")

    for r in results:
        status_icon = "[OK]" if r.get("status") == "OK" else "[!!]"
        print(f"  {status_icon} {r['modelo']}: {r.get('status')} - {r.get('tempo_s', '?')}s")

    print("\n")
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
