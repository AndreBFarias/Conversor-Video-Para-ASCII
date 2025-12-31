EMOTION_KEYWORDS = {
    "sarcastica": ["mortal", "obvio", "claro", "tedio", "serio", "ironico"],
    "curiosa": ["curioso", "interessante", "hmm", "deixa eu ver", "vejamos"],
    "feliz": ["legal", "otimo", "adorei", "gostei", "bom"],
    "irritada": ["raiva", "droga", "inferno", "maldito", "irritante"],
    "triste": ["triste", "pena", "sinto muito", "lamento"],
    "apaixonada": ["amor", "querido", "fofo", "doce", "lindo"],
    "flertando": ["charmoso", "bonito", "atraente", "sedutor"],
    "observando": [],
}

ACTION_PATTERNS = [
    (r"olh\w+", "olha"),
    (r"revir\w+.*olhos?", "revira os olhos"),
    (r"suspend?ir\w+", "suspira"),
    (r"sorr\w+", "sorri"),
    (r"franz\w+", "franze a testa"),
    (r"inclin\w+", "inclina a cabeca"),
    (r"cruz\w+.*brac", "cruza os bracos"),
    (r"pens\w+", "pensa"),
]
