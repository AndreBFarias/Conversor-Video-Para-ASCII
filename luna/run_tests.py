#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))


class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def header(title: str):
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  {title}  {Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")


def run_test_module(module_path: str, name: str) -> bool:
    print(f"{Colors.INFO}[RUN]{Colors.RESET} {name}")
    print(f"{Colors.DIM}      {module_path}{Colors.RESET}")

    start = time.time()
    result = subprocess.run(
        [sys.executable, module_path], capture_output=True, text=True, cwd=str(Path(__file__).parent)
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"{Colors.OK}[PASS]{Colors.RESET} {name} ({elapsed:.2f}s)\n")
        return True
    else:
        print(f"{Colors.FAIL}[FAIL]{Colors.RESET} {name} ({elapsed:.2f}s)")
        if result.stdout:
            for line in result.stdout.split("\n")[-20:]:
                if line.strip():
                    print(f"       {line}")
        if result.stderr:
            for line in result.stderr.split("\n")[-10:]:
                if line.strip():
                    print(f"       {Colors.FAIL}{line}{Colors.RESET}")
        print()
        return False


def main():
    header("LUNA TEST SUITE RUNNER")

    test_modules = [
        ("src/tests/test_luna_features.py", "Luna Features"),
        ("src/tests/test_pantheon.py", "Pantheon / Entities"),
        ("src/tests/test_ui_integrity.py", "UI Integrity"),
        ("src/tests/test_providers.py", "Multi-LLM Providers"),
        ("src/tests/test_new_features.py", "New Features (v4.5)"),
    ]

    results = {}
    total_start = time.time()

    for module_path, name in test_modules:
        full_path = Path(__file__).parent / module_path
        if full_path.exists():
            results[name] = run_test_module(str(full_path), name)
        else:
            print(f"{Colors.WARN}[SKIP]{Colors.RESET} {name} - arquivo nao encontrado")
            results[name] = None

    total_elapsed = time.time() - total_start

    header("RESUMO FINAL")

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for name, result in results.items():
        if result is True:
            status = f"{Colors.OK}PASS{Colors.RESET}"
        elif result is False:
            status = f"{Colors.FAIL}FAIL{Colors.RESET}"
        else:
            status = f"{Colors.WARN}SKIP{Colors.RESET}"
        print(f"  {name}: {status}")

    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Tempo: {total_elapsed:.2f}s")

    if failed == 0 and passed > 0:
        print(f"\n{Colors.OK}{Colors.BOLD}TODOS OS TESTES PASSARAM{Colors.RESET}")
        return 0
    elif failed > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}ALGUNS TESTES FALHARAM{Colors.RESET}")
        return 1
    else:
        print(f"\n{Colors.WARN}{Colors.BOLD}NENHUM TESTE EXECUTADO{Colors.RESET}")
        return 2


if __name__ == "__main__":
    sys.exit(main())


# "O que nao me mata, me fortalece."
# - Friedrich Nietzsche
