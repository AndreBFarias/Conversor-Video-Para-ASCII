import time
import os
import sys

ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§"
ANSI_CLEAR_AND_HOME = "\033[2J\033[H"


def imprimir_frame_colorido(frame_data):
    output_buffer = []
    lines = frame_data.split('\n')

    for line in lines:
        if not line:
            continue
        pixels = line.split(COLOR_SEPARATOR)
        line_buffer = []
        for i in range(0, len(pixels) - 1, 2):
            char = pixels[i]
            code = pixels[i+1]
            if char and code.isdigit():
                line_buffer.append(f"\033[38;5;{code}m{char}")
            elif char:
                line_buffer.append(char)
        output_buffer.append("".join(line_buffer))

    sys.stdout.write("\n".join(output_buffer) + ANSI_RESET)
    sys.stdout.flush()


def iniciar_player(arquivo_path, loop=False):
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' nao encontrado.")

    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Erro ao ler o arquivo '{arquivo_path}': {e}")

    parts = content.split('\n', 1)
    if len(parts) < 2:
        raise ValueError("Formato de arquivo invalido: FPS ou conteudo nao encontrado.")

    try:
        fps = float(parts[0].strip())
    except ValueError as e:
        raise ValueError(f"FPS invalido na primeira linha ('{parts[0].strip()}'): {e}")

    frame_content = parts[1]
    if frame_content.startswith("[FRAME]\n"):
        frame_content = frame_content[len("[FRAME]\n"):]
    frames = frame_content.split("[FRAME]\n")

    if not frames or all(not f.strip() for f in frames):
        raise ValueError("Nenhum frame valido encontrado no arquivo apos o FPS.")

    os.system('cls' if os.name == 'nt' else 'clear')

    is_static_image = (fps == 0)

    try:
        if is_static_image:
            frame_data = frames[0]
            if frame_data.strip():
                sys.stdout.write(ANSI_CLEAR_AND_HOME)
                imprimir_frame_colorido(frame_data)
                print("\n\n[Imagem Estatica - Pressione Enter para sair]")
                input()
        else:
            delay = 1.0 / fps
            while True:
                for frame_data in frames:
                    if not frame_data.strip():
                        continue
                    sys.stdout.write(ANSI_CLEAR_AND_HOME)
                    imprimir_frame_colorido(frame_data)
                    time.sleep(delay)
                if not loop:
                    break
    except KeyboardInterrupt:
        print("\nPlayer interrompido pelo usuario.")
    finally:
        print(ANSI_RESET)
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        test_loop = len(sys.argv) > 2 and sys.argv[2] == '--loop'
        try:
            print(f"Testando player com: {test_file} (Loop: {test_loop})")
            print("Pressione Ctrl+C para parar.")
            time.sleep(1.5)
            iniciar_player(test_file, test_loop)
        except Exception as e:
            print(f"\n--- Erro no Teste do Player ---")
            print(e)
            print("----------------------------")
            input("Pressione Enter para sair...")
    else:
        print("Uso para teste: python src/core/player.py <caminho_arquivo.txt> [--loop]")
