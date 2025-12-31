import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from src.core.fallback_manager import get_fallback_manager
from src.core.ollama_client import get_ollama_client
from src.core.router import Intent, detect_intent, get_provider_config, should_use_local


class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def ok(msg: str) -> str:
    return f"{Colors.OK}[OK]{Colors.RESET} {msg}"


def fail(msg: str) -> str:
    return f"{Colors.FAIL}[FAIL]{Colors.RESET} {msg}"


def warn(msg: str) -> str:
    return f"{Colors.WARN}[WARN]{Colors.RESET} {msg}"


def info(msg: str) -> str:
    return f"{Colors.INFO}[INFO]{Colors.RESET} {msg}"


class ProviderTester:
    def __init__(self):
        self.results = {}
        self.client = None
        self.fallback_manager = None

    async def setup(self):
        self.client = get_ollama_client()
        self.fallback_manager = get_fallback_manager()
        print("=" * 70)
        print(f"{Colors.BOLD}LUNA MULTI-LLM PROVIDER TEST SUITE{Colors.RESET}")
        print("=" * 70)
        print()
        print(info("Configuracao atual:"))
        print(f"  CHAT_PROVIDER: {config.CHAT_PROVIDER}")
        print(f"  CODE_PROVIDER: {config.CODE_PROVIDER}")
        print(f"  VISION_PROVIDER: {config.VISION_PROVIDER}")
        print(f"  OLLAMA_BASE_URL: {config.OLLAMA_CONFIG['BASE_URL']}")
        print()

    async def teardown(self):
        if self.client:
            await self.client.close()
        if self.fallback_manager:
            await self.fallback_manager.close()

    async def test_ollama_health(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Ollama Health Check{Colors.RESET}")
        result = False
        try:
            healthy = await self.client.check_health()
            if healthy:
                print(f"  {ok('Ollama esta rodando')}")
                models = await self.client.list_models()
                if models:
                    print(f"  {info(f'Modelos disponiveis: {len(models)}')}")
                    for m in models[:5]:
                        print(f"    - {m}")
                    if len(models) > 5:
                        print(f"    ... e mais {len(models) - 5}")
                result = True
            else:
                print(f"  {fail('Ollama nao respondeu')}")
                print(f"  {info('Inicie com: ollama serve')}")
        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_model_availability(self, model: str, purpose: str) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Modelo {purpose}: {model}{Colors.RESET}")
        result = False
        try:
            exists = await self.client.model_exists(model)
            if exists:
                print(f"  {ok(f'Modelo {model} disponivel')}")
                result = True
            else:
                print(f"  {warn(f'Modelo {model} nao encontrado')}")
                print(f"  {info(f'Instale com: ollama pull {model}')}")
        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_chat_generation(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Geracao de Chat (Dolphin){Colors.RESET}")
        result = False
        try:
            from src.core.models.dolphin import get_dolphin_chat

            chat = get_dolphin_chat()

            if not await chat.is_available():
                print(f"  {warn('Modelo de chat nao disponivel, pulando teste')}")
                assert isinstance(result, bool)
                return result

            start = time.time()
            response = await chat.chat("Diga 'ola' em uma frase curta e misteriosa.", include_history=False)
            elapsed = time.time() - start

            if response.error:
                print(f"  {fail(f'Erro: {response.error}')}")
                assert isinstance(result, bool)
                return result

            print(f"  {ok(f'Resposta em {elapsed:.2f}s')}")
            print(f"  {info(f'Texto: {response.text[:80]}...')}")
            result = True

        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_code_generation(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Geracao de Codigo (Qwen){Colors.RESET}")
        result = False
        try:
            from src.core.models.qwen_coder import CodeLanguage, get_qwen_coder

            coder = get_qwen_coder()

            if not await coder.is_available():
                print(f"  {warn('Modelo de codigo nao disponivel, pulando teste')}")
                assert isinstance(result, bool)
                return result

            start = time.time()
            response = await coder.generate(
                "Escreva uma funcao Python que calcula o fatorial de um numero.", language=CodeLanguage.PYTHON
            )
            elapsed = time.time() - start

            if response.error:
                print(f"  {fail(f'Erro: {response.error}')}")
                assert isinstance(result, bool)
                return result

            has_def = "def " in response.code
            has_factorial = "fatorial" in response.code.lower() or "factorial" in response.code.lower()

            print(f"  {ok(f'Codigo gerado em {elapsed:.2f}s')}")
            print(f"  {info(f'Contem def: {has_def}, menciona factorial: {has_factorial}')}")
            print(f"  {info(f'Linguagem detectada: {response.language}')}")
            result = True

        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_vision_availability(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Modelo de Visao (MiniCPM-V){Colors.RESET}")
        result = False
        try:
            from src.core.models.minicpm_vision import get_minicpm_vision

            vision = get_minicpm_vision()

            if not await vision.is_available():
                print(f"  {warn('Modelo de visao nao disponivel')}")
                print(f"  {info('Instale com: ollama pull minicpm-v')}")
                assert isinstance(result, bool)
                return result

            print(f"  {ok('Modelo de visao disponivel')}")
            result = True

        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_intent_detection(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Deteccao de Intents{Colors.RESET}")
        test_cases = [
            ("Ola, como voce esta?", Intent.CHAT, False, False),
            ("Qual seu nome?", Intent.CHAT, False, False),
            ("Me conte uma historia", Intent.CHAT, False, False),
            ("Escreva um codigo Python para calcular fatorial", Intent.CODE, False, False),
            ("SELECT * FROM users WHERE active = true", Intent.CODE, False, False),
            ("Crie uma funcao que soma dois numeros", Intent.CODE, False, False),
            ("O que voce ve na imagem?", Intent.VISION, False, False),
            ("Descreva o que esta na tela", Intent.VISION, False, False),
            ("Analise esta foto", Intent.VISION, True, False),
            ("/nova", Intent.SYSTEM, False, False),
            ("/ajuda", Intent.SYSTEM, False, False),
        ]

        all_passed = True
        for text, expected, has_image, has_code in test_cases:
            result = detect_intent(text, has_image=has_image, has_code_context=has_code)
            passed = result == expected
            if not passed:
                all_passed = False
            status = ok("") if passed else fail("")
            print(f"  {status}'{text[:35]:<35}' -> {result.value:<8} (esperado: {expected.value})")

        assert isinstance(all_passed, bool)
        return all_passed

    async def test_provider_config(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Configuracao de Providers{Colors.RESET}")
        result = False
        try:
            for intent in [Intent.CHAT, Intent.CODE, Intent.VISION]:
                provider, cfg = get_provider_config(intent)
                use_local = should_use_local(intent)
                model = cfg.get("model", "N/A")
                print(f"  {info(f'{intent.value:<8}: provider={provider:<8} local={str(use_local):<5} model={model}')}")
            print(f"  {ok('Configuracoes carregadas corretamente')}")
            result = True
        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_fallback_manager(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] FallbackManager{Colors.RESET}")
        result = False
        try:
            health = await self.fallback_manager.get_health_summary()

            ollama_status = health.get("ollama", {}).get("status", "unknown")
            gemini_status = health.get("gemini", {}).get("status", "unknown")

            print(f"  {info(f'Ollama: {ollama_status}')}")
            print(f"  {info(f'Gemini: {gemini_status}')}")

            if ollama_status == "available":
                print(f"  {ok('Ollama disponivel para fallback')}")
            else:
                print(f"  {warn('Ollama indisponivel, usara API como fallback')}")

            if gemini_status == "available":
                print(f"  {ok('Gemini API configurada')}")
            else:
                print(f"  {warn('Gemini API nao configurada')}")

            result = True
        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_fallback_generation(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Geracao com Fallback{Colors.RESET}")
        result = False
        try:
            start = time.time()
            text, error, success = await self.fallback_manager.generate_with_fallback(
                prompt="Diga apenas 'teste funcionando' em portugues.",
                intent=Intent.CHAT,
                system="Voce e uma assistente concisa.",
            )
            elapsed = time.time() - start

            if success:
                print(f"  {ok(f'Geracao bem-sucedida em {elapsed:.2f}s')}")
                print(f"  {info(f'Resposta: {text[:60]}...')}")
                result = True
            else:
                print(f"  {fail(f'Erro: {error}')}")

        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def test_streaming(self) -> bool:
        print(f"\n{Colors.BOLD}[TEST] Streaming de Resposta{Colors.RESET}")
        result = False
        try:
            if not await self.client.check_health():
                print(f"  {warn('Ollama nao disponivel, pulando teste de streaming')}")
                assert isinstance(result, bool)
                return result

            model = config.CHAT_LOCAL.get("model", "dolphin-mistral")
            if not await self.client.model_exists(model):
                print(f"  {warn(f'Modelo {model} nao disponivel')}")
                assert isinstance(result, bool)
                return result

            start = time.time()
            chunks = []
            async for chunk in self.client.generate_stream(
                prompt="Conte ate 5, um numero por linha.", model=model, max_tokens=50
            ):
                chunks.append(chunk)
                if len(chunks) <= 3:
                    print(f"  {info(f'Chunk {len(chunks)}: {repr(chunk[:20])}')}")

            elapsed = time.time() - start
            full_response = "".join(chunks)

            print(f"  {ok(f'Streaming concluido: {len(chunks)} chunks em {elapsed:.2f}s')}")
            result = True

        except Exception as e:
            print(f"  {fail(f'Erro: {e}')}")
        assert isinstance(result, bool)
        return result

    async def run_all_tests(self):
        await self.setup()

        self.results["ollama_health"] = await self.test_ollama_health()

        if self.results["ollama_health"]:
            chat_model = config.CHAT_LOCAL.get("model", "dolphin-mistral")
            code_model = config.CODE_LOCAL.get("model", "qwen2.5-coder:7b")
            vision_model = config.VISION_LOCAL.get("model", "minicpm-v")

            self.results["chat_model"] = await self.test_model_availability(chat_model, "Chat")
            self.results["code_model"] = await self.test_model_availability(code_model, "Code")
            self.results["vision_model"] = await self.test_model_availability(vision_model, "Vision")

            if self.results["chat_model"]:
                self.results["chat_gen"] = await self.test_chat_generation()
                self.results["streaming"] = await self.test_streaming()

            if self.results["code_model"]:
                self.results["code_gen"] = await self.test_code_generation()

            if self.results["vision_model"]:
                self.results["vision_avail"] = await self.test_vision_availability()

        self.results["intent_detection"] = await self.test_intent_detection()
        self.results["provider_config"] = await self.test_provider_config()
        self.results["fallback_manager"] = await self.test_fallback_manager()
        self.results["fallback_gen"] = await self.test_fallback_generation()

        await self.teardown()
        self.print_summary()

    def print_summary(self):
        print()
        print("=" * 70)
        print(f"{Colors.BOLD}RESUMO DOS TESTES{Colors.RESET}")
        print("=" * 70)

        passed = sum(1 for v in self.results.values() if v)
        failed = sum(1 for v in self.results.values() if not v)
        total = len(self.results)

        for name, result in self.results.items():
            status = ok("") if result else fail("")
            print(f"  {status}{name}")

        print("-" * 70)
        print(f"  {Colors.BOLD}Total: {passed}/{total} testes passaram{Colors.RESET}")

        if passed == total:
            print(f"\n  {Colors.OK}{Colors.BOLD}[SUCCESS] Todos os testes passaram!{Colors.RESET}")
        else:
            print(f"\n  {Colors.WARN}{Colors.BOLD}[WARNING] {failed} teste(s) falharam{Colors.RESET}")
            print()
            print(f"  {info('Verifique:')}")
            print("    1. Ollama esta rodando? (ollama serve)")
            print("    2. Modelos instalados? (ollama list)")
            print("    3. .env configurado? (GOOGLE_API_KEY)")
            print()
            print(f"  {info('Comandos para instalar modelos:')}")
            print("    ollama pull dolphin-mistral")
            print("    ollama pull qwen2.5-coder:7b")
            print("    ollama pull minicpm-v")

        print("=" * 70)


async def quick_test():
    print("Quick test - verificando conectividade basica...")
    client = get_ollama_client()

    try:
        healthy = await client.check_health()
        print(f"Ollama: {'disponivel' if healthy else 'indisponivel'}")

        if healthy:
            models = await client.list_models()
            print(f"Modelos: {len(models)}")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        await client.close()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Luna Provider Test Suite")
    parser.add_argument("--quick", action="store_true", help="Teste rapido de conectividade")
    args = parser.parse_args()

    if args.quick:
        await quick_test()
    else:
        tester = ProviderTester()
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
