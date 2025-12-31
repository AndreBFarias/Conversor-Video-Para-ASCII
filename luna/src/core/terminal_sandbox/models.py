from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class CommandRisk(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"
    BLOCKED = "blocked"


class ExecutionMode(Enum):
    INTERACTIVE = "interactive"
    AUTONOMOUS = "autonomous"


class ConfirmationAction(Enum):
    EXECUTE = "execute"
    SKIP = "skip"
    BLOCK = "block"


ConfirmationCallback = Callable[[str, "CommandRisk", str], bool]


@dataclass
class SandboxResult:
    allowed: bool
    risk: CommandRisk
    reason: str
    sanitized_command: str | None = None
    requires_confirmation: bool = False
    matched_pattern: str | None = None


@dataclass
class ExecutionPolicy:
    mode: ExecutionMode = ExecutionMode.INTERACTIVE
    confirm_callback: ConfirmationCallback | None = None
    auto_deny_critical: bool = True
    log_denied: bool = True
    denied_commands: list[str] = field(default_factory=list)
