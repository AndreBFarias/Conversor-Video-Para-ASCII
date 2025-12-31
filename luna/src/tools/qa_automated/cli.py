import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from .controller import LunaInteractiveController
from .runner import LunaTestRunner


async def run_tests():
    runner = LunaTestRunner()
    report = await runner.run_all_tests()

    print("\n" + "=" * 60)
    print("RELATORIO DE TESTES - LUNA QA")
    print("=" * 60)
    print(f"Total: {len(report.tests)}")
    print(f"Passou: {report.passed_count}")
    print(f"Falhou: {report.failed_count}")
    print("-" * 60)

    for test in report.tests:
        status = "[PASS]" if test.passed else "[FAIL]"
        print(f"{status} {test.name} ({test.duration:.3f}s)")
        if test.error:
            print(f"       Erro: {test.error}")

    print("=" * 60)

    report_path = (
        Path(__file__).parent.parent.parent / "logs" / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"\nRelatorio salvo em: {report_path}")

    return report.failed_count == 0


async def run_interactive():
    controller = LunaInteractiveController()
    await controller.start()
    await controller.run_interactive()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Luna QA Automated Testing")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interativo")
    parser.add_argument("--test", "-t", action="store_true", help="Executar testes automatizados")
    args = parser.parse_args()

    if args.interactive:
        asyncio.run(run_interactive())
    elif args.test:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    else:
        print("Uso: python qa_automated.py [--test | --interactive]")
        print("  --test, -t       Executar testes automatizados")
        print("  --interactive, -i  Modo interativo para controle manual")
