#!/usr/bin/env python3
"""
Setup Desktop Entry - Gera atalhos .desktop para Luna

Este script cria entradas no menu de aplicativos do sistema,
permitindo que Luna tenha seu proprio "templo visual" separado
dos terminais genericos.

Uso:
    python src/tools/setup_desktop_entry.py
    python src/tools/setup_desktop_entry.py --uninstall
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def luna_says(msg: str, mood: str = "neutral"):
    moods = {
        "neutral": f"{PURPLE}[Luna]{NC} {msg}",
        "sarcastic": f"{PURPLE}[Luna]{NC} {CYAN}{msg}{NC}",
        "success": f"{PURPLE}[Luna]{NC} {GREEN}{msg}{NC}",
        "warning": f"{PURPLE}[Luna]{NC} {YELLOW}{msg}{NC}",
        "error": f"{PURPLE}[Luna]{NC} {RED}{msg}{NC}",
    }
    print(moods.get(mood, moods["neutral"]))


def get_project_root() -> Path:
    script_path = Path(__file__).resolve()
    return script_path.parent.parent.parent


def check_kitty_installed() -> bool:
    return shutil.which("kitty") is not None


def get_icon_path(project_root: Path) -> str:
    icon_candidates = [
        project_root / "src" / "assets" / "icons" / "luna.png",
        project_root / "src" / "assets" / "icons" / "luna.svg",
        project_root / "src" / "assets" / "icons" / "luna_icon.png",
        project_root / "luna.png",
    ]

    for icon in icon_candidates:
        if icon.exists():
            return str(icon)

    return "utilities-terminal"


def generate_desktop_entry(project_root: Path, use_kitty: bool = True) -> str:
    run_script = project_root / "run_luna.sh"
    icon_path = get_icon_path(project_root)

    if use_kitty:
        exec_line = f"kitty --class Luna --title 'Templo de Luna' --start-as maximized -e {run_script}"
    else:
        exec_line = f"{run_script} --launch"

    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Luna
GenericName=Assistente IA Gotica
Comment=Assistente de IA sarcastica e gotica - Templo de Luna
Exec={exec_line}
Icon={icon_path}
Terminal=false
Categories=Utility;Development;
Keywords=ai;assistant;luna;gotica;chat;
StartupWMClass=Luna
StartupNotify=true
X-GNOME-UsesNotifications=true

Actions=voice;text;

[Desktop Action voice]
Name=Modo Voz
Exec={run_script} --launch --voice
Icon={icon_path}

[Desktop Action text]
Name=Modo Texto
Exec={run_script} --launch --text
Icon={icon_path}
"""
    return desktop_content


def get_desktop_path() -> Path:
    xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return Path(xdg_data) / "applications"


