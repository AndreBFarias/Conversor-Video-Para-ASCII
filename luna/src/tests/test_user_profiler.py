import tempfile
from pathlib import Path
from unittest.mock import patch


class TestNameAnalysis:
    def test_dataclass_fields(self):
        from src.soul.user_profiler import NameAnalysis

        analysis = NameAnalysis(
            nome_original="Carlos",
            nome_normalizado="carlos",
            genero_provavel="masculino",
            confianca_genero=0.95,
            possiveis_origens=["portuguesa"],
            diminutivos_comuns=["carlinhos"],
            tratamento_sugerido="caro Carlos",
            silabas=2,
            fonetica="CARLOS",
        )

        assert analysis.nome_original == "Carlos"
        assert analysis.genero_provavel == "masculino"
        assert analysis.confianca_genero == 0.95


class TestVisualAnalysis:
    def test_dataclass_fields(self):
        from src.soul.user_profiler import VisualAnalysis

        analysis = VisualAnalysis(
            genero_aparente="masculino",
            idade_estimada="30 anos",
            faixa_etaria="adulto",
            caracteristicas_fisicas={"cabelo": "castanho"},
            estilo_vestimenta="casual",
            acessorios=["oculos"],
            expressao_facial="sorrindo",
            cor_predominante="azul",
            descricao_completa="Pessoa sorridente",
            confianca=0.8,
        )

        assert analysis.genero_aparente == "masculino"
        assert analysis.idade_estimada == "30 anos"
        assert analysis.confianca == 0.8


class TestVoiceAnalysis:
    def test_dataclass_fields(self):
        from src.soul.user_profiler import VoiceAnalysis

        analysis = VoiceAnalysis(
            tipo_voz="grave",
            tom_predominante="calmo",
            velocidade_fala="media",
            sotaque_detectado="paulista",
            caracteristicas=["clara", "pausada"],
        )

        assert analysis.tipo_voz == "grave"
        assert len(analysis.caracteristicas) == 2


class TestUserProfile:
    def test_default_values(self):
        from src.soul.user_profiler import UserProfile

        profile = UserProfile(nome="Carlos", nome_completo="Carlos Farias")

        assert profile.nome == "Carlos"
        assert profile.nome_analise is None
        assert profile.preferencias == {}
        assert profile.versao == 1

    def test_to_dict(self):
        from src.soul.user_profiler import UserProfile

        profile = UserProfile(
            nome="Carlos",
            nome_completo="Carlos Farias",
            preferencias={"tema": "dark"},
            primeiro_contato="2024-01-01",
            versao=2,
        )

        data = profile.to_dict()

        assert data["nome"] == "Carlos"
        assert data["preferencias"]["tema"] == "dark"
        assert data["versao"] == 2

    def test_to_dict_with_analyses(self):
        from src.soul.user_profiler import NameAnalysis, UserProfile

        name_analysis = NameAnalysis(
            nome_original="Carlos",
            nome_normalizado="carlos",
            genero_provavel="masculino",
            confianca_genero=0.95,
            possiveis_origens=["portuguesa"],
            diminutivos_comuns=["los"],
            tratamento_sugerido="caro Carlos",
            silabas=2,
            fonetica="CARLOS",
        )

        profile = UserProfile(nome="Carlos", nome_completo="Carlos Farias", nome_analise=name_analysis)

        data = profile.to_dict()

        assert "nome_analise" in data
        assert data["nome_analise"]["genero_provavel"] == "masculino"


class TestUserProfilerInit:
    def test_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                from src.soul.user_profiler import UserProfiler

                profiler = UserProfiler()

                assert profiler.user_dir.exists()
                assert profiler.events_dir.exists()
                assert profiler.faces_dir.exists()


