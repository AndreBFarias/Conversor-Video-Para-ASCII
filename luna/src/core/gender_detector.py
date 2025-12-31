import logging
from typing import Literal

logger = logging.getLogger(__name__)

GenderType = Literal["M", "F", "N"]

NOMES_MASCULINOS = {
    "andre",
    "arthur",
    "antonio",
    "bernardo",
    "bruno",
    "carlos",
    "cesar",
    "daniel",
    "david",
    "diego",
    "eduardo",
    "enrique",
    "fabio",
    "felipe",
    "fernando",
    "francisco",
    "gabriel",
    "guilherme",
    "gustavo",
    "henrique",
    "hugo",
    "igor",
    "ivan",
    "joao",
    "jose",
    "julio",
    "leonardo",
    "lucas",
    "luis",
    "luiz",
    "marcelo",
    "marcos",
    "mateus",
    "matheus",
    "miguel",
    "nicolas",
    "otavio",
    "pablo",
    "paulo",
    "pedro",
    "rafael",
    "raul",
    "ricardo",
    "roberto",
    "rodrigo",
    "samuel",
    "sergio",
    "thiago",
    "tiago",
    "vinicius",
    "vitor",
    "wagner",
    "william",
    "caio",
    "enzo",
    "heitor",
    "davi",
    "theo",
    "noah",
    "gael",
    "ravi",
    "anthony",
    "lorenzo",
}

NOMES_FEMININOS = {
    "ana",
    "alice",
    "amanda",
    "beatriz",
    "bianca",
    "bruna",
    "camila",
    "carla",
    "carolina",
    "clara",
    "cristina",
    "daniela",
    "debora",
    "eduarda",
    "elisa",
    "fernanda",
    "gabriela",
    "giovana",
    "helena",
    "isabela",
    "isabella",
    "julia",
    "juliana",
    "lara",
    "larissa",
    "laura",
    "leticia",
    "livia",
    "lorena",
    "luana",
    "lucia",
    "luisa",
    "luiza",
    "manuela",
    "marcia",
    "maria",
    "mariana",
    "marina",
    "natalia",
    "patricia",
    "paula",
    "rafaela",
    "raquel",
    "rebeca",
    "renata",
    "roberta",
    "sabrina",
    "sara",
    "sofia",
    "sophia",
    "tatiana",
    "valentina",
    "vanessa",
    "victoria",
    "vitoria",
    "yasmin",
    "cecilia",
    "eloisa",
    "isadora",
    "melissa",
    "antonella",
    "heloisa",
    "liz",
    "aurora",
    "ayla",
    "maya",
}


def infer_gender_from_name(name: str) -> GenderType:
    nome_lower = name.lower().strip().split()[0] if name else ""

    if nome_lower in NOMES_MASCULINOS:
        return "M"
    if nome_lower in NOMES_FEMININOS:
        return "F"

    if nome_lower.endswith(("a", "e")) and not nome_lower.endswith(("ue", "lhe")):
        if nome_lower.endswith("a"):
            return "F"

    if nome_lower.endswith(("o", "os", "or", "el", "eu", "au")):
        return "M"

    return "N"


def get_treatment(gender: GenderType, name: str = None) -> dict[str, str]:
    nome_formatado = name.capitalize() if name else "meu bem"

    treatments = {
        "M": {
            "eleito": f"meu {nome_formatado}" if name else "meu eleito",
            "tratamento_possessivo": "meu",
            "tratamento_carinhoso": "meu bem",
            "tratamento_sedutor": "meu senhor das trevas",
            "tratamento_formal": "senhor",
            "pronome": "ele",
            "pronome_objeto": "o",
            "adjetivo_belo": "belo",
            "adjetivo_querido": "querido",
            "adjetivo_meu": "meu",
        },
        "F": {
            "eleito": f"minha {nome_formatado}" if name else "minha eleita",
            "tratamento_possessivo": "minha",
            "tratamento_carinhoso": "minha querida",
            "tratamento_sedutor": "minha senhora das sombras",
            "tratamento_formal": "senhora",
            "pronome": "ela",
            "pronome_objeto": "a",
            "adjetivo_belo": "bela",
            "adjetivo_querido": "querida",
            "adjetivo_meu": "minha",
        },
        "N": {
            "eleito": nome_formatado if name else "meu bem",
            "tratamento_possessivo": "querido",
            "tratamento_carinhoso": nome_formatado if name else "meu bem",
            "tratamento_sedutor": "criatura das sombras",
            "tratamento_formal": nome_formatado if name else "viajante",
            "pronome": "voce",
            "pronome_objeto": "te",
            "adjetivo_belo": "belo",
            "adjetivo_querido": "querido",
            "adjetivo_meu": "meu",
        },
    }
    return treatments.get(gender, treatments["N"])


def get_user_context(name: str, gender: GenderType | None = None) -> dict[str, str]:
    if gender is None:
        gender = infer_gender_from_name(name)
        logger.debug(f"Genero inferido para '{name}': {gender}")

    treatments = get_treatment(gender, name)

    return {
        "user_name": name,
        "user_gender": gender,
        **treatments,
    }
