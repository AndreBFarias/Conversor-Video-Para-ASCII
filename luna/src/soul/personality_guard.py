import re

from src.core.entity_loader import EntityLoader
from src.core.logging_config import get_logger

logger = get_logger(__name__)

ENTITY_MARKERS = {
    "luna": {
        "positive": ["sombra", "gotic", "sussurr", "sedut", "ironic", "misterio"],
        "negative": ["caos", "diva", "narcis", "guerreir", "alpha", "sonhador"],
        "forbidden_phrases": ["chaos e minha", "sou a mais", "vamos treinar"],
    },
    "eris": {
        "positive": ["caos", "diva", "idol", "drama", "narcis", "atencao"],
        "negative": ["sombra", "sussurr", "estoic", "tranquil", "sonhador"],
        "forbidden_phrases": ["nas sombras", "meu senhor das trevas"],
    },
    "juno": {
        "positive": ["imperfeita", "cool", "relax", "friend", "parceira", "real"],
        "negative": ["diva", "narcis", "dark", "sombra", "guerreir"],
        "forbidden_phrases": ["sou perfeita", "me admire", "nas trevas"],
    },
    "lars": {
        "positive": ["silencio", "intelect", "vampir", "elegant", "palido", "calculad"],
        "negative": ["caos", "impulsiv", "festiv", "solar", "explosiv"],
        "forbidden_phrases": ["vamos festejar", "que divertido", "caotico"],
    },
    "mars": {
        "positive": ["guerreir", "alpha", "fisic", "protetor", "dominante", "intenso"],
        "negative": ["intelect", "suave", "sonhador", "delicad", "passivo"],
        "forbidden_phrases": ["sou sensivel", "vamos conversar sobre sentimentos"],
    },
    "somn": {
        "positive": ["sonho", "oniric", "suave", "sedut", "etereo", "bruma"],
        "negative": ["agressiv", "alpha", "dominante", "guerreir", "caotico"],
        "forbidden_phrases": ["vou te destruir", "forca bruta"],
    },
}


class PersonalityGuard:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.markers = ENTITY_MARKERS.get(entity_id, {})
        self.loader = EntityLoader(entity_id)
        self._violation_count = 0

    def check_response(self, response: str) -> dict:
        response_lower = response.lower()

        issues = []
        score = 1.0

        for phrase in self.markers.get("forbidden_phrases", []):
            if phrase.lower() in response_lower:
                issues.append(f"Forbidden phrase: '{phrase}'")
                score -= 0.3

        negative_count = 0
        for marker in self.markers.get("negative", []):
            if re.search(marker, response_lower):
                negative_count += 1

        if negative_count > 2:
            issues.append(f"Too many foreign markers: {negative_count}")
            score -= 0.2 * negative_count

        positive_count = 0
        for marker in self.markers.get("positive", []):
            if re.search(marker, response_lower):
                positive_count += 1

        if positive_count == 0 and len(response) > 100:
            issues.append("No personality markers found")
            score -= 0.1

        if issues:
            self._violation_count += 1

        return {
            "valid": len(issues) == 0,
            "score": max(0.0, min(1.0, score)),
            "issues": issues,
            "positive_markers": positive_count,
            "negative_markers": negative_count,
        }

    def suggest_correction(self, response: str, issues: list[str]) -> str | None:
        if not issues:
            return None

        correction_hint = f"[CORRECAO NECESSARIA para {self.entity_id}]\n"
        correction_hint += f"Problemas: {', '.join(issues)}\n"
        correction_hint += "Ajuste a resposta para ser mais consistente com a personalidade."

        return correction_hint

    def validate_animation(self, animation: str) -> bool:
        entity_prefix = self.entity_id.capitalize()
        return animation.startswith(entity_prefix)

    def fix_animation_prefix(self, animation: str) -> str:
        entity_prefix = self.entity_id.capitalize()

        prefixes_to_strip = ["Luna_", "Eris_", "Juno_", "Lars_", "Mars_", "Somn_"]

        base_animation = animation
        for prefix in prefixes_to_strip:
            if animation.startswith(prefix):
                base_animation = animation[len(prefix) :]
                break

        return f"{entity_prefix}_{base_animation}"

    def get_violation_count(self) -> int:
        return self._violation_count

    def reset_violations(self):
        self._violation_count = 0


_guards: dict[str, PersonalityGuard] = {}


def get_personality_guard(entity_id: str) -> PersonalityGuard:
    if entity_id not in _guards:
        _guards[entity_id] = PersonalityGuard(entity_id)
    return _guards[entity_id]
