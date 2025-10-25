#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ponto de entrada principal (Launcher) para a Interface Gráfica (GTK)
do Êxtase em 4R73.

Este script configura o ambiente Python para garantir que os módulos
dentro de 'src/' possam ser importados corretamente e, em seguida,
inicia a aplicação principal.

REQUER DEPENDÊNCIAS DO 'requirements.txt' E do sistema (GTK, OpenCV).
Execute 'install.sh' para a configuração completa.
"""

import os
import sys
import traceback # Para exibir erros mais detalhados

def main():
    """
    Configura o sys.path e inicia a aplicação principal 'src.main.run_app()'.
    """
    try:
        # Garante que o diretório atual seja o diretório do script
        # Isso ajuda a resolver caminhos relativos de forma consistente
        project_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_root)

        # Adiciona a raiz do projeto ao sys.path para que 'import src.xxx' funcione
        if project_root not in sys.path:
             sys.path.insert(0, project_root)

        # Verifica se o diretório 'src' existe
        src_dir = os.path.join(project_root, 'src')
        if not os.path.isdir(src_dir):
            print(f"Erro Crítico: Diretório 'src' não encontrado em '{project_root}'.", file=sys.stderr)
            print("Verifique a estrutura do projeto.", file=sys.stderr)
            sys.exit(1)

        print(f"Lançador: Adicionado '{project_root}' ao sys.path.")
        print("Lançador: Tentando importar 'src.main.run_app'...")

        # Importa DEPOIS de ajustar o path
        from src.main import run_app

        print("Lançador: Importação bem-sucedida. Executando run_app()...")
        # Executa a função principal da aplicação
        run_app()
        print("Lançador: run_app() finalizado.")

    except ImportError as e:
        print("\n--- ERRO CRÍTICO DE IMPORTAÇÃO ---", file=sys.stderr)
        # Verifica se o erro é sobre 'gi' (GTK)
        if "gi" in str(e).lower() or "Gtk" in str(e):
            print("Erro: Não foi possível importar componentes GTK ('gi', 'Gtk').", file=sys.stderr)
            print("Verifique se as dependências do sistema GTK estão instaladas corretamente:", file=sys.stderr)
            print("   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0", file=sys.stderr)
            print("Certifique-se também que o ambiente virtual foi criado com '--system-site-packages'.", file=sys.stderr)
        elif "cv2" in str(e):
             print("Erro: Não foi possível importar OpenCV ('cv2').", file=sys.stderr)
             print("Verifique se as dependências do sistema OpenCV estão instaladas:", file=sys.stderr)
             print("   sudo apt install python3-opencv", file=sys.stderr)
             print("E se 'opencv-python' está no seu requirements.txt e instalado no venv:", file=sys.stderr)
             print("   venv/bin/pip install -r requirements.txt", file=sys.stderr)
        else:
            print(f"Erro: Não foi possível importar um módulo necessário: {e}", file=sys.stderr)
            print("Verifique se todas as dependências estão instaladas e se a estrutura do projeto está correta.", file=sys.stderr)
        # Imprime o traceback completo para depuração
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("-----------------\n", file=sys.stderr)
        sys.exit(1)

    except FileNotFoundError as e:
         print(f"\n--- ERRO: ARQUIVO NÃO ENCONTRADO ---", file=sys.stderr)
         print(f"{e}", file=sys.stderr)
         print("Verifique se todos os arquivos necessários (como .glade ou config.ini) estão nos locais corretos.", file=sys.stderr)
         print("----------------------------------\n", file=sys.stderr)
         sys.exit(1)

    except Exception as e:
        print(f"\n--- ERRO INESPERADO NO LANÇADOR ---", file=sys.stderr)
        print(f"Tipo: {type(e).__name__}", file=sys.stderr)
        print(f"Erro: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("-----------------\n", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
