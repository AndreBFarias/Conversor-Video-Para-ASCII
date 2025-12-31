import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestCheckFile:
    def test_finds_missing_accent(self):
        from src.tools.check_acentuacao import check_file, PROJECT_ROOT

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Voce nao sabe o que esta fazendo.\n")
            f.flush()
            filepath = Path(f.name)

        try:
            with patch.object(Path, "relative_to", return_value=filepath.name):
                issues = check_file(filepath)
                assert len(issues) >= 2
                words_found = [i["wrong"].lower() for i in issues]
                assert "voce" in words_found or "nao" in words_found
        finally:
            filepath.unlink()

    def test_no_issues_with_correct_accents(self):
        from src.tools.check_acentuacao import check_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Você não sabe o que está fazendo.\n")
            f.flush()
            filepath = Path(f.name)

        try:
            with patch.object(Path, "relative_to", return_value=filepath.name):
                issues = check_file(filepath)
                assert len(issues) == 0
        finally:
            filepath.unlink()

    def test_handles_missing_file(self):
        from src.tools.check_acentuacao import check_file

        filepath = Path("/nonexistent/file.txt")
        issues = check_file(filepath)
        assert issues == []


class TestCheckJsonFile:
    def test_finds_missing_accent_in_json(self):
        from src.tools.check_acentuacao import check_json_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"message": "Voce nao pode fazer isso"}')
            f.flush()
            filepath = Path(f.name)

        try:
            with patch.object(Path, "relative_to", return_value=filepath.name):
                issues = check_json_file(filepath)
                assert len(issues) >= 1
        finally:
            filepath.unlink()

    def test_no_issues_with_correct_json(self):
        from src.tools.check_acentuacao import check_json_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"message": "Você não pode fazer isso"}')
            f.flush()
            filepath = Path(f.name)

        try:
            with patch.object(Path, "relative_to", return_value=filepath.name):
                issues = check_json_file(filepath)
                assert len(issues) == 0
        finally:
            filepath.unlink()

    def test_handles_invalid_json(self):
        from src.tools.check_acentuacao import check_json_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            f.flush()
            filepath = Path(f.name)

        try:
            issues = check_json_file(filepath)
            assert issues == []
        finally:
            filepath.unlink()


class TestPalavrasComuns:
    def test_has_common_words(self):
        from src.tools.check_acentuacao import PALAVRAS_COMUNS

        assert "voce" in PALAVRAS_COMUNS
        assert "nao" in PALAVRAS_COMUNS
        assert "esta" in PALAVRAS_COMUNS
        assert PALAVRAS_COMUNS["voce"] == "você"
        assert PALAVRAS_COMUNS["nao"] == "não"

    def test_has_acao_suffix_words(self):
        from src.tools.check_acentuacao import PALAVRAS_COMUNS

        acao_words = [k for k in PALAVRAS_COMUNS if k.endswith("acao")]
        assert len(acao_words) > 10
        for word in acao_words:
            assert PALAVRAS_COMUNS[word].endswith("ação")


class TestFalsosPositivos:
    def test_has_common_prepositions(self):
        from src.tools.check_acentuacao import FALSOS_POSITIVOS

        assert "e" in FALSOS_POSITIVOS
        assert "a" in FALSOS_POSITIVOS
        assert "de" in FALSOS_POSITIVOS
        assert "para" in FALSOS_POSITIVOS
