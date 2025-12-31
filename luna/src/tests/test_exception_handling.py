import os
import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestNoSilentExceptions:
    """Testes para garantir que nao ha excecoes silenciadas."""

    def test_no_bare_except_pass(self):
        """Verifica que nao existe 'except: pass' no codigo."""
        result = subprocess.run(
            ["grep", "-rn", r"except:\s*$", "src/"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        lines = [l for l in result.stdout.strip().split("\n") if l and "test_" not in l]
        lines = [l for l in lines if "__pycache__" not in l]

        filtered = []
        for line in lines:
            next_check = subprocess.run(
                ["grep", "-A1", line.split(":")[0] + ":" + line.split(":")[1]],
                capture_output=True,
                text=True,
                input=open(line.split(":")[0]).read() if os.path.exists(line.split(":")[0]) else "",
            )
            if "pass" in next_check.stdout and "logger" not in next_check.stdout:
                filtered.append(line)

        assert len(filtered) == 0, "Encontrados except silenciosos:\n" + "\n".join(filtered)

    def test_no_exception_pass_without_logging(self):
        """Verifica que 'except Exception: pass' nao existe sem logging."""
        result = subprocess.run(
            ["grep", "-rn", "-A1", "except Exception.*:", "src/"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        violations = []
        lines = result.stdout.strip().split("\n")

        for i, line in enumerate(lines):
            if "except Exception" in line and "test_" not in line and "__pycache__" not in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.search(r"^\s*pass\s*$", next_line) and "logger" not in line:
                        violations.append(f"{line}\n{next_line}")

        assert len(violations) == 0, "Except sem logging:\n" + "\n".join(violations)


class TestLoggingConfigured:
    """Testes para verificar configuracao de logging."""

    def test_soul_modules_have_logger(self):
        """Verifica que modulos em soul/ tem logger configurado."""
        soul_dir = PROJECT_ROOT / "src" / "soul"
        missing_logger = []

        wrapper_indicators = ["wrapper de compatibilidade", "implementacao real esta em"]

        for filename in os.listdir(soul_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(soul_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()

                    is_wrapper = any(ind in content.lower() for ind in wrapper_indicators)
                    if is_wrapper:
                        continue

                    if "def " in content and "logger" not in content.lower():
                        missing_logger.append(filename)

        assert len(missing_logger) == 0, f"Arquivos sem logger: {missing_logger}"

    def test_core_modules_have_logger(self):
        """Verifica que modulos em core/ tem logger configurado."""
        core_dir = PROJECT_ROOT / "src" / "core"
        missing_logger = []

        for filename in os.listdir(core_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(core_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    if "def " in content and "class " in content:
                        if "logger" not in content.lower() and "logging" not in content:
                            missing_logger.append(filename)

        assert len(missing_logger) == 0, f"Arquivos sem logger: {missing_logger}"

    def test_app_modules_have_logger(self):
        """Verifica que modulos em app/ tem logger configurado."""
        app_dir = PROJECT_ROOT / "src" / "app"
        missing_logger = []

        for filename in os.listdir(app_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(app_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    if "def " in content and "logger" not in content.lower() and "logging" not in content:
                        missing_logger.append(filename)

        assert len(missing_logger) == 0, f"Arquivos sem logger: {missing_logger}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
