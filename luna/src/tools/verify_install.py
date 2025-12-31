import os
import pathlib
import shutil
import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.resolve()


def check_venv() -> tuple[bool, str]:
    venv_path = PROJECT_ROOT / "venv"
    if not venv_path.exists():
        return False, "venv nao encontrado"

    python_bin = venv_path / "bin" / "python"
    if not python_bin.exists():
        return False, "venv corrompido (python nao encontrado)"

    return True, "OK"


def check_env_file() -> tuple[bool, str]:
    env_path = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"

    if not env_path.exists():
        if env_example.exists():
            shutil.copy(env_example, env_path)
            return True, "Criado de .env.example (configure as API keys)"
        return False, ".env nao encontrado"

    with open(env_path) as f:
        content = f.read()

    if "GOOGLE_API_KEY=" in content:
        lines = content.strip().split("\n")
        for line in lines:
            if line.startswith("GOOGLE_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if not value or value == "sua_chave_aqui":
                    return False, "GOOGLE_API_KEY nao configurada no .env"
                break

    return True, "OK"


def check_directories() -> tuple[bool, str]:
    required_dirs = [
        "src/logs",
        "src/sessions",
        "src/temp/audio",
        "src/assets/panteao/entities/luna/animations",
        "src/assets/icons",
    ]

    missing = []
    for d in required_dirs:
        dir_path = PROJECT_ROOT / d
        if not dir_path.exists():
            missing.append(d)
            os.makedirs(dir_path, exist_ok=True)

    if missing:
        return True, f"Criados: {', '.join(missing)}"

    return True, "OK"


def check_python_imports() -> tuple[bool, str]:
    missing = []

    try:
        import textual
    except ImportError:
        missing.append("textual")

    try:
        from google import genai
    except ImportError:
        missing.append("google-genai")

    try:
        import faster_whisper
    except ImportError:
        missing.append("faster-whisper")

    try:
        import webrtcvad
    except ImportError:
        missing.append("webrtcvad")

    try:
        import pyaudio
    except ImportError:
        missing.append("pyaudio")

    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import sounddevice
    except ImportError:
        missing.append("sounddevice")

    if missing:
        return False, f"Faltando: {', '.join(missing)}"

    return True, "OK"


def check_system_deps() -> tuple[bool, str]:
    missing = []

    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")

    portaudio_found = any(
        [pathlib.Path("/usr/include/portaudio.h").exists(), pathlib.Path("/usr/local/include/portaudio.h").exists()]
    )
    if not portaudio_found:
        missing.append("portaudio19-dev")

    if missing:
        return False, f"Faltando: {', '.join(missing)}"

    return True, "OK"


def check_assets() -> tuple[bool, str]:
    required_assets = [
        "src/assets/panteao/entities/luna/animations/Luna_observando.txt.gz",
        "src/assets/icons/luna_icon.png",
        "src/assets/panteao/entities/luna/alma.txt",
    ]

    missing = []
    for asset in required_assets:
        if not (PROJECT_ROOT / asset).exists():
            missing.append(asset)

    if missing:
        return False, f"Faltando: {', '.join(missing)}"

    return True, "OK"


def check_whisper_model() -> tuple[bool, str]:
    cache_dir = pathlib.Path.home() / ".cache" / "huggingface" / "hub"

    whisper_patterns = ["models--Systran--faster-whisper-medium", "models--guillaumekln--faster-whisper-medium"]

    for pattern in whisper_patterns:
        if (cache_dir / pattern).exists():
            return True, "Modelo medium encontrado"

    return True, "Modelo sera baixado no primeiro uso (normal)"


def check_gpu() -> tuple[bool, str]:
    try:
        import torch

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            return True, f"GPU disponivel: {device_name}"
        return True, "GPU nao disponivel (usara CPU)"
    except ImportError:
        return True, "torch nao instalado (verificacao de GPU ignorada)"


def run_verification(verbose: bool = True) -> bool:
    checks = [
        ("Virtual Environment", check_venv),
        ("Arquivo .env", check_env_file),
        ("Diretorios", check_directories),
        ("Dependencias Sistema", check_system_deps),
        ("Modulos Python", check_python_imports),
        ("Assets", check_assets),
        ("Modelo Whisper", check_whisper_model),
        ("GPU/CUDA", check_gpu),
    ]

    all_ok = True
    results = []

    for name, check_func in checks:
        try:
            ok, msg = check_func()
            status = "OK" if ok else "ERRO"
            results.append((name, status, msg))
            if not ok:
                all_ok = False
        except Exception as e:
            results.append((name, "ERRO", str(e)))
            all_ok = False

    if verbose:
        print("\n" + "=" * 50)
        print("       LUNA - Verificacao de Instalacao")
        print("=" * 50 + "\n")

        for name, status, msg in results:
            icon = "[+]" if status == "OK" else "[-]"
            print(f"  {icon} {name}: {msg}")

        print("\n" + "=" * 50)
        if all_ok:
            print("       Instalacao verificada com sucesso!")
        else:
            print("       Problemas encontrados. Execute ./install.sh")
        print("=" * 50 + "\n")

    return all_ok


if __name__ == "__main__":
    success = run_verification(verbose=True)
    sys.exit(0 if success else 1)
