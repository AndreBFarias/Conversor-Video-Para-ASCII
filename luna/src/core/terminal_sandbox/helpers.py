from __future__ import annotations

from typing import TYPE_CHECKING

from .models import CommandRisk, ExecutionMode, SandboxResult
from .sandbox import TerminalSandbox

if TYPE_CHECKING:
    from .models import ConfirmationCallback

_sandbox_instance: TerminalSandbox | None = None


def get_terminal_sandbox(
    strict_mode: bool = True,
    execution_mode: ExecutionMode = ExecutionMode.INTERACTIVE,
    confirm_callback: "ConfirmationCallback | None" = None,
) -> TerminalSandbox:
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = TerminalSandbox(
            strict_mode=strict_mode,
            execution_mode=execution_mode,
            confirm_callback=confirm_callback,
        )
    return _sandbox_instance


def reset_sandbox() -> None:
    global _sandbox_instance
    _sandbox_instance = None


def execute_safe(
    command: str,
    working_dir: str | None = None,
    timeout: int = 30,
    skip_confirmation: bool = False,
) -> tuple[int, str, str]:
    sandbox = get_terminal_sandbox()
    return sandbox.execute_sandboxed(
        command=command,
        working_dir=working_dir,
        timeout=timeout,
        skip_confirmation=skip_confirmation,
    )


def is_command_safe(command: str) -> bool:
    sandbox = get_terminal_sandbox()
    result = sandbox.analyze_command(command)
    return result.allowed and result.risk == CommandRisk.SAFE


def is_command_critical(command: str) -> bool:
    sandbox = get_terminal_sandbox()
    result = sandbox.analyze_command(command)
    return result.risk == CommandRisk.CRITICAL


def get_command_risk(command: str) -> SandboxResult:
    sandbox = get_terminal_sandbox()
    return sandbox.analyze_command(command)


def set_sandbox_mode(mode: ExecutionMode) -> None:
    sandbox = get_terminal_sandbox()
    sandbox.execution_mode = mode


def set_confirm_callback(callback: "ConfirmationCallback | None") -> None:
    sandbox = get_terminal_sandbox()
    sandbox.set_confirm_callback(callback)
