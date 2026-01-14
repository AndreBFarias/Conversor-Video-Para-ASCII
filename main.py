#!/usr/bin/env python3

import os
import sys
import traceback


def main():
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_root)

        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        src_dir = os.path.join(project_root, 'src')
        if not os.path.isdir(src_dir):
            print(f"Erro Critico: Diretorio 'src' nao encontrado em '{project_root}'.", file=sys.stderr)
            print("Verifique a estrutura do projeto.", file=sys.stderr)
            sys.exit(1)

        print(f"Lancador: Adicionado '{project_root}' ao sys.path.")
        print("Lancador: Tentando importar 'src.main.run_app'...")

        from src.main import run_app

        print("Lancador: Importacao bem-sucedida. Executando run_app()...")
        run_app()
        print("Lancador: run_app() finalizado.")

    except ImportError as e:
        print("\n--- ERRO CRITICO DE IMPORTACAO ---", file=sys.stderr)
        if "gi" in str(e).lower() or "Gtk" in str(e):
            print("Erro: Nao foi possivel importar componentes GTK ('gi', 'Gtk').", file=sys.stderr)
            print("Verifique se as dependencias do sistema GTK estao instaladas corretamente:", file=sys.stderr)
            print("   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0", file=sys.stderr)
            print("Certifique-se tambem que o ambiente virtual foi criado com '--system-site-packages'.", file=sys.stderr)
        elif "cv2" in str(e):
            print("Erro: Nao foi possivel importar OpenCV ('cv2').", file=sys.stderr)
            print("Verifique se as dependencias do sistema OpenCV estao instaladas:", file=sys.stderr)
            print("   sudo apt install python3-opencv", file=sys.stderr)
            print("E se 'opencv-python' esta no seu requirements.txt e instalado no venv:", file=sys.stderr)
            print("   venv/bin/pip install -r requirements.txt", file=sys.stderr)
        else:
            print(f"Erro: Nao foi possivel importar um modulo necessario: {e}", file=sys.stderr)
            print("Verifique se todas as dependencias estao instaladas e se a estrutura do projeto esta correta.", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("-----------------\n", file=sys.stderr)
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n--- ERRO: ARQUIVO NAO ENCONTRADO ---", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        print("Verifique se todos os arquivos necessarios (como .glade ou config.ini) estao nos locais corretos.", file=sys.stderr)
        print("----------------------------------\n", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n--- ERRO INESPERADO NO LANCADOR ---", file=sys.stderr)
        print(f"Tipo: {type(e).__name__}", file=sys.stderr)
        print(f"Erro: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("-----------------\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
