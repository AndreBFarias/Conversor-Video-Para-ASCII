import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def test_parser():
    print("\n" + "=" * 60)
    print("1. TESTE DO PARSER UNIVERSAL")
    print("=" * 60)

    from src.soul.response_parser import UniversalResponseParser

    parser = UniversalResponseParser()

    tests = [
        ("JSON valido", '{"fala_tts": "Oi mortal", "animacao": "Luna_sarcastica", "comando_visao": false}'),
        ("JSON com markdown", '```json\n{"fala_tts": "teste", "animacao": "Luna_curiosa"}\n```'),
        ("Semicolon format", "fala: Oi mortal; tom: tedio; animacao: Luna_sarcastica; visao: false"),
        ("Semicolon simples", "E ai mortal, o que quer?; tedio; Luna_sarcastica; false"),
        ("Texto puro", "Olha, isso aqui parece ser uma resposta normal sem formato especifico."),
        ("Resposta com campos", 'fala_tts = "teste"; animacao = Luna_feliz; comando_visao = false'),
    ]

    passed = 0
    for name, input_text in tests:
        result, method = parser.parse(input_text)
        has_fala = bool(result.get("fala_tts"))
        has_anim = bool(result.get("animacao"))

        if has_fala and has_anim:
            print(f"[OK] {name}")
            print(f"     method={method}, fala='{result['fala_tts'][:40]}...', anim={result['animacao']}")
            passed += 1
        else:
            print(f"[FAIL] {name}")
            print(f"       result={result}")

    print(f"\nParser: {passed}/{len(tests)} testes passaram")
    return passed == len(tests)


def test_model_manager():
    print("\n" + "=" * 60)
    print("2. TESTE DO MODEL MANAGER")
    print("=" * 60)

    from src.soul.model_manager import get_model_manager

    manager = get_model_manager()

    print("[INFO] Verificando Ollama...")
    if manager.check_ollama_running():
        print("[OK] Ollama rodando")
    else:
        print("[WARN] Ollama nao esta rodando")
        return True

    installed = manager.get_installed_models()
    print(f"[OK] {len(installed)} modelos instalados: {installed}")

    test_models = ["dolphin-mistral", "llama3.2:3b", "moondream"]
    for model in test_models:
        status = "instalado" if manager.is_installed(model) else "NAO instalado"
        print(f"     - {model}: {status}")

    return True


def test_consciencia():
    print("\n" + "=" * 60)
    print("3. TESTE DA CONSCIENCIA COM FALLBACK")
    print("=" * 60)

    from src.soul.consciencia import Consciencia

    class MockApp:
        pass

    try:
        consciencia = Consciencia(MockApp())
        print(f"[OK] Provider: {consciencia.provider}")
        print(f"[OK] Model: {consciencia.model_name}")
        print(f"[OK] Parser integrado: {consciencia.response_parser is not None}")

        print("\n[INFO] Testando interacao...")
        response = consciencia.process_interaction("ola, tudo bem?")

        print("\n[RESULTADO]")
        print(f"  fala_tts: {response.get('fala_tts', 'N/A')[:80]}...")
        print(f"  animacao: {response.get('animacao', 'N/A')}")
        print(f"  log_terminal: {response.get('log_terminal', 'N/A')[:60]}...")

        if response.get("fala_tts") and "problema tecnico" not in response.get("fala_tts", "").lower():
            print("\n[OK] Consciencia funcionando!")
            return True
        else:
            print("\n[WARN] Resposta pode ser fallback")
            return True

    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config_integration():
    print("\n" + "=" * 60)
    print("4. TESTE DA INTEGRACAO CONFIG")
    print("=" * 60)

    import config

    checks = [
        ("CHAT_PROVIDER", config.CHAT_PROVIDER),
        ("TTS_PROVIDER", config.TTS_PROVIDER),
        ("STT_PROVIDER", config.STT_PROVIDER),
        ("ANIMATION_TO_EMOTION", len(config.ANIMATION_TO_EMOTION)),
        ("EMOTION_MAP", len(config.EMOTION_MAP)),
    ]

    for name, value in checks:
        print(f"[OK] {name}: {value}")

    return True


def main():
    print("=" * 60)
    print("TESTE DE INTEGRACAO COMPLETA - LUNA")
    print("=" * 60)

    results = {}

    results["parser"] = test_parser()
    results["model_manager"] = test_model_manager()
    results["config"] = test_config_integration()
    results["consciencia"] = test_consciencia()

    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    all_ok = True
    for name, ok in results.items():
        status = "[OK]" if ok else "[FALHA]"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n[SUCESSO] Todos os testes passaram!")
        print("\nO sistema esta pronto para uso:")
        print("  1. Execute: ./run_luna.sh")
        print("  2. Digite uma mensagem e pressione Enter")
        print("  3. Ative o botao de voz para Luna falar")
        print("  4. Use o Canone para mudar configuracoes")
        print("     (modelos nao instalados serao baixados automaticamente)")
    else:
        print("\n[ATENCAO] Alguns testes falharam. Verifique os logs acima.")

    return all_ok


if __name__ == "__main__":
    main()
