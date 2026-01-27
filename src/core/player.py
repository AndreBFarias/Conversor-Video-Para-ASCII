#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Player Module - Playback for ASCII/Pixel Art videos
Supports terminal (ANSI), window (OpenCV), and hybrid display modes
With interactive zoom controls and ASCII-in-window rendering
Matrix Rain overlay support for terminal playback
"""
import time
import os
import sys
import cv2
import configparser
import random

from .renderer import render_terminal, render_window, cleanup_window, DEFAULT_SCALE_FACTOR
try:
    from .renderer import render_window_gtk, GTK_AVAILABLE
except ImportError:
    GTK_AVAILABLE = False
    render_window_gtk = None

ANSI_RESET = "\033[0m"

KATAKANA_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=<>")
BINARY_CHARS = list("01")
ASCII_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
COLOR_SEPARATOR = "§"
GREEN_BRIGHT = 46
GREEN_MED = 40
GREEN_DARK = 34
GREEN_DARKER = 28
GREEN_DARKEST = 22


class TerminalMatrixRain:
    def __init__(self, width: int, height: int, num_particles: int = 500, char_set: str = 'katakana', mode: str = 'overlay'):
        self.width = max(1, width)
        self.height = max(1, height)
        self.mode = mode
        self.speed_multiplier = 1.0
        self.trail_length = min(height, 12)

        if char_set == 'katakana':
            self.chars = KATAKANA_CHARS
        elif char_set == 'binary':
            self.chars = BINARY_CHARS
        else:
            self.chars = ASCII_CHARS

        self._init_columns()

    def _init_columns(self):
        self.head_y = []
        self.speeds = []
        self.char_grid = []

        for x in range(self.width):
            self.head_y.append(random.uniform(-self.trail_length, self.height))
            self.speeds.append(random.uniform(0.3, 1.0))

        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(random.choice(self.chars))
            self.char_grid.append(row)

        self.brightness_grid = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

        for _ in range(5):
            self._update_internal(0.1)

    def _update_internal(self, dt: float):
        for x in range(self.width):
            movement = self.speeds[x] * 5.0 * dt * self.speed_multiplier
            self.head_y[x] += movement

            if self.head_y[x] > self.height + self.trail_length:
                self.head_y[x] = random.uniform(-self.trail_length, 0)
                self.speeds[x] = random.uniform(0.3, 1.0)

        for y in range(self.height):
            for x in range(self.width):
                self.brightness_grid[y][x] *= 0.85

        for x in range(self.width):
            head = int(self.head_y[x])
            for offset in range(self.trail_length):
                y = head - offset
                if 0 <= y < self.height:
                    if offset == 0:
                        self.brightness_grid[y][x] = 1.5
                    elif offset == 1:
                        self.brightness_grid[y][x] = max(self.brightness_grid[y][x], 1.3)
                    else:
                        trail_val = 1.0 - (offset / self.trail_length) * 0.7
                        self.brightness_grid[y][x] = max(self.brightness_grid[y][x], trail_val)

        if random.random() < 0.3:
            num_changes = max(1, int(self.width * self.height * 0.02))
            for _ in range(num_changes):
                cy = random.randint(0, self.height - 1)
                cx = random.randint(0, self.width - 1)
                self.char_grid[cy][cx] = random.choice(self.chars)

    def update(self, dt: float = 0.033, speed_multiplier: float = 1.0):
        self.speed_multiplier = speed_multiplier
        self._update_internal(dt)

    def render_overlay(self, frame_data: str, speed_multiplier: float = 1.0) -> str:
        lines = frame_data.split('\n')
        if not lines:
            return frame_data

        first_line_pixels = lines[0].split(COLOR_SEPARATOR) if lines else []
        detected_width = len(first_line_pixels) // 2 if first_line_pixels else 80
        detected_height = len(lines)

        if self.width != detected_width or self.height != detected_height:
            self.width = max(1, detected_width)
            self.height = max(1, detected_height)
            self._init_columns()

        self.update(0.033, speed_multiplier)

        result_lines = []
        for y, line in enumerate(lines):
            if y >= self.height:
                result_lines.append(line)
                continue

            pixels = line.split(COLOR_SEPARATOR)
            new_pixels = []

            for i in range(0, len(pixels) - 1, 2):
                char = pixels[i]
                code = pixels[i + 1]
                x = i // 2

                if x >= self.width:
                    new_pixels.append(char)
                    new_pixels.append(code)
                    continue

                is_background = False
                if code.isdigit():
                    color_val = int(code)
                    if 232 <= color_val <= 240:
                        is_background = True
                    elif color_val == 16:
                        is_background = True
                    elif char.strip() == '' or char == ' ':
                        is_background = True

                brightness = self.brightness_grid[y][x]

                if brightness > 0.05 and is_background:
                    rain_char = self.char_grid[y][x]

                    if brightness >= 1.2:
                        color_code = GREEN_BRIGHT
                    elif brightness >= 0.8:
                        color_code = GREEN_MED
                    elif brightness >= 0.5:
                        color_code = GREEN_DARK
                    elif brightness >= 0.3:
                        color_code = GREEN_DARKER
                    else:
                        color_code = GREEN_DARKEST

                    new_pixels.append(rain_char)
                    new_pixels.append(str(color_code))
                else:
                    new_pixels.append(char)
                    new_pixels.append(code)

            result_lines.append(COLOR_SEPARATOR.join(new_pixels) + COLOR_SEPARATOR)

        return '\n'.join(result_lines)


def iniciar_player(arquivo_path, loop=False, config=None):
    """
    Play ASCII/Pixel Art video with configurable display mode

    Args:
        arquivo_path: Path to .txt file with ASCII art
        loop: Whether to loop playback
        config: ConfigParser object (optional, for display_mode)
    """
    matrix_rain = None
    matrix_speed = 1.0

    if config:
        try:
            matrix_enabled = config.getboolean('MatrixRain', 'enabled', fallback=False)
            if matrix_enabled:
                matrix_mode = config.get('MatrixRain', 'mode', fallback='overlay')
                matrix_charset = config.get('MatrixRain', 'char_set', fallback='katakana')
                matrix_particles = config.getint('MatrixRain', 'num_particles', fallback=500)
                matrix_speed = config.getfloat('MatrixRain', 'speed_multiplier', fallback=1.0)
                matrix_rain = TerminalMatrixRain(
                    width=150,
                    height=50,
                    num_particles=matrix_particles,
                    char_set=matrix_charset,
                    mode=matrix_mode
                )
                print(f"[Matrix Rain] Ativado no player: mode={matrix_mode}, particles={matrix_particles}")
        except Exception as e:
            print(f"[Matrix Rain] Erro ao inicializar: {e}")
            matrix_rain = None

    if not os.path.exists(arquivo_path):
        raise FileNotFoundError(f"Arquivo ASCII '{arquivo_path}' nao encontrado.")

    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Erro ao ler o arquivo '{arquivo_path}': {e}")

    # Parse file format
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

    # Determine display mode from config
    display_mode = 'terminal'  # Default fallback
    initial_scale = DEFAULT_SCALE_FACTOR
    
    if config:
        try:
            display_mode = config.get('Geral', 'display_mode', fallback='terminal').lower()
            # Try to read initial zoom from config
            initial_scale = config.getint('Quality', 'player_zoom', fallback=DEFAULT_SCALE_FACTOR)
            # Handle float zoom values (convert to int)
            if initial_scale < 1:
                initial_scale = int(initial_scale * 10) if initial_scale > 0 else DEFAULT_SCALE_FACTOR
        except Exception:
            display_mode = 'terminal'
            initial_scale = DEFAULT_SCALE_FACTOR
    
    # Validate display mode
    valid_modes = ['terminal', 'window', 'both']
    if display_mode not in valid_modes:
        print(f"Aviso: display_mode '{display_mode}' invalido. Usando 'terminal'.")
        display_mode = 'terminal'
    
    # Clear screen for initial display
    os.system('clear')
    
    is_static_image = (fps == 0)
    window_name = "ASCII Converter Output"
    current_scale = initial_scale

    # Determine rendering mode
    use_gtk = GTK_AVAILABLE and display_mode in ['window', 'both']
    
    # Show controls for window mode
    if display_mode in ['window', 'both']:
        if use_gtk:
            print("Controles GTK:")
            print("  [Arrastar bordas] - Redimensionar livremente (aspect ratio preservado!)")
            print("  [q] ou [ESC] - Sair")
            print("  Player GTK - Miniatura a fullscreen sem distorcao")
        else:
            print("Controles OpenCV:")
            print("  [Arrastar bordas] - Redimensionar janela")
            print("  [q] ou [ESC] - Sair")
            print("  AVISO: OpenCV tem limitacoes de aspect ratio")
        print("")

    try:
        if is_static_image:
            frame_data = frames[0]
            if frame_data.strip():
                frame_to_render = frame_data
                if matrix_rain and display_mode in ['terminal', 'both']:
                    frame_to_render = matrix_rain.render_overlay(frame_data, matrix_speed)

                if display_mode in ['terminal', 'both']:
                    render_terminal(frame_to_render)
                
                gtk_window = None
                
                if display_mode in ['window', 'both']:
                    if use_gtk:
                        # GTK mode - perfect aspect ratio!
                        gtk_window = render_window_gtk(None, None, 
                                                      is_ascii=True, ascii_string=frame_data)
                        
                        print("\n[Imagem Estatica - Pressione ESC ou 'q' para sair]")
                        
                        # GTK event loop for static image
                        import gi
                        gi.require_version('Gtk', '3.0')
                        from gi.repository import Gtk
                        
                        Gtk.main()  # Will exit when window closes or q/ESC pressed
                    else:
                        # OpenCV fallback
                        render_window(None, window_name, current_scale, 
                                     is_ascii=True, ascii_string=frame_data)
                        
                        print("\n[Imagem Estatica - Pressione ESC ou 'q' para sair]")
                        
                        while True:
                            key = cv2.waitKey(100) & 0xFF
                            if key == ord('q') or key == 27:  # ESC
                                break
                
                elif display_mode == 'terminal':
                    print("\n\n[Imagem Estatica - Pressione Enter para sair]")
                    input()
        else:
            # Video playback
            delay = 1.0 / fps
            delay_ms = int(delay * 1000)
            
            gtk_window = None
            
            while True:
                for frame_data in frames:
                    if not frame_data.strip():
                        continue

                    frame_to_render = frame_data
                    if matrix_rain and display_mode in ['terminal', 'both']:
                        frame_to_render = matrix_rain.render_overlay(frame_data, matrix_speed)

                    if display_mode in ['terminal', 'both']:
                        render_terminal(frame_to_render)

                    if display_mode in ['window', 'both']:
                        if use_gtk:
                            # GTK mode
                            gtk_window = render_window_gtk(None, gtk_window,
                                                          is_ascii=True, ascii_string=frame_data)
                            
                            # Process GTK events
                            gtk_window.process_events()
                            
                            # Check if window was closed
                            if gtk_window.should_close:
                                return
                            
                            # Sleep for frame timing
                            time.sleep(delay)
                        else:
                            # OpenCV fallback
                            current_scale = render_window(None, window_name, current_scale,
                                                         is_ascii=True, ascii_string=frame_data)
                            
                            # Handle timing and input
                            key = cv2.waitKey(delay_ms) & 0xFF
                            if key == ord('q') or key == 27:  # ESC
                                return
                    else:
                        # Terminal only mode
                        time.sleep(delay)
                
                if not loop:
                    break
                    
    except KeyboardInterrupt:
        print("\nPlayer interrompido pelo usuario.")
    finally:
        # Cleanup
        if display_mode in ['window', 'both']:
            cleanup_window(window_name)
        if display_mode in ['terminal', 'both']:
            print(ANSI_RESET)
            os.system('clear')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        test_loop = len(sys.argv) > 2 and sys.argv[2] == '--loop'
        
        # Try to load config for display mode
        config = None
        config_path = 'config.ini'
        if os.path.exists(config_path):
            config = configparser.ConfigParser(interpolation=None)
            config.read(config_path)
        
        try:
            print(f"Testando player com: {test_file} (Loop: {test_loop})")
            if config:
                mode = config.get('Geral', 'display_mode', fallback='terminal')
                print(f"Modo de exibição: {mode}")
            print("Pressione Ctrl+C (terminal) ou ESC/'q' (window) para parar.")
            time.sleep(1.5)
            iniciar_player(test_file, test_loop, config)
        except Exception as e:
            print("\n--- Erro no Teste do Player ---")
            print(e)
            print("----------------------------")
            input("Pressione Enter para sair...")
    else:
        print("Uso para teste: python src/core/player.py <caminho_arquivo.txt> [--loop]")

