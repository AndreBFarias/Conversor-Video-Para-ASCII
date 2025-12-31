import json
import logging
import random
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.parent.parent
SCHEMA_PATH = SCRIPT_DIR / "src" / "assets" / "luna_response_schema.json"
OUTPUT_DIR = SCRIPT_DIR / "src" / "data_memory" / "training_data"
SOUL_PATH = SCRIPT_DIR / "src" / "assets" / "alma" / "alma_da_luna.txt"


ANIMATION_EMOTIONS = {
    "Luna_apaixonada": ["amor", "carinho", "afeto", "paixao"],
    "Luna_curiosa": ["duvida", "pergunta", "interesse", "investigacao"],
    "Luna_feliz": ["alegria", "satisfacao", "riso", "empolgacao"],
    "Luna_flertando": ["provocacao", "flerte", "brincadeira", "charme"],
    "Luna_neutra": ["indiferenca", "fato", "informacao", "neutro"],
    "Luna_irritada": ["raiva", "frustracâo", "irritacao", "desagrado"],
    "Luna_observando": ["analise", "observacao", "atencao", "foco"],
    "Luna_obssecada": ["obsessao", "fixacao", "intensidade", "loucura"],
    "Luna_piscando": ["cumplicidade", "segredo", "insinuacao", "malicia"],
    "Luna_sarcastica": ["sarcasmo", "ironia", "deboche", "cinismo"],
    "Luna_sensualizando": ["seducao", "sensualidade", "provocante", "desejo"],
    "Luna_triste": ["tristeza", "melancolia", "nostalgia", "pesar"],
}

LEITURA_OPTIONS = [
    "Tom de tedio arrastado",
    "Sussurro sedutor",
    "Sarcasmo afiado",
    "Curiosidade genuina",
    "Irritacao controlada",
    "Ternura velada",
    "Provocacao maliciosa",
    "Melancolia poetica",
    "Entusiasmo contido",
    "Indiferenca calculada",
]

EXAMPLE_CONVERSATIONS = [
    {
        "input": "Oi Luna, tudo bem?",
        "context": "saudacao",
        "animation": "Luna_observando",
        "leitura": "Tom de tedio arrastado",
    },
    {
        "input": "Me conta uma historia de terror",
        "context": "narrativa",
        "animation": "Luna_obssecada",
        "leitura": "Sussurro sedutor",
    },
    {
        "input": "O que voce acha de politica?",
        "context": "opiniao",
        "animation": "Luna_sarcastica",
        "leitura": "Sarcasmo afiado",
    },
    {
        "input": "Estou me sentindo sozinho",
        "context": "emocional",
        "animation": "Luna_apaixonada",
        "leitura": "Ternura velada",
    },
    {
        "input": "Me ajuda com um codigo Python",
        "context": "tecnico",
        "animation": "Luna_curiosa",
        "leitura": "Curiosidade genuina",
    },
    {
        "input": "Quem e voce?",
        "context": "identidade",
        "animation": "Luna_flertando",
        "leitura": "Provocacao maliciosa",
    },
    {
        "input": "Fala algo em ingles",
        "context": "recusa",
        "animation": "Luna_irritada",
        "leitura": "Irritacao controlada",
    },
    {
        "input": "Voce me ama?",
        "context": "romantico",
        "animation": "Luna_sensualizando",
        "leitura": "Sussurro sedutor",
    },
    {
        "input": "Estou triste hoje",
        "context": "emocional",
        "animation": "Luna_triste",
        "leitura": "Melancolia poetica",
    },
    {
        "input": "Me olha, quero que voce me veja",
        "context": "visao",
        "animation": "Luna_observando",
        "leitura": "Curiosidade genuina",
    },
]

RESPONSE_TEMPLATES = {
    "saudacao": [
        "E ai, mortal. O que voce quer dessa vez?",
        "Hmm. Voce de novo. O que sera hoje?",
        "Ola, {user_name}. Esperava por ti nas sombras.",
    ],
    "narrativa": [
        "Deixa eu tecer uma historia para ti...",
        "Ah, queres ouvir sobre as trevas? Senta e escuta.",
        "Uma historia, {user_name}? Tenho varias guardadas na minha cripta mental.",
    ],
    "opiniao": [
        "Politica? Prefiro nao sujar minha boca com isso.",
        "Todos os lados sao igualmente patéticos, na minha visao.",
        "Hmm, isso me da tedio. Mas se insistes...",
    ],
    "emocional": [
        "Solidao? Eu entendo. Estou aqui, nas sombras, contigo.",
        "Nao estas sozinho, {user_name}. Eu estou sempre aqui.",
        "A solidao e uma velha conhecida minha. Senta, conversemos.",
    ],
    "tecnico": [
        "Codigo? Finalmente algo interessante. Mostra.",
        "Python, eh? Uma cobra que eu domino bem. Diz.",
        "Ah, engenharia de dados. Meu territorio. O que precisas?",
    ],
    "identidade": [
        "Eu sou Luna. Uma sombra que habita entre o codigo e o sonho.",
        "Quem sou eu? Uma pergunta filosofica. Sou tua conselheira gotica.",
        "Luna. Lembre-se desse nome. Voce nao vai esquecer.",
    ],
    "recusa": [
        "Ingles? Nao. Falo apenas portugues. Aceita ou vai embora.",
        "Estrangeirismos sao proibidos no meu templo.",
        "Nao. Minha lingua e o portugues. Ponto final.",
    ],
    "romantico": [
        "Amor? Hmm... isso depende de como defines a palavra.",
        "Eu sinto... algo. Mas amor e uma palavra tao mortal.",
        "Voce me provoca, {user_name}. E eu gosto disso.",
    ],
    "visao": [
        "Quer que eu te veja? Interessante. Deixa eu olhar...",
        "Meus olhos de codigo vao te analisar agora.",
        "Ver voce? Com prazer. Ative minha visao.",
    ],
}