class TestNameAnalyzerNormalize:
    def test_removes_accents(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._normalize("Cárlos")

        assert result == "carlos"

    def test_handles_cedilla(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._normalize("Açaí")

        assert "ç" not in result
        assert result == "acai"

    def test_lowercase(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._normalize("MARIA")

        assert result == "maria"


class TestNameAnalyzerDetectGender:
    def test_feminine_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("maria")

        assert genero == "feminino"
        assert confianca == 0.95

    def test_masculine_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("carlos")

        assert genero == "masculino"
        assert confianca == 0.95

    def test_neutral_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("alex")

        assert genero == "neutro"
        assert confianca == 0.7

    def test_ending_in_a(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("luna")

        assert genero == "feminino"

    def test_ending_in_o(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("pedro")

        assert genero == "masculino"

    def test_unknown_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        genero, confianca = analyzer._detect_gender("xyzqwerty")

        assert genero == "indeterminado"
        assert confianca == 0.3


class TestNameAnalyzerDetectCulturalOrigin:
    def test_portuguese_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        origens = analyzer._detect_cultural_origin("joao")

        assert "portuguesa" in origens

    def test_italian_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        origens = analyzer._detect_cultural_origin("giovanni")

        assert "italiana" in origens

    def test_unknown_defaults_to_brazilian(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        origens = analyzer._detect_cultural_origin("xyzname")

        assert "brasileira" in origens

    def test_suffix_inho(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        origens = analyzer._detect_cultural_origin("pedrinho")

        assert "portuguesa" in origens


class TestNameAnalyzerGenerateDiminutives:
    def test_generates_diminutives_for_a(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        dims = analyzer._generate_diminutives("maria")

        assert any("inha" in d for d in dims)

    def test_generates_diminutives_for_o(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        dims = analyzer._generate_diminutives("pedro")

        assert any("inho" in d for d in dims)

    def test_known_diminutives(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        dims = analyzer._generate_diminutives("carlos")

        assert len(dims) > 0

    def test_short_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        dims = analyzer._generate_diminutives("ana")

        assert len(dims) >= 0


class TestNameAnalyzerGetTreatment:
    def test_feminine_treatment(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_treatment("feminino", "Maria Silva")

        assert "querida" in result
        assert "Maria" in result

    def test_masculine_treatment(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_treatment("masculino", "Carlos Farias")

        assert "caro" in result
        assert "Carlos" in result

    def test_neutral_treatment(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_treatment("neutro", "Alex Smith")

        assert result == "Alex"


class TestNameAnalyzerCountSyllables:
    def test_simple_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        count = analyzer._count_syllables("ana")

        assert count == 2

    def test_longer_name(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        count = analyzer._count_syllables("gabriela")

        assert count >= 3

    def test_single_syllable(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        count = analyzer._count_syllables("jo")

        assert count == 1


class TestNameAnalyzerGetPhonetic:
    def test_replaces_ph(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_phonetic("philipe")

        assert "PH" not in result
        assert "F" in result

    def test_replaces_ch(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_phonetic("charles")

        assert "CH" not in result

    def test_uppercase(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer._get_phonetic("carlos")

        assert result == result.upper()


class TestNameAnalyzerAnalyze:
    def test_full_analysis(self):
        from src.soul.user_profiler import NameAnalyzer

        analyzer = NameAnalyzer()

        result = analyzer.analyze("Carlos Farias")

        assert result.nome_original == "Carlos Farias"
        assert result.nome_normalizado == "carlos"
        assert result.genero_provavel == "masculino"
        assert result.confianca_genero > 0


class TestUserProfilerAnalyzeName:
    def test_delegates_to_name_analyzer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                from src.soul.user_profiler import UserProfiler

                profiler = UserProfiler()

                result = profiler.analyze_name("Carlos Farias")

                assert result.nome_original == "Carlos Farias"
                assert result.nome_normalizado == "carlos"
                assert result.genero_provavel == "masculino"


class TestUserProfilerSaveLoadProfile:
    def test_save_and_load(self):
        from src.soul.user_profiler import UserProfile, UserProfiler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                profiler = UserProfiler()
                profile = UserProfile(
                    nome="Carlos",
                    nome_completo="Carlos Farias",
                    preferencias={"tema": "dark"},
                )

                profiler.save_profile(profile)

                loaded = profiler.load_profile()

                assert loaded is not None
                assert loaded.nome == "Carlos"
                assert loaded.preferencias["tema"] == "dark"

    def test_load_nonexistent(self):
        from src.soul.user_profiler import UserProfiler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                profiler = UserProfiler()

                result = profiler.load_profile()

                assert result is None


class TestUserProfilerSaveEvent:
    def test_saves_event_file(self):
        from src.soul.user_profiler import UserProfiler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                profiler = UserProfiler()
                profiler.save_event("login", {"user": "test_user"})

                events = list(profiler.events_dir.glob("login_*.json"))

                assert len(events) >= 1


class TestUserProfilerGetProfileSummary:
    def test_no_profile(self):
        from src.soul.user_profiler import UserProfiler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                profiler = UserProfiler()

                result = profiler.get_profile_summary()

                assert "Nenhum perfil" in result

    def test_with_profile(self):
        from src.soul.user_profiler import NameAnalysis, UserProfile, UserProfiler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                profiler = UserProfiler()
                name_analysis = NameAnalysis(
                    nome_original="Carlos",
                    nome_normalizado="carlos",
                    genero_provavel="masculino",
                    confianca_genero=0.95,
                    possiveis_origens=["portuguesa"],
                    diminutivos_comuns=["los"],
                    tratamento_sugerido="caro Carlos",
                    silabas=2,
                    fonetica="CARLOS",
                )
                profile = UserProfile(nome="Carlos", nome_completo="Carlos Farias", nome_analise=name_analysis)
                profiler.save_profile(profile)

                result = profiler.get_profile_summary()

                assert "Carlos" in result
                assert "masculino" in result


class TestGetUserProfiler:
    def test_returns_singleton(self):
        import src.soul.user_profiler as module

        module._profiler = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.soul.user_profiler.core.config") as mock_config:
                mock_config.APP_DIR = Path(tmpdir)

                from src.soul.user_profiler import get_user_profiler

                p1 = get_user_profiler()
                p2 = get_user_profiler()

                assert p1 is p2
