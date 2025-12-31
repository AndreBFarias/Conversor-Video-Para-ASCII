from dataclasses import dataclass
from enum import Enum


class CommandCategory(Enum):
    NAVIGATION = "navegacao"
    GIT = "git"
    SYSTEM = "sistema"
    NETWORK = "rede"
    FILE = "arquivo"
    PROJECT = "projeto"
    SEARCH = "busca"
    OTHER = "outro"


@dataclass
class TerminalCommand:
    name: str
    description: str
    usage: str
    category: CommandCategory
    requires_sudo: bool
    command_type: str
    raw_command: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "usage": self.usage,
            "category": self.category.value,
            "requires_sudo": self.requires_sudo,
            "command_type": self.command_type,
        }
