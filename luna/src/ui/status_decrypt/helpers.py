from src.core.entity_loader import EntityLoader, get_active_entity

from .constants import GENDER_FORMS


def get_entity_status_text(sentiment: str = "observando") -> str:
    entity_id = get_active_entity()
    entity_loader = EntityLoader(entity_id)
    config = entity_loader.get_config()
    entity_name = config.get("name", entity_id.capitalize())
    gender = config.get("gender", "feminine")

    emotion = sentiment
    for prefix in ["Luna", "Juno", "Eris", "Lars", "Mars", "Somn"]:
        if sentiment.startswith(f"{prefix}_"):
            emotion = sentiment[len(prefix) + 1 :]
            break

    emotion_base = emotion.lower().replace(" ", "_")
    if emotion_base in GENDER_FORMS:
        fem, masc = GENDER_FORMS[emotion_base]
        emotion_display = masc if gender == "masculine" else fem
    else:
        emotion_display = emotion.replace("_", " ")

    return f"{entity_name} esta {emotion_display}"
