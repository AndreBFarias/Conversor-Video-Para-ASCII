# O sussurro final, player.py. Lê o .txt e anima no terminal. Rode com python3 player.py --arquivo saida.txt --loop sim.

# #1. Invocações: os, time, sys, argparse.

# #2. Função de Projeção: Lê FPS e frames, calcula intervalo, loop: limpa, imprime, pausa. Trata erros.

# #3. Círculo Principal: Parseia args, inicia projeção com loop.

# Ritual de Magia Negra Digital: Projeção de Sombras v1.0
import os
import time
import sys
import argparse
import configparser

def projetar_ascii(caminho_arquivo, loop_infinito):
    print(f"Projetando sombras de '{caminho_arquivo}'...")
    try:
        with open(caminho_arquivo, 'r') as f:
            linhas = f.readlines()
            fps = float(linhas[0].strip())
            conteudo_frames = "".join(linhas[1:])
            quadros = conteudo_frames.split('[FRAME]\n')
        intervalo_quadro = 1.0 / fps
        nome_base = os.path.basename(caminho_arquivo)
        while True:
            for quadro in quadros:
                os.system('clear')
                rodape = f"\nArquivo: {nome_base} | FPS: {fps:.1f}"
                sys.stdout.write(quadro + rodape)
                sys.stdout.flush()
                time.sleep(intervalo_quadro)
            if not loop_infinito:
                break
    except FileNotFoundError:
        print(f"Erro: '{caminho_arquivo}' não encontrado.")
    except IndexError:
        print("Erro: Arquivo vazio ou corrompido.")
    except ValueError:
        print("Erro: FPS corrompido.")
    except KeyboardInterrupt:
        print("\nProjeção banida.")
        os.system('clear')

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    default_arquivo = config.get('Player', 'arquivo', fallback=None)
    default_loop = config.get('Player', 'loop', fallback='sim') == 'sim'

    parser = argparse.ArgumentParser(description="Projeta animação ASCII.")
    parser.add_argument("--arquivo", help="Caminho pro arquivo ASCII.txt.", default=default_arquivo)
    parser.add_argument("--loop", choices=["sim", "nao"], help="Loop infinito?", default="sim" if default_loop else "nao")
    args = parser.parse_args()

    if args.arquivo is None:
        parser.error("O argumento --arquivo é requerido se não definido no config.ini")

    loop = args.loop == "sim"
    projetar_ascii(args.arquivo, loop)

if __name__ == '__main__':
    main()

# "A liberdade é o oxigênio da alma." - Henri Frédéric Amiel, respirando nosso código aberto e selvagem.
