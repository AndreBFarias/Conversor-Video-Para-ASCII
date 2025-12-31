import logging
import subprocess

from .registry import TerminalCommandRegistry

logger = logging.getLogger(__name__)


class TerminalExecutor:
    def __init__(self, registry: TerminalCommandRegistry | None = None):
        self.registry = registry or TerminalCommandRegistry()
        self._output_buffer: list[str] = []
        self._running_process: subprocess.Popen | None = None

        from src.core.terminal_sandbox import get_terminal_sandbox

        self._sandbox = get_terminal_sandbox(strict_mode=True)

    def execute(
        self, command: str, working_dir: str | None = None, timeout: int = 60, capture_output: bool = True
    ) -> tuple[int, str, str]:
        return self._sandbox.execute_sandboxed(command=command, working_dir=working_dir, timeout=timeout)

    def execute_alias(self, alias_name: str, args: str = "") -> tuple[int, str, str]:
        cmd = self.registry.get_command(alias_name)
        if not cmd:
            return -1, "", f"Comando '{alias_name}' nao encontrado"

        if cmd.command_type == "alias" and cmd.raw_command:
            full_command = f"{cmd.raw_command} {args}".strip()
            return self.execute(full_command)

        return self.execute(f"{alias_name} {args}".strip())

    def execute_function(self, function_name: str, args: str = "") -> tuple[int, str, str]:
        cmd = self.registry.get_command(function_name)
        if not cmd:
            return -1, "", f"Funcao '{function_name}' nao encontrada"

        terminal_dir = TerminalCommandRegistry.TERMINAL_DIR
        source_cmd = f"source {terminal_dir}/functions.zsh && {function_name} {args}"

        return self.execute(source_cmd)

    def run_project_command(self, project: str, subproject: str = "", branch: str = "") -> tuple[int, str, str]:
        args = f"{project}"
        if subproject:
            args += f" {subproject}"
        if branch:
            args += f" {branch}"

        return self.execute_function("santuario", args)

    def open_antigravity(self, path: str = ".") -> tuple[int, str, str]:
        return self.execute(f"nohup antigravity {path} > /dev/null 2>&1 &")

    def get_system_info(self) -> dict[str, str]:
        info = {}

        exit_code, stdout, _ = self.execute("uname -r", timeout=5)
        if exit_code == 0:
            info["kernel"] = stdout.strip()

        exit_code, stdout, _ = self.execute("lsb_release -d", timeout=5)
        if exit_code == 0:
            info["distro"] = stdout.replace("Description:", "").strip()

        exit_code, stdout, _ = self.execute("df -h / | tail -1 | awk '{print $4}'", timeout=5)
        if exit_code == 0:
            info["disk_free"] = stdout.strip()

        return info
