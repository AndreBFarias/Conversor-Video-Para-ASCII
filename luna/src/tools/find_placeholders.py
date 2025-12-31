#!/usr/bin/env python3
"""
Luna - Detector de Placeholders
Escaneia o projeto e lista todos os TODOs, FIXMEs e funcoes vazias.
"""

import re
from collections import defaultdict
from pathlib import Path

PATTERNS = [
    (r"#\s*TODO[:\s]*(.*)", "TODO"),
    (r"#\s*FIXME[:\s]*(.*)", "FIXME"),
    (r"#\s*PLACEHOLDER[:\s]*(.*)", "PLACEHOLDER"),
    (r"#\s*HACK[:\s]*(.*)", "HACK"),
    (r"#\s*XXX[:\s]*(.*)", "XXX"),
    (r"#\s*NOTA?[:\s]*(.*)", "NOTE"),
    (r"raise NotImplementedError", "NOT_IMPLEMENTED"),
]

PASS_PATTERN = re.compile(r"^\s*pass\s*$")
DEF_PATTERN = re.compile(r"^\s*def\s+(\w+)\s*\(")
CLASS_PATTERN = re.compile(r"^\s*class\s+(\w+)")


def scan_file(filepath: Path) -> list:
    results = []
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return results

    current_def = None
    current_class = None

    for line_num, line in enumerate(lines, 1):
        class_match = CLASS_PATTERN.match(line)
        if class_match:
            current_class = class_match.group(1)

        def_match = DEF_PATTERN.match(line)
        if def_match:
            current_def = def_match.group(1)

        for pattern, tag in PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                content = match.group(1) if match.lastindex else line.strip()
                results.append(
                    {
                        "file": str(filepath),
                        "line": line_num,
                        "tag": tag,
                        "content": content.strip()[:80],
                        "function": current_def,
                        "class": current_class,
                    }
                )

        if PASS_PATTERN.match(line) and current_def:
            prev_line = lines[line_num - 2] if line_num > 1 else ""
            if "def " in prev_line or line_num < 3:
                results.append(
                    {
                        "file": str(filepath),
                        "line": line_num,
                        "tag": "EMPTY_PASS",
                        "content": f"Funcao vazia: {current_def}()",
                        "function": current_def,
                        "class": current_class,
                    }
                )

    return results


def categorize_file(filepath: str) -> str:
    if "/luna/" in filepath:
        return "Core"
    elif "/ui/" in filepath:
        return "UI"
    elif "/core/" in filepath:
        return "Core"
    elif "/data_memory/" in filepath:
        return "Memory"
    elif "/tools/" in filepath:
        return "Tools"
    else:
        return "Other"


def main():
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"

    all_results = []

    for py_file in src_path.rglob("*.py"):
        all_results.extend(scan_file(py_file))

    main_py = project_root / "main.py"
    if main_py.exists():
        all_results.extend(scan_file(main_py))

    config_py = project_root / "config.py"
    if config_py.exists():
        all_results.extend(scan_file(config_py))

    by_category = defaultdict(list)
    for r in all_results:
        cat = categorize_file(r["file"])
        by_category[cat].append(r)

    print("# Placeholders Encontrados")
    print(f"\n> Escaneado em: {project_root}")
    print(f"> Total: {len(all_results)} placeholders\n")

    tag_counts = defaultdict(int)
    for r in all_results:
        tag_counts[r["tag"]] += 1

    print("## Resumo por Tag\n")
    print("| Tag | Quantidade |")
    print("|-----|------------|")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"| {tag} | {count} |")
    print()

    for category in ["Core", "UI", "Memory", "Tools", "Other"]:
        items = by_category.get(category, [])
        if not items:
            continue

        print(f"## [{category}]\n")
        print("| Tag | Arquivo | Linha | Funcao | Descricao |")
        print("|-----|---------|-------|--------|-----------|")

        for r in sorted(items, key=lambda x: (x["tag"], x["file"], x["line"])):
            rel_path = r["file"].replace(str(project_root) + "/", "")
            func = r["function"] or "-"
            desc = r["content"][:50] + "..." if len(r["content"]) > 50 else r["content"]
            print(f"| {r['tag']} | `{rel_path}` | {r['line']} | {func} | {desc} |")

        print()

    print("---")
    print(f"*Gerado automaticamente em: {project_root}/src/tools/find_placeholders.py*")


if __name__ == "__main__":
    main()
