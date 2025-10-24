#!/usr/bin/env python3

"""
#1
Ponto de entrada do Player ASCII (Linha de Comando).

Permite executar o player diretamente do terminal, com loop por padrão.
Uso "Prático": Se nenhum arquivo for fornecido, ele reproduz
automaticamente o arquivo .txt mais recente da pasta de saída.
"""

import argparse
import sys
import os
import configparser

# Define a raiz do projeto (um nível acima de onde este script está, se ele estivesse em 'src')
# Mas como ele está na raiz, o BASE_DIR é o diretório atual.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

# #2. Função find_latest_file (Nova)
def find_latest_file(config):
    """
    Encontra o arquivo .txt modificado mais recentemente na pasta de saída.
    """
    try:
        output_dir = config.get('Pastas', 'output_dir')
    except Exception:
        print("Erro: 'output_dir' não encontrado no config.ini.", file=sys.stderr)
        return None
        
    output_path = os.path.join(BASE_DIR, output_dir)
    if not os.path.exists(output_path):
        print(f"Erro: Pasta de saída '{output_path}' não existe.", file=sys.stderr)
        return None

    # Encontra todos os arquivos .txt
    txt_files = [
        os.path.join(output_path, f) 
        for f in os.listdir(output_path) 
        if f.endswith('.txt')
    ]

    if not txt_files:
        return None

    # Retorna o arquivo mais recente (baseado no tempo de modificação)
    latest_file = max(txt_files, key=os.path.getmtime)
    return latest_file

# #3. Função main (Atualizada)
def main():
    # Adiciona a raiz do projeto ao sys.path para importar 'src'
    sys.path.insert(0, BASE_DIR)

    parser = argparse.ArgumentParser(description="Player de Animação ASCII Colorida")
    parser.add_argument(
        "-f", "--arquivo", 
        required=False,  # Não é mais obrigatório
        help="Caminho para o arquivo .txt. Se omitido, toca o arquivo mais recente."
    )
    parser.add_argument(
        "--no-loop", 
        action="store_true", 
        help="Executa a animação apenas uma vez (o padrão é loop infinito)."
    )
    args = parser.parse_args()

    # Importa o core
    try:
        from src.core import iniciar_player
    except ImportError as e:
        print(f"Erro: Não foi possível importar o módulo 'src'.\nVerifique a estrutura de pastas. Erro: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado na importação: {e}", file=sys.stderr)
        sys.exit(1)
        
    file_to_play = None

    if args.arquivo:
        # O usuário especificou um arquivo
        file_to_play = args.arquivo
    else:
        # Lógica "Prática": Encontrar o mais recente
        print("Nenhum arquivo especificado. Procurando o mais recente...")
        config = configparser.ConfigParser()
        if not config.read(CONFIG_PATH):
             print(f"Erro: config.ini não encontrado em '{CONFIG_PATH}'", file=sys.stderr)
             sys.exit(1)
        
        file_to_play = find_latest_file(config)
        
        if file_to_play:
            print(f"Reproduzindo: {os.path.basename(file_to_play)}")
        else:
            print(f"Erro: Nenhum arquivo .txt encontrado na pasta de saída definida no config.ini.", file=sys.stderr)
            sys.exit(1)

    # Execução
    try:
        # Chama o player. O loop é 'True' a menos que --no-loop seja usado.
        iniciar_player(arquivo_path=file_to_play, loop=(not args.no_loop))
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em '{file_to_play}'", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nPlayer finalizado pelo usuário.")
    except Exception as e:
        print(f"Erro durante a execução do player: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
