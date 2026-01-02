#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Player Module - Playback for ASCII/Pixel Art videos
Supports terminal (ANSI), window (OpenCV), and hybrid display modes
With interactive zoom controls and ASCII-in-window rendering
"""
import time
import os
import sys
import cv2
import configparser

# Import renderer functions
from .renderer import render_terminal, render_window, cleanup_window, DEFAULT_SCALE_FACTOR
try:
    from .renderer import render_window_gtk, GTK_AVAILABLE
except ImportError:
    GTK_AVAILABLE = False
    render_window_gtk = None

ANSI_RESET = "\033[0m"


def iniciar_player(arquivo_path, loop=False, config=None):
    """
    Play ASCII/Pixel Art video with configurable display mode
    
    Args:
        arquivo_path: Path to .txt file with ASCII art
        loop: Whether to loop playback
        config: ConfigParser object (optional, for display_mode)
    """
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
            # Static image display
            frame_data = frames[0]
            if frame_data.strip():
                if display_mode in ['terminal', 'both']:
                    render_terminal(frame_data)
                
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
                    
                    # Render based on mode
                    if display_mode in ['terminal', 'both']:
                        render_terminal(frame_data)
                    
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

