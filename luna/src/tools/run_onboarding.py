#!/usr/bin/env python3
"""
Luna Debug Mode - Executa sem memorias para teste rapido.
Limpa sessoes temporariamente e roda com onboarding.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
SESSIONS_DIR = PROJECT_ROOT / "src" / "sessions"
MANIFEST_FILE = SESSIONS_DIR / "sessions_manifest.json"


def backup_sessions():
    backup_dir = None
    if SESSIONS_DIR.exists():
        backup_dir = Path(tempfile.mkdtemp(prefix="luna_sessions_backup_"))
        for item in SESSIONS_DIR.iterdir():
            if item.is_file():
                shutil.copy2(item, backup_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, backup_dir / item.name)
        print(f"[DEBUG] Sessoes salvas em: {backup_dir}")
    return backup_dir


def clear_sessions():
    if MANIFEST_FILE.exists():
        MANIFEST_FILE.write_text('{"sessions": [], "current_session_id": null}')
        print("[DEBUG] Manifest limpo")

    for item in SESSIONS_DIR.glob("session_*"):
        if item.is_dir():
            shutil.rmtree(item)
            print(f"[DEBUG] Removido: {item.name}")


def restore_sessions(backup_dir):
    if backup_dir and backup_dir.exists():
        for item in SESSIONS_DIR.glob("session_*"):
            if item.is_dir():
                shutil.rmtree(item)

        for item in backup_dir.iterdir():
            dest = SESSIONS_DIR / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                shutil.copytree(item, dest)

        shutil.rmtree(backup_dir)
        print("[DEBUG] Sessoes restauradas")


def main():
    print("=" * 50)
    print("  LUNA DEBUG MODE - Sem Memorias")
    print("=" * 50)

    backup_dir = backup_sessions()
    clear_sessions()

    try:
        os.chdir(PROJECT_ROOT)

        sys.path.insert(0, str(PROJECT_ROOT))

        import main as luna_main

        app = luna_main.TemploDeLuna()
        app.skip_onboarding = False
        app.run()

    except KeyboardInterrupt:
        print("\n[DEBUG] Interrompido pelo usuario")
    except Exception as e:
        print(f"[DEBUG] Erro: {e}")
        import traceback

        traceback.print_exc()
    finally:
        restore_sessions(backup_dir)
        print("[DEBUG] Sessao de debug finalizada")


if __name__ == "__main__":
    main()
