# Importações
import time
import os
import sys

# Constantes de Cor
ANSI_RESET = "\033[0m"
COLOR_SEPARATOR = "§" # Delimitador (deve ser o mesmo do converter.py)
ANSI_CLEAR_AND_HOME = "\033[2J\033[H" # Limpar Tela e Mover para Topo

# #2. Função para processar e imprimir um frame colorido
def imprimir_frame_colorido(frame_data):
    output_buffer = []
    lines = frame_data.split('\n')
    
    for line in lines:
        if not line:
            continue
        
        # (CORRIGIDO) O split agora gera ['char', 'code', 'char', 'code', '']
        pixels = line.split(COLOR_SEPARATOR)
        
        line_buffer = []
        # Iteramos de 2 em 2
        for i in range(0, len(pixels) - 1, 2): # -1 para ignorar o ''] final
            char = pixels[i]
            code = pixels[i+1]
                
            if char:
                # Monta a string de cor ANSI
                line_buffer.append(f"\033[38;5;{code}m{char}")
            elif i == 0:
                # O primeiro char pode ser vazio se a linha começar com o separador
                # (o que não deve acontecer, mas por segurança)
                pass 
        
        output_buffer.append("".join(line_buffer))
    
    # Imprime o buffer de uma vez
    sys.stdout.write("\n".join(output_buffer) + ANSI_RESET)
    sys.stdout.flush()

# Ponto de entrada da biblioteca
def iniciar_player(arquivo_path, loop=False):
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' não encontrado.")
    
    try:
        with open(arquivo_path, 'r') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Erro ao ler o arquivo: {e}")

    parts = content.split('\n', 1)
    if len(parts) < 2:
        raise ValueError("Formato de arquivo inválido. FPS não encontrado.")

    try:
        fps = float(parts[0])
        delay = 1.0 / fps
    except ValueError:
        raise ValueError("FPS inválido no arquivo.")
        
    # O metatexto [FRAME]
    frames = parts[1].split("[FRAME]\n")
    
    # Limpa a tela UMA VEZ
    os.system('cls' if os.name == 'nt' else 'clear')
    
    try:
        # Loop de Playback
        while True:
            for frame in frames:
                
                # (CORRIGIDO) Limpa a tela e move o cursor ANTES de imprimir
                sys.stdout.write(ANSI_CLEAR_AND_HOME)
                
                # Chama a função de impressão colorida
                imprimir_frame_colorido(frame)
                
                # Sleep (delay)
                time.sleep(delay)
            
            if not loop:
                break
                
    except KeyboardInterrupt:
        print("\nPlayer interrompido.")
    finally:
        # Limpa a cor e a tela ao sair
        print(ANSI_RESET)
        os.system('cls' if os.name == 'nt' else 'clear')
