"""
Fixtures padrão para testes.
Use estas fixtures ao invés de dados hardcoded.
"""

import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, Mock

import pytest


def _create_module_mock(name: str) -> MagicMock:
    mock = MagicMock(spec=ModuleType)
    mock.__name__ = name
    mock.__spec__ = MagicMock()
    mock.__spec__.name = name
    mock.__spec__.loader = MagicMock()
    mock.__path__ = []
    mock.__file__ = f"/fake/{name}.py"
    return mock


if "torchaudio" not in sys.modules:
    sys.modules["torchaudio"] = _create_module_mock("torchaudio")

# ============================================
# CONSTANTES DE TESTE
# ============================================

TEST_USER = "test_user"
TEST_USER_ID = "user_001"
TEST_EMAIL = "test@example.com"
TEST_ENTITY = "luna"


# ============================================
# FIXTURES DE USUÁRIO
# ============================================


@pytest.fixture
def test_user():
    """Nome de usuário para testes."""
    return TEST_USER


@pytest.fixture
def test_user_id():
    """ID de usuário para testes."""
    return TEST_USER_ID


@pytest.fixture
def test_email():
    """Email para testes."""
    return TEST_EMAIL


@pytest.fixture
def test_entity():
    """Entidade padrão para testes."""
    return TEST_ENTITY


@pytest.fixture
def user_profile():
    """Perfil de usuário completo para testes."""
    return {
        "name": TEST_USER,
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "preferences": {
            "theme": "dark",
            "language": "pt-BR",
        },
    }


# ============================================
# FIXTURES DE ARQUIVOS/PATHS
# ============================================


@pytest.fixture
def temp_dir():
    """Diretório temporário que é limpo após o teste."""
    dir_path = tempfile.mkdtemp(prefix="luna_test_")
    yield Path(dir_path)
    # Cleanup
    import shutil

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


@pytest.fixture
def temp_file(temp_dir):
    """Arquivo temporário para testes."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("test content")
    return file_path


@pytest.fixture
def temp_json_file(temp_dir):
    """Arquivo JSON temporário para testes."""
    import json

    file_path = temp_dir / "test_data.json"
    file_path.write_text(json.dumps({"key": "value"}))
    return file_path


# ============================================
# FIXTURES DE MOCKS
# ============================================


@pytest.fixture
def mock_config(monkeypatch, temp_dir):
    """Mock de configurações apontando para diretório temporário."""
    monkeypatch.setattr("config.APP_DIR", temp_dir)
    monkeypatch.setattr("config.DATA_DIR", temp_dir / "data")
    monkeypatch.setattr("config.CACHE_DIR", temp_dir / "cache")
    return temp_dir


@pytest.fixture
def mock_llm_response():
    """Mock de resposta do LLM."""
    return {
        "fala_tts": "Resposta de teste",
        "log_terminal": "[Luna] Teste",
        "animacao": "neutra",
        "comando_visao": False,
        "filesystem_ops": [],
    }


@pytest.fixture
def mock_embedding():
    """Mock de embedding para testes de memória."""
    import numpy as np

    return np.random.rand(384).astype(np.float32)


@pytest.fixture
def mock_audio_data():
    """Mock de dados de áudio."""
    import numpy as np

    # 1 segundo de áudio silencioso a 16kHz
    return np.zeros(16000, dtype=np.int16)


@pytest.fixture
def mock_image():
    """Mock de imagem para testes de visão."""
    import numpy as np

    # Imagem 100x100 RGB preta
    return np.zeros((100, 100, 3), dtype=np.uint8)


# ============================================
# FIXTURES DE CONTEXTO
# ============================================


@pytest.fixture
def mock_entity_loader(test_entity):
    """Mock do EntityLoader."""
    loader = Mock()
    loader.entity_id = test_entity
    loader.get_soul_prompt.return_value = "Prompt de teste"
    loader.get_color_theme.return_value = {"primary": "#8B5CF6"}
    loader.get_animation_path.return_value = None
    return loader


@pytest.fixture
def mock_memory():
    """Mock do SmartMemory."""
    memory = Mock()
    memory.add.return_value = True
    memory.retrieve.return_value = []
    memory.clear.return_value = True
    return memory


# ============================================
# MARKERS CUSTOMIZADOS
# ============================================


def pytest_configure(config):
    """Registra markers customizados."""
    config.addinivalue_line("markers", "slow: marca testes lentos (rodar com -m 'not slow' para pular)")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "requires_display: marca testes que precisam de display")
    config.addinivalue_line("markers", "requires_gpu: marca testes que precisam de GPU")
