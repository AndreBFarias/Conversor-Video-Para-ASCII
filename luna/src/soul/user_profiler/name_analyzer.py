from __future__ import annotations

from .constants import DIMINUTIVOS_COMUNS, NOMES_FEMININOS, NOMES_MASCULINOS, NOMES_NEUTROS, ORIGENS_CULTURAIS
from .models import NameAnalysis


class NameAnalyzer:
    def analyze(self, nome: str) -> NameAnalysis:
        nome_original = nome.strip()
        nome_normalizado = self._normalize(nome_original.split()[0] if nome_original else "")

        genero, confianca = self._detect_gender(nome_normalizado)
        origens = self._detect_cultural_origin(nome_normalizado)
        diminutivos = self._generate_diminutives(nome_normalizado)
        tratamento = self._get_treatment(genero, nome_original)
        silabas = self._count_syllables(nome_normalizado)
        fonetica = self._get_phonetic(nome_normalizado)

        return NameAnalysis(
            nome_original=nome_original,
            nome_normalizado=nome_normalizado,
            genero_provavel=genero,
            confianca_genero=confianca,
            possiveis_origens=origens,
            diminutivos_comuns=diminutivos,
            tratamento_sugerido=tratamento,
            silabas=silabas,
            fonetica=fonetica,
        )

    def _normalize(self, text: str) -> str:
        replacements = {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "è": "e",
            "í": "i",
            "ì": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ò": "o",
            "ú": "u",
            "ù": "u",
            "ü": "u",
            "ç": "c",
            "ñ": "n",
        }
        result = text.lower().strip()
        for k, v in replacements.items():
            result = result.replace(k, v)
        return result

    def _detect_gender(self, nome: str) -> tuple[str, float]:
        nome_lower = nome.lower()

        if nome_lower in NOMES_FEMININOS:
            return "feminino", 0.95
        if nome_lower in NOMES_MASCULINOS:
            return "masculino", 0.95
        if nome_lower in NOMES_NEUTROS:
            return "neutro", 0.7

        if nome_lower.endswith("a") and not nome_lower.endswith(("ia", "oa")):
            return "feminino", 0.75
        if nome_lower.endswith(("o", "os", "on", "or")):
            return "masculino", 0.7
        if nome_lower.endswith(("ina", "ana", "ela", "ete", "ine")):
            return "feminino", 0.8
        if nome_lower.endswith(("son", "ton", "ito", "inho")):
            return "masculino", 0.75

        return "indeterminado", 0.3

    def _detect_cultural_origin(self, nome: str) -> list[str]:
        nome_lower = nome.lower()
        origens = []

        for origem, nomes in ORIGENS_CULTURAIS.items():
            if nome_lower in nomes:
                origens.append(origem)

        if not origens:
            if nome_lower.endswith(("inho", "inha", "ão")):
                origens.append("portuguesa")
            elif nome_lower.endswith(("ini", "etti", "ucci")):
                origens.append("italiana")
            elif nome_lower.endswith(("berg", "stein", "mann")):
                origens.append("alema")

        return origens if origens else ["brasileira"]

    def _generate_diminutives(self, nome: str) -> list[str]:
        diminutivos = []
        nome_lower = nome.lower()

        if len(nome_lower) > 3:
            if nome_lower.endswith("a"):
                diminutivos.append(nome_lower[:-1] + "inha")
            elif nome_lower.endswith("o"):
                diminutivos.append(nome_lower[:-1] + "inho")
            else:
                diminutivos.append(nome_lower + "inho")

        if len(nome_lower) > 4:
            diminutivos.append(nome_lower[:2].upper())
            diminutivos.append(nome_lower[:3].capitalize())

        if nome_lower in DIMINUTIVOS_COMUNS:
            diminutivos.extend(DIMINUTIVOS_COMUNS[nome_lower])

        return list(set(diminutivos))[:5]

    def _get_treatment(self, genero: str, nome: str) -> str:
        primeiro_nome = nome.split()[0] if nome else ""

        if genero == "feminino":
            return f"querida {primeiro_nome}"
        elif genero == "masculino":
            return f"caro {primeiro_nome}"
        else:
            return primeiro_nome

    def _count_syllables(self, nome: str) -> int:
        vogais = "aeiou"
        count = 0
        prev_vowel = False

        for char in nome.lower():
            is_vowel = char in vogais
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        return max(1, count)

    def _get_phonetic(self, nome: str) -> str:
        phonetic = nome.upper()
        replacements = [
            ("PH", "F"),
            ("CH", "X"),
            ("LH", "LI"),
            ("NH", "NI"),
            ("RR", "R"),
            ("SS", "S"),
            ("SC", "S"),
            ("SÇ", "S"),
            ("XC", "S"),
            ("Ç", "S"),
            ("GE", "JE"),
            ("GI", "JI"),
            ("GU", "G"),
            ("QU", "K"),
            ("Y", "I"),
            ("W", "V"),
        ]
        for old, new in replacements:
            phonetic = phonetic.replace(old, new)
        return phonetic
