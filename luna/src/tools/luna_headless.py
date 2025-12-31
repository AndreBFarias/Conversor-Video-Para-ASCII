import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class LunaHeadless:
    def __init__(self):
        from src.soul.consciencia import Consciencia

        class MockApp:
            def __init__(self):
                self.app_state = "IDLE"

            def add_chat_entry(self, role, content):
                pass

        self.mock_app = MockApp()
        self.consciencia = Consciencia(self.mock_app)
        self.history = []

    def process_input(self, text: str) -> dict:
        try:
            result = self.consciencia.process_interaction(text)
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "luna", "content": result})
            return result
        except Exception as e:
            logger.error(f"Erro ao processar: {e}")
            return {"error": str(e)}

    def get_response_text(self, result: dict) -> str:
        if "error" in result:
            return f"[ERRO] {result['error']}"
        return result.get("fala_tts", result.get("log_terminal", ""))

    def run_interactive(self):
        print("=" * 50)
        print("LUNA HEADLESS - Modo Console")
        print("=" * 50)
        print("Digite suas mensagens. 'quit' para sair.")
        print("Comandos especiais: /history, /raw, /emotion, /clear")
        print("=" * 50)
        print()

        show_raw = False

        while True:
            try:
                user_input = input("Voce: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    print("\nAte a proxima, mortal.")
                    break

                if user_input == "/history":
                    for msg in self.history:
                        role = msg["role"].upper()
                        content = msg["content"]
                        if isinstance(content, dict):
                            content = content.get("fala_tts", str(content))
                        print(f"[{role}] {content[:100]}...")
                    continue

                if user_input == "/raw":
                    show_raw = not show_raw
                    print(f"Modo raw: {'ON' if show_raw else 'OFF'}")
                    continue

                if user_input == "/emotion":
                    if self.history and isinstance(self.history[-1]["content"], dict):
                        last = self.history[-1]["content"]
                        print(f"Animacao: {last.get('animacao', 'N/A')}")
                        print(f"Leitura: {last.get('leitura', 'N/A')}")
                    continue

                if user_input == "/clear":
                    self.history.clear()
                    print("Historico limpo.")
                    continue

                result = self.process_input(user_input)

                if show_raw:
                    print(f"\nLuna (raw): {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    response_text = self.get_response_text(result)
                    animacao = result.get("animacao", "")
                    print(f"\nLuna [{animacao}]: {response_text}")

                print()

            except KeyboardInterrupt:
                print("\n\nInterrompido.")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"Erro: {e}")

    def process_batch(self, inputs: list[str]) -> list[dict]:
        results = []
        for text in inputs:
            result = self.process_input(text)
            results.append({"input": text, "output": result})
        return results


def test_consciencia():
    print("Testando Consciencia...")
    luna = LunaHeadless()

    test_inputs = [
        "Oi Luna",
        "Como voce esta?",
        "Me conta algo interessante",
    ]

    for inp in test_inputs:
        print(f"\n[INPUT] {inp}")
        result = luna.process_input(inp)
        print(f"[OUTPUT] {luna.get_response_text(result)}")
        print(f"[ANIMACAO] {result.get('animacao', 'N/A')}")

    print("\n[OK] Teste completo")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Luna Headless - Modo Console")
    parser.add_argument("--test", "-t", action="store_true", help="Executar teste rapido")
    parser.add_argument("--batch", "-b", type=str, help="Arquivo JSON com inputs para processar")
    parser.add_argument("--input", "-i", type=str, help="Processar um unico input")
    args = parser.parse_args()

    if args.test:
        test_consciencia()
    elif args.batch:
        luna = LunaHeadless()
        with open(args.batch) as f:
            inputs = json.load(f)
        results = luna.process_batch(inputs)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.input:
        luna = LunaHeadless()
        result = luna.process_input(args.input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        luna = LunaHeadless()
        luna.run_interactive()


if __name__ == "__main__":
    main()
