import re

from textual.message import Message
from textual.suggester import Suggester
from textual.widgets import Input

import config

REACTION_ALIASES = ("/reacao", "/reação", "/react", "/Reacao", "/Reação", "/REACAO", "/REACT", "/rea")


class ReactionSuggester(Suggester):
    def __init__(self) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._reactions = list(config.ANIMATION_TO_EMOTION.keys())
        self._pattern = re.compile(r"/(rea[cç]?[aã]?o?|react)\s+(\w*)$", re.IGNORECASE)

    async def get_suggestion(self, value: str) -> str | None:
        match = self._pattern.search(value)
        if not match:
            return None

        partial = match.group(2).lower()
        prefix = value[: match.start()]

        for reaction in self._reactions:
            reaction_lower = reaction.lower().replace("luna_", "")
            if reaction_lower.startswith(partial):
                return f"{prefix}/react {reaction}"

        for reaction in self._reactions:
            reaction_lower = reaction.lower()
            if partial in reaction_lower:
                return f"{prefix}/react {reaction}"

        if not partial:
            return f"{prefix}/react Luna_observando"

        return None


class ReactionInput(Input):
    class ReactionSelected(Message):
        def __init__(self, reaction: str) -> None:
            self.reaction = reaction
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        suggester = ReactionSuggester()
        super().__init__(*args, suggester=suggester, **kwargs)
        self._reaction_pattern = re.compile(r"/(rea[cç]?[aã]?o?|react)\s+(Luna_\w+)", re.IGNORECASE)

    def _on_suggestion_ready(self, event) -> None:
        super()._on_suggestion_ready(event)

    def action_cursor_right(self) -> None:
        if self._suggestion:
            self.value = self._suggestion
            self.cursor_position = len(self.value)
            self._suggestion = ""
            self._check_for_reaction()
        else:
            super().action_cursor_right()

    def on_key(self, event) -> None:
        if event.key == "tab" and self._suggestion:
            self.value = self._suggestion
            self.cursor_position = len(self.value)
            self._suggestion = ""
            self._check_for_reaction()
            event.prevent_default()
            event.stop()

    def _check_for_reaction(self) -> None:
        match = self._reaction_pattern.search(self.value)
        if match:
            self.post_message(self.ReactionSelected(match.group(2)))


def get_available_reactions() -> list[str]:
    return list(config.ANIMATION_TO_EMOTION.keys())


def get_reaction_descriptions() -> dict[str, str]:
    descriptions = {
        "Luna_apaixonada": "apaixonada, calorosa, afetuosa",
        "Luna_curiosa": "curiosa, interessada, investigativa",
        "Luna_feliz": "feliz, alegre, entusiasmada",
        "Luna_flertando": "flertando, brincalhona, leve",
        "Luna_neutra": "neutra, indiferente, apatica",
        "Luna_irritada": "irritada, brava, rispida",
        "Luna_medrosa": "medrosa, assustada, vulneravel",
        "Luna_observando": "observando, atenta, analitica",
        "Luna_obssecada": "obcecada, intensa, focada",
        "Luna_sarcastica": "sarcastica, ironica, debochada",
        "Luna_sensualizando": "seduzindo, sensual, provocante",
        "Luna_travessa": "travessa, maliciosa, provocadora",
        "Luna_triste": "triste, melancolica, pensativa",
    }
    return descriptions