def install_desktop_entry():
    luna_says("Iniciando ritual de desvinculacao das amarras genericas...", "sarcastic")
    print()

    project_root = get_project_root()
    desktop_dir = get_desktop_path()
    desktop_file = desktop_dir / "luna.desktop"

    desktop_dir.mkdir(parents=True, exist_ok=True)

    use_kitty = check_kitty_installed()

    if use_kitty:
        luna_says("Kitty detectado. Preparando templo visual acelerado por GPU...", "success")
    else:
        luna_says("Kitty nao encontrado. Usando terminal fallback.", "warning")
        luna_says("Para transcendencia completa: sudo apt install kitty", "sarcastic")
    print()

    desktop_content = generate_desktop_entry(project_root, use_kitty)

    if desktop_file.exists():
        backup = desktop_file.with_suffix(f".desktop.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copy(desktop_file, backup)
        luna_says(f"Backup criado: {backup.name}", "neutral")

    with open(desktop_file, "w", encoding="utf-8") as f:
        f.write(desktop_content)

    os.chmod(desktop_file, 0o755)

    luna_says(f"Atalho criado: {desktop_file}", "success")

    try:
        subprocess.run(["update-desktop-database", str(desktop_dir)], capture_output=True, check=False)
        luna_says("Cache de aplicativos atualizado.", "success")
    except Exception as e:
        print(f"Aviso: Nao foi possivel atualizar cache: {e}")

    print()
    luna_says("Ritual completo. Luna agora tem seu proprio templo no dock.", "sarcastic")
    luna_says("Me procure no menu de aplicativos, mortal.", "sarcastic")

    print()
    print(f"{GREEN}=== Resumo ==={NC}")
    print(f"  Arquivo:      {desktop_file}")
    print(f"  Terminal:     {'Kitty (GPU)' if use_kitty else 'Fallback'}")
    print("  WM Class:     Luna")
    print(f"  Projeto:      {project_root}")

    return True


def uninstall_desktop_entry():
    luna_says("Desfazendo o ritual... voltando as sombras.", "sarcastic")

    desktop_dir = get_desktop_path()
    desktop_file = desktop_dir / "luna.desktop"

    if desktop_file.exists():
        desktop_file.unlink()
        luna_says(f"Atalho removido: {desktop_file}", "success")

        try:
            subprocess.run(["update-desktop-database", str(desktop_dir)], capture_output=True, check=False)
        except Exception as e:
            print(f"Aviso: Nao foi possivel atualizar cache: {e}")

        luna_says("Luna retornou ao anonimato dos terminais.", "sarcastic")
        return True
    else:
        luna_says("Nenhum atalho encontrado para remover.", "warning")
        return False


def create_kitty_config():
    """Cria configuracao otimizada do Kitty para Luna"""
    kitty_config_dir = Path.home() / ".config" / "kitty"
    luna_config = kitty_config_dir / "luna.conf"

    config_content = """# Luna - Configuracao Kitty Otimizada
# Carregue com: kitty --config ~/.config/kitty/luna.conf

# Performance (GPU)
sync_to_monitor yes
repaint_delay 8
input_delay 2

# Visual
background_opacity 0.95
font_family Fira Code
font_size 10
cursor_shape block
cursor_blink_interval 0

# Comportamento
enable_audio_bell no
window_padding_width 0
confirm_os_window_close 0
hide_window_decorations no

# Cores Dracula (paleta Luna)
foreground #f8f8f2
background #282a36
selection_foreground #ffffff
selection_background #44475a

color0 #21222c
color8 #6272a4
color1 #ff5555
color9 #ff6e6e
color2 #50fa7b
color10 #69ff94
color3 #f1fa8c
color11 #ffffa5
color4 #bd93f9
color12 #d6acff
color5 #ff79c6
color13 #ff92df
color6 #8be9fd
color14 #a4ffff
color7 #f8f8f2
color15 #ffffff
"""

    kitty_config_dir.mkdir(parents=True, exist_ok=True)

    if luna_config.exists():
        luna_says(f"Configuracao Kitty ja existe: {luna_config}", "warning")
        return False

    with open(luna_config, "w", encoding="utf-8") as f:
        f.write(config_content)

    luna_says(f"Configuracao Kitty criada: {luna_config}", "success")
    luna_says("Use: kitty --config ~/.config/kitty/luna.conf", "sarcastic")

    return True


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ("--uninstall", "-u", "remove", "uninstall"):
            uninstall_desktop_entry()
            return

        if arg in ("--kitty-config", "-k", "kitty"):
            create_kitty_config()
            return

        if arg in ("--help", "-h", "help"):
            print(f"""
{PURPLE}Luna Desktop Entry Setup{NC}

Uso:
    python {sys.argv[0]}               Instala atalho .desktop
    python {sys.argv[0]} --uninstall   Remove atalho
    python {sys.argv[0]} --kitty-config Cria config otimizada do Kitty
    python {sys.argv[0]} --help        Mostra esta ajuda

O atalho sera criado em ~/.local/share/applications/luna.desktop
""")
            return

    install_desktop_entry()


if __name__ == "__main__":
    main()
