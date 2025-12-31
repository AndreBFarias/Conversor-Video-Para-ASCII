import json
import logging
import re

import config

from .models import CommandCategory, TerminalCommand

logger = logging.getLogger(__name__)


class TerminalCommandRegistry:
    TERMINAL_DIR = config.APP_DIR / "src" / "assets" / "others" / "terminal"
    CACHE_FILE = config.APP_DIR / "src" / "data_memory" / "terminal_commands.json"

    CATEGORY_KEYWORDS = {
        CommandCategory.GIT: ["git", "commit", "push", "pull", "branch", "merge", "stash", "rebase", "checkout"],
        CommandCategory.SYSTEM: [
            "apt",
            "dpkg",
            "systemctl",
            "servico",
            "instalar",
            "remover",
            "atualizar",
            "reparo",
            "diagnostico",
        ],
        CommandCategory.NETWORK: ["ip", "ssh", "rsync", "conectar", "portas", "curl"],
        CommandCategory.FILE: ["cp", "mv", "rm", "mkdir", "tar", "zip", "extrair", "copiar", "mover", "apagar"],
        CommandCategory.NAVIGATION: ["cd", "..", "ls", "tree", "liste"],
        CommandCategory.PROJECT: ["santuario", "levitar", "venv", "pip", "python", "cargo"],
        CommandCategory.SEARCH: ["find", "grep", "buscar", "encontre", "procure"],
    }

    def __init__(self):
        self.commands: dict[str, TerminalCommand] = {}
        self._parse_terminal_files()

    def _categorize_command(self, name: str, description: str) -> CommandCategory:
        text = f"{name} {description}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return CommandCategory.OTHER

    def _requires_sudo(self, raw_command: str) -> bool:
        sudo_patterns = [
            r"sudo\s+",
            r"systemctl\s+",
            r"apt\s+install",
            r"apt\s+remove",
            r"apt\s+purge",
            r"reboot",
            r"shutdown",
        ]
        return any(re.search(p, raw_command) for p in sudo_patterns)

    def _parse_aliases(self, content: str) -> None:
        pattern = r"#\s*Proposito:\s*(.+)\n#\s*Uso:\s*(.+)\nalias\s+(\w+)=['\"](.+)['\"]"

        for match in re.finditer(pattern, content, re.IGNORECASE):
            description, usage, name, raw_cmd = match.groups()
            cmd = TerminalCommand(
                name=name.strip(),
                description=description.strip(),
                usage=usage.strip(),
                category=self._categorize_command(name, description),
                requires_sudo=self._requires_sudo(raw_cmd),
                command_type="alias",
                raw_command=raw_cmd.strip(),
            )
            self.commands[name.strip()] = cmd

        simple_pattern = r"alias\s+(\w+)=['\"]([^'\"]+)['\"]"
        for match in re.finditer(simple_pattern, content):
            name, raw_cmd = match.groups()
            if name.strip() not in self.commands:
                cmd = TerminalCommand(
                    name=name.strip(),
                    description=f"Alias para: {raw_cmd[:50]}",
                    usage=name.strip(),
                    category=self._categorize_command(name, raw_cmd),
                    requires_sudo=self._requires_sudo(raw_cmd),
                    command_type="alias",
                    raw_command=raw_cmd.strip(),
                )
                self.commands[name.strip()] = cmd

    def _parse_functions(self, content: str) -> None:
        pattern = r"#\s*Proposito:\s*(.+)\n#\s*Uso:\s*(.+)\n(\w+)\s*\(\)\s*\{"

        for match in re.finditer(pattern, content, re.IGNORECASE):
            description, usage, name = match.groups()

            func_start = match.end()
            brace_count = 1
            func_end = func_start
            while brace_count > 0 and func_end < len(content):
                if content[func_end] == "{":
                    brace_count += 1
                elif content[func_end] == "}":
                    brace_count -= 1
                func_end += 1

            func_body = content[func_start:func_end]

            cmd = TerminalCommand(
                name=name.strip(),
                description=description.strip(),
                usage=usage.strip(),
                category=self._categorize_command(name, description),
                requires_sudo=self._requires_sudo(func_body),
                command_type="function",
                raw_command=None,
            )
            self.commands[name.strip()] = cmd

    def _parse_terminal_files(self) -> None:
        aliases_file = self.TERMINAL_DIR / "aliases.zsh"
        functions_file = self.TERMINAL_DIR / "functions.zsh"

        if aliases_file.exists():
            try:
                content = aliases_file.read_text(encoding="utf-8")
                self._parse_aliases(content)
                logger.info(f"Parsed {len([c for c in self.commands.values() if c.command_type == 'alias'])} aliases")
            except Exception as e:
                logger.error(f"Erro ao parsear aliases: {e}")

        if functions_file.exists():
            try:
                content = functions_file.read_text(encoding="utf-8")
                self._parse_functions(content)
                logger.info(
                    f"Parsed {len([c for c in self.commands.values() if c.command_type == 'function'])} funcoes"
                )
            except Exception as e:
                logger.error(f"Erro ao parsear funcoes: {e}")

        self._save_cache()

    def _save_cache(self) -> None:
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"commands": {k: v.to_dict() for k, v in self.commands.items()}, "count": len(self.commands)}
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache de comandos: {e}")

    def search_commands(self, query: str, limit: int = 10) -> list[TerminalCommand]:
        query_lower = query.lower()
        results = []

        for cmd in self.commands.values():
            score = 0
            if query_lower == cmd.name.lower():
                score += 100
            elif query_lower in cmd.name.lower():
                score += 50
            if query_lower in cmd.description.lower():
                score += 20
            if query_lower in cmd.usage.lower():
                score += 10

            if score > 0:
                results.append((score, cmd))

        results.sort(key=lambda x: -x[0])
        return [cmd for _, cmd in results[:limit]]

    def get_commands_by_category(self, category: CommandCategory) -> list[TerminalCommand]:
        return [c for c in self.commands.values() if c.category == category]

    def get_command(self, name: str) -> TerminalCommand | None:
        return self.commands.get(name)

    def get_all_for_context(self) -> str:
        lines = ["=== COMANDOS DO TERMINAL DISPONIVEIS ==="]
        by_category: dict[CommandCategory, list[TerminalCommand]] = {}

        for cmd in self.commands.values():
            if cmd.category not in by_category:
                by_category[cmd.category] = []
            by_category[cmd.category].append(cmd)

        for category in CommandCategory:
            cmds = by_category.get(category, [])
            if cmds:
                lines.append(f"\n[{category.value.upper()}]")
                for cmd in cmds[:10]:
                    lines.append(f"  - {cmd.name}: {cmd.description[:60]}")

        return "\n".join(lines)
