from enum import Enum


class MemoryCategory(Enum):
    USER_INFO = "user_info"
    PREFERENCE = "preference"
    FACT = "fact"
    EVENT = "event"
    EMOTION = "emotion"
    CONTEXT = "context"
    INSTRUCTION = "instruction"


CATEGORY_KEYWORDS = {
    MemoryCategory.USER_INFO: [
        "nome",
        "chamo",
        "sou",
        "moro",
        "trabalho",
        "idade",
        "nasci",
        "profissao",
        "formacao",
        "familia",
        "casado",
        "solteiro",
    ],
    MemoryCategory.PREFERENCE: [
        "gosto",
        "prefiro",
        "adoro",
        "odeio",
        "favorito",
        "melhor",
        "pior",
        "amo",
        "detesto",
        "curto",
        "prefere",
    ],
    MemoryCategory.FACT: [
        "significa",
        "define",
        "porque",
        "como",
        "quando",
        "onde",
        "quem",
        "explicar",
        "entender",
        "saber",
    ],
    MemoryCategory.EVENT: [
        "aconteceu",
        "fiz",
        "foi",
        "ontem",
        "hoje",
        "semana",
        "mes",
        "ano",
        "viagem",
        "comprei",
        "vendi",
        "conheci",
    ],
    MemoryCategory.EMOTION: [
        "triste",
        "feliz",
        "ansioso",
        "animado",
        "cansado",
        "estressado",
        "preocupado",
        "aliviado",
        "frustrado",
        "empolgado",
    ],
}
