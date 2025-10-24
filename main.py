#!/usr/bin/env python3

"""
Ponto de entrada principal (Launcher) para a Interface Gráfica (GTK).

Este script existe para inicializar corretamente o ambiente e executar
o aplicativo principal a partir do módulo 'src'.

REQUER DEPENDÊNCIAS DO 'requirements_gtk.txt'
"""

import os
import sys

def main():
    """
    Configura o ambiente e inicia a aplicação principal.
    """
    # Adiciona a raiz do projeto ao sys.path para garantir que 'src' seja importável
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    try:
        # Importa e executa a lógica principal da aplicação
        from src.main import run_app
        run_app()
    except ImportError as e:
        # Erro comum se 'PyGObject' não estiver instalado
        if "gi" in str(e):
            print("Erro Crítico: Não foi possível importar 'gi' (PyGObject).", file=sys.stderr)
            print("Esta interface gráfica é opcional.", file=sys.stderr)
            print("Execute: pip install -r requirements_gtk.txt", file=sys.stderr)
            print("(Isso pode exigir dependências de sistema via 'apt')", file=sys.stderr)
        else:
            print(f"Erro Crítico: Não foi possível importar o módulo 'src'.\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado no launcher: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
