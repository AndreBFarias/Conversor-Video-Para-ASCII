from .executor import TerminalExecutor
from .registry import TerminalCommandRegistry

_registry: TerminalCommandRegistry | None = None
_executor: TerminalExecutor | None = None


def get_terminal_registry() -> TerminalCommandRegistry:
    global _registry
    if _registry is None:
        _registry = TerminalCommandRegistry()
    return _registry


def get_terminal_executor() -> TerminalExecutor:
    global _executor
    if _executor is None:
        _executor = TerminalExecutor(get_terminal_registry())
    return _executor


COMMON_COMMANDS = {
    "reiniciar": "sudo reboot",
    "desligar": "sudo shutdown -h now",
    "atualizar sistema": "sudo apt update && sudo apt full-upgrade -y",
    "abrir luna": "santuario Luna",
    "abrir antigravity": "antigravity .",
    "limpar terminal": "clear",
    "ver processos": "htop",
    "ver disco": "df -h",
    "ver memoria": "free -h",
    "ver gpu": "nvidia-smi",
    "buscar arquivo": "find . -name",
    "status git": "git status",
    "push git": "git push",
    "pull git": "git pull",
}


def parse_natural_command(text: str) -> str | None:
    text_lower = text.lower().strip()

    for phrase, cmd in COMMON_COMMANDS.items():
        if phrase in text_lower:
            return cmd

    if "reinici" in text_lower and ("pc" in text_lower or "computador" in text_lower):
        return "sudo reboot"

    if "deslig" in text_lower and ("pc" in text_lower or "computador" in text_lower):
        return "sudo shutdown -h now"

    if "atualiz" in text_lower and "sistema" in text_lower:
        return "sudo apt update && sudo apt full-upgrade -y"

    if "abr" in text_lower and "luna" in text_lower:
        return "santuario Luna"

    if "abr" in text_lower and ("antigravity" in text_lower or "ide" in text_lower):
        return "antigravity ."

    return None
