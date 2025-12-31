from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.logging_config import get_logger
from src.core.terminal_executor import get_terminal_executor, parse_natural_command

if TYPE_CHECKING:
    from src.soul.consciencia.core import Consciencia

logger = get_logger(__name__)


class ActionDispatcher:
    def __init__(self, consciencia: Consciencia) -> None:
        self._consciencia = consciencia
        self._terminal_executor = get_terminal_executor()
        self._max_commands = 5
        self._command_timeout = 30

    def execute_filesystem_ops(self, response_data: dict, user_text: str) -> dict:
        filesystem_ops = response_data.get("filesystem_ops", [])
        if filesystem_ops and isinstance(filesystem_ops, list):
            cmd_results = self._execute_commands(filesystem_ops)
            if cmd_results:
                response_data["log_terminal"] += "\n\n--- TERMINAL ---\n" + "\n".join(cmd_results)

        natural_cmd = parse_natural_command(user_text)
        if natural_cmd and not filesystem_ops:
            result = self._execute_natural_command(natural_cmd)
            if result:
                response_data["log_terminal"] += "\n\n--- TERMINAL ---\n" + result

        return response_data

    def _execute_commands(self, commands: list) -> list[str]:
        results = []
        for cmd in commands[: self._max_commands]:
            if isinstance(cmd, str) and cmd.strip():
                exit_code, stdout, stderr = self._terminal_executor.execute(cmd, timeout=self._command_timeout)
                if exit_code == 0:
                    results.append(f"$ {cmd}\n{stdout[:200]}")
                else:
                    results.append(f"$ {cmd}\n[ERRO] {stderr[:100]}")
                logger.info(f"Terminal: {cmd} -> exit={exit_code}")
        return results

    def _execute_natural_command(self, cmd: str) -> str | None:
        exit_code, stdout, stderr = self._terminal_executor.execute(cmd, timeout=self._command_timeout)
        if exit_code == 0:
            logger.info(f"Comando natural executado: {cmd}")
            return f"$ {cmd}\n{stdout[:300]}"
        else:
            return f"$ {cmd}\n[ERRO] {stderr[:150]}"

    def execute_web_search(self, query: str) -> str | None:
        try:
            if not self._consciencia.web_search:
                logger.warning("Web search nao disponivel")
                return None

            results = self._consciencia.web_search.search(query, max_results=3)
            if results:
                formatted = []
                for r in results:
                    formatted.append(f"- {r.get('title', 'Sem titulo')}: {r.get('snippet', '')[:150]}")
                return "\n".join(formatted)
            return None
        except Exception as e:
            logger.error(f"Erro na busca web: {e}")
            return None

    def dispatch(self, response_data: dict, user_text: str) -> dict:
        response_data = self.execute_filesystem_ops(response_data, user_text)

        pesquisa_web = response_data.get("pesquisa_web")
        if pesquisa_web and isinstance(pesquisa_web, str) and len(pesquisa_web) > 2:
            logger.info(f"Pesquisa web detectada: '{pesquisa_web}'")
            search_results = self.execute_web_search(pesquisa_web)
            if search_results:
                response_data["log_terminal"] += f"\n\n--- WEB ---\n{search_results}"

        return response_data

    def get_stats(self) -> dict[str, Any]:
        return {
            "max_commands": self._max_commands,
            "command_timeout": self._command_timeout,
            "web_search_enabled": self._consciencia.web_search is not None,
        }
