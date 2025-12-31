from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.logging_config import get_logger

from .models import (
    CommandRisk,
    ConfirmationCallback,
    ExecutionMode,
    ExecutionPolicy,
    SandboxResult,
)
from .patterns import (
    BLOCKED_PATTERNS,
    CRITICAL_PATTERNS,
    DANGEROUS_PATTERNS,
    DEFAULT_TIMEOUT,
    MAX_COMMAND_LENGTH,
    MAX_TIMEOUT,
    SAFE_COMMANDS,
    SAFE_PATHS,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class TerminalSandbox:
    def __init__(
        self,
        strict_mode: bool = True,
        execution_mode: ExecutionMode = ExecutionMode.INTERACTIVE,
        confirm_callback: ConfirmationCallback | None = None,
    ):
        self.strict_mode = strict_mode
        self._policy = ExecutionPolicy(
            mode=execution_mode,
            confirm_callback=confirm_callback,
        )
        self._blocked_patterns = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]
        self._dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]
        self._critical_patterns = [(re.compile(p, re.IGNORECASE), desc) for p, desc in CRITICAL_PATTERNS]

    @property
    def execution_mode(self) -> ExecutionMode:
        return self._policy.mode

    @execution_mode.setter
    def execution_mode(self, mode: ExecutionMode) -> None:
        self._policy.mode = mode
        logger.info(f"[SANDBOX] Modo alterado para: {mode.value}")

    def set_confirm_callback(self, callback: ConfirmationCallback | None) -> None:
        self._policy.confirm_callback = callback

    def set_autonomous_mode(self) -> None:
        self._policy.mode = ExecutionMode.AUTONOMOUS
        logger.warning("[SANDBOX] Modo AUTONOMO ativado - comandos criticos serao BLOQUEADOS")

    def set_interactive_mode(self) -> None:
        self._policy.mode = ExecutionMode.INTERACTIVE
        logger.info("[SANDBOX] Modo INTERATIVO ativado - comandos criticos pedirao confirmacao")

    def analyze_command(self, command: str) -> SandboxResult:
        if not command or not command.strip():
            return SandboxResult(
                allowed=False,
                risk=CommandRisk.BLOCKED,
                reason="Comando vazio",
            )

        command = command.strip()

        if len(command) > MAX_COMMAND_LENGTH:
            return SandboxResult(
                allowed=False,
                risk=CommandRisk.BLOCKED,
                reason=f"Comando excede limite de {MAX_COMMAND_LENGTH} caracteres",
            )

        for pattern in self._blocked_patterns:
            if pattern.search(command):
                logger.warning(f"[SANDBOX] Comando BLOQUEADO por padrao perigoso: {command[:50]}")
                return SandboxResult(
                    allowed=False,
                    risk=CommandRisk.BLOCKED,
                    reason="Comando contem padrao bloqueado por seguranca",
                    matched_pattern=pattern.pattern,
                )

        for pattern, description in self._critical_patterns:
            if pattern.search(command):
                logger.info(f"[SANDBOX] Comando CRITICO detectado: {description}")
                return SandboxResult(
                    allowed=self._policy.mode == ExecutionMode.INTERACTIVE,
                    risk=CommandRisk.CRITICAL,
                    reason=f"Comando critico: {description}",
                    sanitized_command=command,
                    requires_confirmation=True,
                    matched_pattern=pattern.pattern,
                )

        for pattern in self._dangerous_patterns:
            if pattern.search(command):
                return SandboxResult(
                    allowed=not self.strict_mode,
                    risk=CommandRisk.DANGEROUS,
                    reason="Comando requer permissoes elevadas",
                    matched_pattern=pattern.pattern,
                )

        base_command = self._extract_base_command(command)

        if base_command in SAFE_COMMANDS:
            return SandboxResult(
                allowed=True,
                risk=CommandRisk.SAFE,
                reason="Comando na whitelist",
                sanitized_command=command,
            )

        if self.strict_mode:
            return SandboxResult(
                allowed=False,
                risk=CommandRisk.MODERATE,
                reason=f"Comando '{base_command}' nao esta na whitelist",
            )

        return SandboxResult(
            allowed=True,
            risk=CommandRisk.MODERATE,
            reason="Comando permitido em modo nao-estrito",
            sanitized_command=command,
        )

    def _extract_base_command(self, command: str) -> str:
        command = re.sub(r"\s*\|\s*", " | ", command)
        command = re.sub(r"\s*&&\s*", " && ", command)
        command = re.sub(r"\s*;\s*", " ; ", command)

        parts = re.split(r"\s*[\|;&]\s*", command)
        if parts:
            first_part = parts[0].strip()
            words = first_part.split()
            if words:
                return words[0].strip()

        return command.split()[0] if command.split() else ""

    def validate_path(self, path: str) -> bool:
        try:
            abs_path = Path(path).resolve()
            abs_str = str(abs_path)

            for safe_path in SAFE_PATHS:
                if abs_str.startswith(safe_path):
                    return True

            return False
        except Exception:
            return False

    def sanitize_timeout(self, timeout: int) -> int:
        if timeout <= 0:
            return DEFAULT_TIMEOUT
        return min(timeout, MAX_TIMEOUT)

    def _request_confirmation(self, command: str, risk: CommandRisk, reason: str) -> bool:
        if self._policy.confirm_callback is None:
            logger.warning(f"[SANDBOX] Sem callback de confirmacao para comando critico: {command[:50]}")
            return False

        try:
            confirmed = self._policy.confirm_callback(command, risk, reason)
            if confirmed:
                logger.info(f"[SANDBOX] Comando CONFIRMADO pelo usuario: {command[:50]}")
            else:
                logger.info(f"[SANDBOX] Comando NEGADO pelo usuario: {command[:50]}")
                if self._policy.log_denied:
                    self._policy.denied_commands.append(command)
            return confirmed
        except Exception as e:
            logger.error(f"[SANDBOX] Erro no callback de confirmacao: {e}")
            return False

    def execute_sandboxed(
        self,
        command: str,
        working_dir: str | None = None,
        timeout: int = 30,
        env: dict | None = None,
        skip_confirmation: bool = False,
    ) -> tuple[int, str, str]:
        result = self.analyze_command(command)

        if not result.allowed and result.risk != CommandRisk.CRITICAL:
            logger.warning(f"[SANDBOX] Comando bloqueado: {result.reason}")
            return -1, "", f"[SANDBOX] Comando bloqueado: {result.reason}"

        if result.risk == CommandRisk.CRITICAL:
            if self._policy.mode == ExecutionMode.AUTONOMOUS:
                logger.warning(f"[SANDBOX] Comando CRITICO bloqueado em modo autonomo: {command[:50]}")
                return -1, "", f"[SANDBOX] Comando critico bloqueado em modo autonomo: {result.reason}"

            if not skip_confirmation:
                if not self._request_confirmation(command, result.risk, result.reason):
                    return -1, "", f"[SANDBOX] Comando critico nao confirmado: {result.reason}"

        safe_timeout = self.sanitize_timeout(timeout)

        if working_dir:
            if not self.validate_path(working_dir):
                return -1, "", f"[SANDBOX] Diretorio nao permitido: {working_dir}"
        else:
            working_dir = str(Path.home())

        safe_env = self._create_safe_env(env)

        try:
            sanitized = result.sanitized_command or command
            shell_cmd = f"bash -c '{sanitized}'"

            logger.info(f"[SANDBOX] Executando ({result.risk.value}): {command[:50]}...")

            proc_result = subprocess.run(
                shell_cmd,
                shell=True,
                cwd=working_dir,
                env=safe_env,
                capture_output=True,
                timeout=safe_timeout,
                text=True,
            )

            logger.info(f"[SANDBOX] Concluido: exit_code={proc_result.returncode}")
            return proc_result.returncode, proc_result.stdout or "", proc_result.stderr or ""

        except subprocess.TimeoutExpired:
            logger.warning(f"[SANDBOX] Timeout ({safe_timeout}s): {command[:30]}")
            return -1, "", f"[SANDBOX] Comando excedeu timeout de {safe_timeout}s"

        except Exception as e:
            logger.error(f"[SANDBOX] Erro: {e}")
            return -1, "", f"[SANDBOX] Erro: {str(e)[:100]}"

    def _create_safe_env(self, base_env: dict | None = None) -> dict:
        safe_env = base_env.copy() if base_env else os.environ.copy()

        safe_env["HOME"] = str(Path.home())
        safe_env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

        dangerous_vars = ["LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES"]
        for var in dangerous_vars:
            safe_env.pop(var, None)

        return safe_env

    def get_denied_commands(self) -> list[str]:
        return self._policy.denied_commands.copy()

    def clear_denied_commands(self) -> None:
        self._policy.denied_commands.clear()

    def get_risk_summary(self, command: str) -> dict:
        result = self.analyze_command(command)
        return {
            "command": command[:100],
            "risk": result.risk.value,
            "allowed": result.allowed,
            "requires_confirmation": result.requires_confirmation,
            "reason": result.reason,
            "matched_pattern": result.matched_pattern,
            "execution_mode": self._policy.mode.value,
        }
