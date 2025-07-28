# # Ritual de Magia Negra Digital: Maestro das Sombras v1.0
# O coração do pacto, main.py. Orquestra a conversão em massa: lê config, lista todos os vídeos .mp4 na pasta de entrada, chama converter pra cada um. Rode com python3 main.py. (Sem --loop, pois foco na conversão; use player.py separadamente pra projeção.)

# #1. Invocações: os, configparser, subprocess.

# #2. Função de Condução: Chama converter pra o vídeo via subprocess.

# #3. Círculo Principal: Lê config, lista vídeos, executa conversão pra cada um, trata erros.
import os
import configparser
import subprocess

#2
def conduzir_conversao(video):
    cmd_converter = ["python3", "converter.py", "--video", video]
    subprocess.run(cmd_converter, check=True)

#3
def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    pasta_entrada = config['Pastas']['input_dir']
    if not os.path.exists(pasta_entrada):
        print(f"Erro: Pasta '{pasta_entrada}' não encontrada.")
        return
    videos = [f for f in os.listdir(pasta_entrada) if f.endswith('.mp4')]
    if not videos:
        print(f"Nenhum vídeo .mp4 encontrado em '{pasta_entrada}'.")
        return
    for video in videos:
        print(f"Conjurando conversão para '{video}'...")
        try:
            conduzir_conversao(video)
            print(f"Conversão de '{video}' concluída.")
        except subprocess.CalledProcessError as e:
            print(f"Conversão falhou para '{video}': {e}")

if __name__ == '__main__':
    main()

# "A ordem nasce do caos." - Friedrich Nietzsche, filósofo sombrio, abençoando nosso código aberto.