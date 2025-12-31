#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ENTITIES_DIR = PROJECT_ROOT / "src" / "assets" / "panteao" / "entities"

PALAVRAS_COMUNS: dict[str, str] = {
    "voce": "você",
    "nao": "não",
    "esta": "está",
    "tambem": "também",
    "ja": "já",
    "so": "só",
    "ate": "até",
    "sera": "será",
    "entao": "então",
    "alem": "além",
    "ai": "aí",
    "la": "lá",
    "mae": "mãe",
    "irmao": "irmão",
    "coracao": "coração",
    "emocao": "emoção",
    "razao": "razão",
    "acao": "ação",
    "atencao": "atenção",
    "informacao": "informação",
    "relacao": "relação",
    "solucao": "solução",
    "questao": "questão",
    "funcao": "função",
    "conexao": "conexão",
    "sensacao": "sensação",
    "situacao": "situação",
    "comunicacao": "comunicação",
    "organizacao": "organização",
    "documentacao": "documentação",
    "configuracao": "configuração",
    "animacao": "animação",
    "programacao": "programação",
    "instalacao": "instalação",
    "atualizacao": "atualização",
    "criacao": "criação",
    "apresentacao": "apresentação",
    "operacao": "operação",
    "producao": "produção",
    "integracao": "integração",
    "traducao": "tradução",
    "verificacao": "verificação",
    "execucao": "execução",
    "inicializacao": "inicialização",
    "finalizacao": "finalização",
    "memoria": "memória",
    "historia": "história",
    "familia": "família",
    "necessario": "necessário",
    "obvio": "óbvio",
    "serio": "sério",
    "misterio": "mistério",
    "territorio": "território",
    "obrigatorio": "obrigatório",
    "vocabulario": "vocabulário",
    "horario": "horário",
    "comentario": "comentário",
    "contrario": "contrário",
    "salario": "salário",
    "dicionario": "dicionário",
    "aniversario": "aniversário",
    "secretaria": "secretária",
    "primaria": "primária",
    "secundaria": "secundária",
    "extraordinario": "extraordinário",
    "temporario": "temporário",
    "imaginario": "imaginário",
    "solitario": "solitário",
    "revolucionario": "revolucionário",
}

FALSOS_POSITIVOS = {
    "e",
    "a",
    "o",
    "as",
    "os",
    "de",
    "da",
    "do",
    "em",
    "no",
    "na",
    "por",
    "para",
    "com",
    "sem",
    "sob",
    "sobre",
    "entre",
    "ate",
    "desde",
    "apos",
    "perante",
    "durante",
    "mediante",
    "segundo",
    "conforme",
    "como",
    "que",
    "se",
    "mas",
    "porem",
    "contudo",
    "todavia",
    "entretanto",
    "ou",
    "ora",
    "ja",
    "quer",
    "seja",
    "nem",
    "logo",
    "pois",
    "portanto",
    "porque",
    "porquanto",
    "embora",
    "conquanto",
    "posto",
    "caso",
    "desde",
    "enquanto",
    "quando",
    "sempre",
    "apenas",
    "mal",
    "assim",
    "tanto",
    "quanto",
    "tal",
    "qual",
    "tao",
    "quao",
}


def check_file(filepath: Path) -> list[dict]:
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return issues

    for wrong, correct in PALAVRAS_COMUNS.items():
        if wrong in FALSOS_POSITIVOS:
            continue

        pattern = rf"\b{wrong}\b"
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for match in matches:
            matched_word = match.group()
            if matched_word.lower() == wrong:
                line_num = content[: match.start()].count("\n") + 1
                context_start = max(0, match.start() - 30)
                context_end = min(len(content), match.end() + 30)
                context = content[context_start:context_end].replace("\n", " ")

                issues.append(
                    {
                        "file": str(filepath.relative_to(PROJECT_ROOT)),
                        "line": line_num,
                        "wrong": matched_word,
                        "correct": correct,
                        "context": context.strip(),
                    }
                )

    return issues


def check_json_file(filepath: Path) -> list[dict]:
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception:
        return issues

    def extract_strings(obj, path=""):
        strings = []
        if isinstance(obj, str):
            strings.append((path, obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                strings.extend(extract_strings(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                strings.extend(extract_strings(v, f"{path}[{i}]"))
        return strings

    all_strings = extract_strings(data)

    for path, text in all_strings:
        for wrong, correct in PALAVRAS_COMUNS.items():
            if wrong in FALSOS_POSITIVOS:
                continue

            pattern = rf"\b{wrong}\b"
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "file": str(filepath.relative_to(PROJECT_ROOT)),
                        "path": path,
                        "wrong": wrong,
                        "correct": correct,
                        "context": text[:60] + "..." if len(text) > 60 else text,
                    }
                )

    return issues


def main() -> int:
    all_issues = []

    if not ENTITIES_DIR.exists():
        print(f"Diretorio nao encontrado: {ENTITIES_DIR}")
        return 1

    for entity_dir in sorted(ENTITIES_DIR.iterdir()):
        if not entity_dir.is_dir():
            continue

        alma_file = entity_dir / "alma.txt"
        if alma_file.exists():
            all_issues.extend(check_file(alma_file))

        config_file = entity_dir / "config.json"
        if config_file.exists():
            all_issues.extend(check_json_file(config_file))

        for frases_file in entity_dir.glob("*frases*.md"):
            all_issues.extend(check_file(frases_file))

        dossie_file = entity_dir / "DOSSIE.md"
        if dossie_file.exists():
            all_issues.extend(check_file(dossie_file))

    print(f"\n{'=' * 60}")
    print(f"RELATORIO DE ACENTUACAO - {len(all_issues)} problemas encontrados")
    print(f"{'=' * 60}\n")

    if not all_issues:
        print("Nenhum problema de acentuacao encontrado.")
        return 0

    by_file: dict[str, list] = {}
    for issue in all_issues:
        fname = issue["file"]
        if fname not in by_file:
            by_file[fname] = []
        by_file[fname].append(issue)

    for fname, issues in sorted(by_file.items()):
        print(f"\n[{fname}] - {len(issues)} problemas")
        print("-" * 40)
        for issue in issues[:10]:
            if "line" in issue:
                print(f"  L{issue['line']}: '{issue['wrong']}' -> '{issue['correct']}'")
                print(f"         ...{issue['context']}...")
            else:
                print(f"  {issue['path']}: '{issue['wrong']}' -> '{issue['correct']}'")
                print(f"         {issue['context']}")
        if len(issues) > 10:
            print(f"  ... e mais {len(issues) - 10} problemas")

    print(f"\n{'=' * 60}")
    print(f"Total: {len(all_issues)} problemas em {len(by_file)} arquivos")
    print(f"{'=' * 60}\n")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
