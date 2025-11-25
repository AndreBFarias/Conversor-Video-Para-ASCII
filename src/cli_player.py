#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ponto de entrada (CLI) para o Player ASCII.

Este script é chamado pelo 'src/main.py' (GUI) para reproduzir
um arquivo .txt em um novo terminal.
"""

import os
import sys
import argparse
import configparser
import time # Adicionado para a pausa

# Adiciona a raiz do projeto ao sys.path para encontrar 'src'
# Como este arquivo está em src/, a raiz é o diretório pai
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from src.core.player import iniciar_player
except ImportError as e:
    print(f"Erro fatal: Não foi possível importar 'src.core.player'.")
    print(f"Verifique se 'src/core/player.py' existe. Erro: {e}")
    # Imprime traceback para mais detalhes
    import traceback
    traceback.print_exc()
    input("Pressione Enter para sair...")
    sys.exit(1)

def main():
    config = None
    config_file = None

    # --- Leitura dos Argumentos ---
    parser = argparse.ArgumentParser(description="Player de Vídeo ASCII (CLI)")
    parser.add_argument('-f', '--file', dest='file_path', default=None,
                        help="Caminho do arquivo .txt para reproduzir.")
    parser.add_argument('-l', '--loop', dest='loop', action='store_true',
                        help="Ativa o loop da animação.")
    parser.add_argument('--config', dest='config_path', default='config.ini',
                        help="Caminho para o config.ini (usado para fallbacks).")
    args = parser.parse_args()

    file_to_play = args.file_path
    loop = args.loop

    # --- Lógica de Fallback (se -f não for fornecido) ---
    if not file_to_play:
        print("Nenhum arquivo fornecido via -f. Lendo config.ini...")
        if not os.path.exists(args.config_path):
            print(f"Erro: Arquivo de configuração não encontrado: {args.config_path}")
            input("Pressione Enter para sair...")
            return

        try:
            # --- #1. CORREÇÃO DE INTERPOLAÇÃO ---
            config = configparser.ConfigParser(interpolation=None)
            config.read(args.config_path, encoding='utf-8')

            file_to_play = config.get('Player', 'arquivo', fallback=None)
            if not file_to_play:
                print("Erro: 'arquivo' não definido em [Player] no config.ini.")
                input("Pressione Enter para sair...")
                return

            # Se o loop não foi ativado via flag, checa o config
            if not loop:
                loop_val = config.get('Player', 'loop', fallback='nao').lower()
                loop = loop_val in ['sim', 'yes', 'true', '1', 'on']

        except Exception as e:
            print(f"Erro ao ler config.ini: {e}")
            input("Pressione Enter para sair...")
            return

    # --- Execução ---
    if not os.path.exists(file_to_play):
        print(f"Erro: Arquivo não encontrado: {file_to_play}")
        input("Pressione Enter para sair...")
        return

    print(f"Reproduzindo: {file_to_play} (Loop: {loop})")
    print("Pressione Ctrl+C para parar.")
    time.sleep(1.5) # Pausa para o usuário ler a mensagem

    try:
        iniciar_player(file_to_play, loop)
    except Exception as e:
        print(f"\n--- ERRO NA REPRODUÇÃO ---")
        print(e)
        print("----------------------------")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