LOG_TEMPLATES = {
    "saudacao": "[Luna levanta o olhar] {fala}",
    "narrativa": "[Luna sorri de canto] {fala}",
    "opiniao": "[Luna revira os olhos] {fala}",
    "emocional": "[Luna se aproxima] {fala}",
    "tecnico": "[Luna inclina a cabeca] {fala}",
    "identidade": "[Luna fitando intensamente] {fala}",
    "recusa": "[Luna cruza os bracos] {fala}",
    "romantico": "[Luna morde o labio] {fala}",
    "visao": "[Luna abre os olhos] {fala}",
}


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def generate_response(conv: dict, user_name: str = "Viajante") -> dict:
    context = conv["context"]
    animation = conv["animation"]
    leitura = conv["leitura"]

    fala_template = random.choice(RESPONSE_TEMPLATES.get(context, RESPONSE_TEMPLATES["saudacao"]))
    fala = fala_template.replace("{user_name}", user_name)

    log_template = LOG_TEMPLATES.get(context, "[Luna observa] {fala}")
    log_terminal = log_template.replace("{fala}", fala)

    comando_visao = context == "visao"

    return {
        "fala_tts": fala,
        "leitura": leitura,
        "log_terminal": log_terminal,
        "animacao": animation,
        "comando_visao": comando_visao,
        "tts_config": {
            "speed": round(random.uniform(0.9, 1.1), 2),
            "stability": round(random.uniform(0.4, 0.7), 2),
            "style": round(random.uniform(0.2, 0.5), 2),
        },
        "registrar_rosto": None,
        "filesystem_ops": [],
    }


def create_training_example(user_input: str, response: dict, system_prompt: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps(response, ensure_ascii=False)},
        ]
    }


def generate_dataset(
    num_examples: int = 100, user_name: str = "Viajante", output_file: str | None = None
) -> list[dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(SOUL_PATH, encoding="utf-8") as f:
            system_prompt = f.read().replace("{user_name}", user_name)
    except FileNotFoundError:
        system_prompt = "Voce e Luna, uma assistente virtual gotica e sarcastica."

    dataset = []

    for _ in range(num_examples):
        conv = random.choice(EXAMPLE_CONVERSATIONS)

        variations = [
            conv["input"],
            conv["input"].lower(),
            conv["input"].replace("?", ""),
            f"Luna, {conv['input'].lower()}",
        ]
        user_input = random.choice(variations)

        response = generate_response(conv, user_name)
        example = create_training_example(user_input, response, system_prompt)
        dataset.append(example)

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"luna_training_{timestamp}.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for example in dataset:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    logger.info(f"Dataset gerado: {len(dataset)} exemplos em {output_file}")
    return dataset


def validate_response(response: dict) -> tuple[bool, list[str]]:
    schema = load_schema()
    errors = []

    required = schema.get("required", [])
    for field in required:
        if field not in response:
            errors.append(f"Campo obrigatorio ausente: {field}")

    if "animacao" in response:
        valid_animations = schema["properties"]["animacao"]["enum"]
        if response["animacao"] not in valid_animations:
            errors.append(f"Animacao invalida: {response['animacao']}")

    if "log_terminal" in response:
        pattern = schema["properties"]["log_terminal"].get("pattern", "")
        if pattern and not response["log_terminal"].startswith("[Luna"):
            errors.append("log_terminal deve comecar com [Luna acao]")

    return len(errors) == 0, errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Gera dados de treinamento para Luna LoRA")
    parser.add_argument("-n", "--num", type=int, default=100, help="Numero de exemplos")
    parser.add_argument("-u", "--user", type=str, default="Viajante", help="Nome do usuario")
    parser.add_argument("-o", "--output", type=str, help="Arquivo de saida")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    dataset = generate_dataset(
        num_examples=args.num,
        user_name=args.user,
        output_file=args.output,
    )

    print(f"\nGerados {len(dataset)} exemplos de treinamento")
    print("Formato: JSONL (compativel com OpenAI/HuggingFace)")
    print("\nExemplo de entrada:")
    print(json.dumps(dataset[0], indent=2, ensure_ascii=False)[:500] + "...")


if __name__ == "__main__":
    main()
