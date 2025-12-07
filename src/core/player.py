# -*- coding: utf-8 -*-
# Importações Essenciais (AQUI ESTÁ O IMPORT PROBLEMÁTICO)
import time
import os
import sys
# >>>>> from src.core.calibrator import CalibratorWindow <<<<<--- REMOVER ESTA LINHA

# Constantes de Cor
ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§"
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"

def imprimir_frame_colorido(frame_data):
    """Processa e imprime um único frame ASCII colorido."""
    output_buffer = []
    lines = frame_data.split('\n')

    for line in lines:
        if not line:
            continue
        pixels = line.split(COLOR_SEPARATOR)
        line_buffer = []
        # Itera de 2 em 2 para pegar par (char, code)
        for i in range(0, len(pixels) - 1, 2):
            char = pixels[i]
            code = pixels[i+1]
            # Garante que 'code' seja numérico antes de formatar
            if char and code.isdigit():
                line_buffer.append(f"\033[38;5;{code}m{char}")
            elif char: # Fallback: imprime sem cor se 'code' não for número
                line_buffer.append(char)
        output_buffer.append("".join(line_buffer))

    # Imprime o buffer de uma vez, garantindo o reset no final
    sys.stdout.write("\n".join(output_buffer) + ANSI_RESET)
    sys.stdout.flush()

def iniciar_player(arquivo_path, loop=False):
    """Ponto de entrada da biblioteca do player."""
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' não encontrado.")

    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Erro ao ler o arquivo '{arquivo_path}': {e}")

    parts = content.split('\n', 1)
    if len(parts) < 2:
        raise ValueError("Formato de arquivo inválido: FPS ou conteúdo não encontrado.")

    try:
        fps = float(parts[0].strip())
    except ValueError as e:
        raise ValueError(f"FPS inválido na primeira linha ('{parts[0].strip()}'): {e}")

    frame_content = parts[1]
    if frame_content.startswith("[FRAME]\n"): frame_content = frame_content[len("[FRAME]\n"):]
    frames = frame_content.split("[FRAME]\n")

    if not frames or all(not f.strip() for f in frames):
         raise ValueError("Nenhum frame válido encontrado no arquivo após o FPS.")

    os.system('cls' if os.name == 'nt' else 'clear')

    is_static_image = (fps == 0)

    try:
        if is_static_image:
            frame_data = frames[0]
            if frame_data.strip():
                sys.stdout.write(ANSI_CLEAR_AND_HOME)
                imprimir_frame_colorido(frame_data)
                print("\n\n[Imagem Estática - Pressione Enter para sair]")
                input()
        else:
            delay = 1.0 / fps
            while True:
                for frame_data in frames:
                    if not frame_data.strip(): continue
                    sys.stdout.write(ANSI_CLEAR_AND_HOME)
                    imprimir_frame_colorido(frame_data)
                    time.sleep(delay)
                if not loop: break
    except KeyboardInterrupt:
        print("\nPlayer interrompido pelo usuário.")
    finally:
        print(ANSI_RESET)
        os.system('cls' if os.name == 'nt' else 'clear')

# Bloco para teste rápido (opcional, pode ser removido ou comentado)
if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        test_loop = len(sys.argv) > 2 and sys.argv[2] == '--loop'
        try:
            print(f"Testando player com: {test_file} (Loop: {test_loop})")
            print("Pressione Ctrl+C para parar.")
            time.sleep(1.5) # Pausa para ler a mensagem
            iniciar_player(test_file, test_loop)
        except Exception as e:
            print(f"\n--- Erro no Teste do Player ---")
            print(e)
            print("----------------------------")
            # Adiciona input para manter o terminal aberto em caso de erro no teste
            input("Pressione Enter para sair...")
    else:
        print("Uso para teste: python src/core/player.py <caminho_arquivo.txt> [--loop]")
