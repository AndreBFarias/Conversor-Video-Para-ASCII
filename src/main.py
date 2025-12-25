# -*- coding: utf-8 -*-
# Importações
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import os
import sys
import configparser
import subprocess
import threading
import platform
import shlex
import traceback
from src.utils.logger import setup_logger

logger = setup_logger()

# Import player for in-process playback (GTK compatible)
try:
    from src.core.player import iniciar_player
    PLAYER_AVAILABLE = True
except ImportError:
    PLAYER_AVAILABLE = False
    logger.warning("Player module not available, falling back to subprocess")

# --- Definição de Caminhos MAIS ROBUSTA ---
try:
    # __file__ é o caminho para src/main.py
    # BASE_DIR será o diretório 'src'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # ROOT_DIR será o diretório pai de 'src' (a raiz do projeto)
    ROOT_DIR = os.path.dirname(BASE_DIR)
    # Garante que a raiz esteja no path para imports como 'src.core'
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

    UI_FILE = os.path.join(BASE_DIR, "gui", "main.glade")
    LOGO_FILE = os.path.join(ROOT_DIR, "assets", "logo.png")
    CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")

    # Caminhos para scripts (usando ROOT_DIR e BASE_DIR)
    # Usa sys.executable para garantir que o Python correto seja usado (do venv se ativo)
    PYTHON_EXEC = sys.executable
    PLAYER_SCRIPT = os.path.join(BASE_DIR, "cli_player.py")
    CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "converter.py")
    IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "image_converter.py")
    PIXEL_ART_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_converter.py")
    PIXEL_ART_IMAGE_CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "pixel_art_image_converter.py")
    CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "calibrator.py")
    REALTIME_SCRIPT = os.path.join(BASE_DIR, "core", "realtime_ascii.py")

except Exception as e:
    logger.critical(f"Erro Crítico ao definir caminhos iniciais: {e}")
    # Tenta mostrar erro GTK simples
    try:
        error_dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text="Erro Crítico de Inicialização")
        error_dialog.format_secondary_text(f"Não foi possível definir os caminhos base do aplicativo:\n{e}")
        error_dialog.run()
        error_dialog.destroy()
    except Exception: pass
    sys.exit(1)
# --- Fim da Definição de Caminhos ---


class App:
    def __init__(self):
        self.initialization_failed = False # Flag para Gtk.main()
        self.builder = Gtk.Builder();
        try:
             if not os.path.exists(UI_FILE):
                 # Usa ROOT_DIR para dar contexto ao caminho relativo no erro
                 ui_rel_path = os.path.relpath(UI_FILE, ROOT_DIR)
                 raise FileNotFoundError(f"Arquivo UI '{ui_rel_path}' não encontrado (esperado em: {UI_FILE}).")
             self.builder.add_from_file(UI_FILE)
        except (GLib.Error, FileNotFoundError) as e:
             print(f"Erro Crítico UI: {e}");
             self._show_init_error("Erro Crítico de Interface", f"Não foi possível carregar o arquivo de interface:\n{UI_FILE}\n\nDetalhes: {e}")
             self.initialization_failed = True; return

        self.window = self.builder.get_object("main_window")
        if not self.window:
             self._show_init_error("Erro Crítico UI", "Objeto 'main_window' não encontrado em main.glade.")
             self.initialization_failed = True; return

        self.window.set_title("Êxtase em 4R73")
        self.window.connect("destroy", Gtk.main_quit)

        # --- AJUSTES VISUAIS ---
        try:
            logo_widget = self.builder.get_object("logo_image")
            title_widget = self.builder.get_object("title_label")
            if logo_widget and title_widget:
                if os.path.exists(LOGO_FILE):
                    pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file_at_size(LOGO_FILE, 77, 77)
                    logo_widget.set_from_pixbuf(pixbuf_logo)
                    pixbuf_icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_FILE)
                    self.window.set_icon(pixbuf_icon)
                else: print(f"Aviso: Arquivo de logo não encontrado: {LOGO_FILE}")
                title_widget.set_markup("<span font_desc='Sans Bold 24' foreground='#EAEAEA'>Êxtase em <span foreground='#81c995'>4R73</span></span>")
            else: print("Aviso: Widgets 'logo_image' ou 'title_label' não encontrados.")
        except Exception as e: print(f"Aviso: Erro ao carregar/aplicar assets: {e}")

        self.builder.connect_signals(self)
        self.config = configparser.ConfigParser(interpolation=None)
        self.config_path = CONFIG_PATH

        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Arquivo config.ini não encontrado em '{self.config_path}'")
            with open(self.config_path, 'r', encoding='utf-8') as f: self.config.read_file(f)
            if not self.config.sections(): raise configparser.NoSectionError("Nenhuma seção lida (arquivo vazio?)")

            self.input_dir = self.config.get('Pastas', 'input_dir', fallback='videos_entrada')
            self.output_dir = self.config.get('Pastas', 'output_dir', fallback='videos_saida')
            self.input_dir = os.path.abspath(os.path.join(ROOT_DIR, self.input_dir))
            self.output_dir = os.path.abspath(os.path.join(ROOT_DIR, self.output_dir))
            os.makedirs(self.input_dir, exist_ok=True)
            os.makedirs(self.output_dir, exist_ok=True)
        except (FileNotFoundError, configparser.Error) as e:
            self._show_init_error("Erro Crítico de Configuração", f"Não foi possível ler '{self.config_path}':\n{e}\n\nVerifique o arquivo.");
            self.initialization_failed = True; return

        # Obtenção segura dos widgets restantes
        try:
            self.status_label = self.builder.get_object("status_label")
            
            self.selected_path_label = self.builder.get_object("selected_path_label")
            self.convert_button = self.builder.get_object("convert_button")
            self.convert_all_button = self.builder.get_object("convert_all_button")
            self.play_mode_combo = self.builder.get_object("play_mode_combo")
            self.play_button = self.builder.get_object("play_button")
            self.open_video_button = self.builder.get_object("open_video_button")
            self.open_folder_button = self.builder.get_object("open_folder_button")
            self.calibrate_button = self.builder.get_object("calibrate_button")
            self.open_webcam_button = self.builder.get_object("open_webcam_button")
            self.select_ascii_button = self.builder.get_object("select_ascii_button")
            self.play_ascii_button = self.builder.get_object("play_ascii_button")
            self.options_button = self.builder.get_object("options_button")
            
            # Widgets do Dialog de Opções
            self.options_dialog = self.builder.get_object("options_dialog")
            self.options_notebook = self.builder.get_object("options_notebook")  # IMPORTANTE: Notebook do Glade
            self.opt_loop_check = self.builder.get_object("opt_loop_check")
            self.opt_width_spin = self.builder.get_object("opt_width_spin")
            self.opt_height_spin = self.builder.get_object("opt_height_spin")
            self.opt_sobel_spin = self.builder.get_object("opt_sobel_spin")
            self.opt_aspect_spin = self.builder.get_object("opt_aspect_spin")
            self.opt_luminance_entry = self.builder.get_object("opt_luminance_entry")
            self.opt_h_min_spin = self.builder.get_object("opt_h_min_spin")
            self.opt_h_max_spin = self.builder.get_object("opt_h_max_spin")
            self.opt_s_min_spin = self.builder.get_object("opt_s_min_spin")
            self.opt_s_max_spin = self.builder.get_object("opt_s_max_spin")
            self.opt_v_min_spin = self.builder.get_object("opt_v_min_spin")
            self.opt_v_max_spin = self.builder.get_object("opt_v_max_spin")
            self.opt_erode_spin = self.builder.get_object("opt_erode_spin")
            self.opt_dilate_spin = self.builder.get_object("opt_dilate_spin")
            
            # Create mode selection widgets programmatically (not in glade)
            self.opt_mode_ascii_radio = None
            self.opt_mode_pixelart_radio = None
            self.opt_pixel_size_spin = None
            self.opt_palette_size_spin = None
            self.opt_fixed_palette_check = None

            if None in [self.status_label, self.selected_path_label, self.convert_button,
                         self.convert_all_button, self.play_mode_combo, self.play_button,
                         self.open_video_button, self.open_folder_button, self.calibrate_button,
                         self.open_webcam_button, self.select_ascii_button, self.play_ascii_button,
                         self.options_button, self.options_dialog, self.options_notebook,
                         self.opt_loop_check, self.opt_width_spin]:
                raise TypeError("Um ou mais widgets essenciais não foram encontrados no arquivo .glade.")
        except Exception as e:
             self._show_init_error("Erro Crítico de UI", f"Falha ao obter componentes da interface:\n{e}\n\nVerifique 'src/ui/main.glade'.")
             self.initialization_failed = True; return

        self.selected_file_path = None
        self.selected_folder_path = None
        self.selected_ascii_path = None # Novo atributo para o arquivo ASCII selecionado
        self.conversion_lock = threading.Lock()
        
        # Criar ComboBox de presets de qualidade
        self._create_quality_preset_combo()
        
        self.update_button_states()
        self.window.show_all()

    # --- Funções Auxiliares ---
    def _get_python_executable(self):
        """Retorna o caminho para o executável Python dentro do venv, se existir."""
        venv_python = os.path.join(ROOT_DIR, "venv", "bin", "python3")
        if os.path.exists(venv_python):
            return venv_python
        # Fallback para o executável que está rodando o script atual
        print("Aviso: Executável Python do venv não encontrado, usando sys.executable.")
        return sys.executable

    def _show_init_error(self, title, text):
        """Mostra um diálogo de erro durante o __init__."""
        print(f"Erro de Inicialização: {title} - {text}")
        try:
            # Não depende de self.window, que pode não existir ainda
            dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text=title)
            dialog.format_secondary_text(str(text))
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.run()
        except Exception as e:
            print(f"Falha ao mostrar diálogo de erro de inicialização: {e}")
        # Marca falha para run_app() saber
        self.initialization_failed = True
        Gtk.main_quit() # Tenta sair do loop GTK se ele já tiver iniciado

    def _create_mode_widgets(self):
        """Cria programaticamente os widgets de seleção de modo e Pixel Art"""
        try:
            # Usa o Notebook que já foi carregado do Glade
            if not hasattr(self, 'options_notebook') or not self.options_notebook:
                print("Erro: options_notebook não existe")
                return
            
            notebook = self.options_notebook
            
            # Cria página para configurações de modo
            mode_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            mode_page.set_margin_start(15)
            mode_page.set_margin_end(15)
            mode_page.set_margin_top(15)
            mode_page.set_margin_bottom(15)
            
            # Frame de seleção de modo
            mode_frame = Gtk.Frame(label="Modo de Conversão")
            mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            mode_box.set_margin_start(10)
            mode_box.set_margin_end(10)
            mode_box.set_margin_top(10)
            mode_box.set_margin_bottom(10)
            
            # Radio buttons
            self.opt_mode_ascii_radio = Gtk.RadioButton.new_with_label_from_widget(None, "ASCII Art")
            self.opt_mode_pixelart_radio = Gtk.RadioButton.new_with_label_from_widget(self.opt_mode_ascii_radio, "Pixel Art")
            
            mode_box.pack_start(self.opt_mode_ascii_radio, False, False, 0)
            mode_box.pack_start(self.opt_mode_pixelart_radio, False, False, 0)
            mode_frame.add(mode_box)
            
            # Frame de configurações Pixel Art
            pixelart_frame = Gtk.Frame(label="Configurações Pixel Art")
            pixelart_grid = Gtk.Grid()
            pixelart_grid.set_column_spacing(10)
            pixelart_grid.set_row_spacing(5)
            pixelart_grid.set_margin_start(10)
            pixelart_grid.set_margin_end(10)
            pixelart_grid.set_margin_top(10)
            pixelart_grid.set_margin_bottom(10)
            
            bit_preset_label = Gtk.Label(label="Preset de Bits:")
            bit_preset_label.set_halign(Gtk.Align.START)
            self.opt_bit_preset_combo = Gtk.ComboBoxText()
            self.opt_bit_preset_combo.append("8bit_low", "8-bit Low (16 cores, px:6)")
            self.opt_bit_preset_combo.append("8bit_high", "8-bit High (16 cores, px:5)")
            self.opt_bit_preset_combo.append("16bit_low", "16-bit Low (128 cores, px:3)")
            self.opt_bit_preset_combo.append("16bit_high", "16-bit High (128 cores, px:2)")
            self.opt_bit_preset_combo.append("32bit", "32-bit (256 cores, px:2)")
            self.opt_bit_preset_combo.append("64bit", "64-bit (256 cores, px:1)")
            self.opt_bit_preset_combo.append("custom", "Custom (Manual)")
            self.opt_bit_preset_combo.connect("changed", self.on_bit_preset_changed)
            
            pixel_size_label = Gtk.Label(label="Tamanho do Pixel:")
            pixel_size_label.set_halign(Gtk.Align.START)
            self.opt_pixel_size_spin = Gtk.SpinButton()
            self.opt_pixel_size_spin.set_range(1, 16)
            self.opt_pixel_size_spin.set_increments(1, 1)
            self.opt_pixel_size_spin.set_value(2)
            
            palette_size_label = Gtk.Label(label="Tamanho da Paleta:")
            palette_size_label.set_halign(Gtk.Align.START)
            self.opt_palette_size_spin = Gtk.SpinButton()
            self.opt_palette_size_spin.set_range(2, 256)
            self.opt_palette_size_spin.set_increments(1, 8)
            self.opt_palette_size_spin.set_value(16)
            
            self.opt_fixed_palette_check = Gtk.CheckButton.new_with_label("Usar Paleta Fixa (Retro)")
            
            pixelart_grid.attach(bit_preset_label, 0, 0, 1, 1)
            pixelart_grid.attach(self.opt_bit_preset_combo, 1, 0, 1, 1)
            pixelart_grid.attach(pixel_size_label, 0, 1, 1, 1)
            pixelart_grid.attach(self.opt_pixel_size_spin, 1, 1, 1, 1)
            pixelart_grid.attach(palette_size_label, 0, 2, 1, 1)
            pixelart_grid.attach(self.opt_palette_size_spin, 1, 2, 1, 1)
            pixelart_grid.attach(self.opt_fixed_palette_check, 0, 3, 2, 1)
            
            pixelart_frame.add(pixelart_grid)
            
            # Adiciona frames à página
            mode_page.pack_start(mode_frame, False, False, 0)
            mode_page.pack_start(pixelart_frame, False, False, 0)
            
            # Adiciona nova aba ao notebook
            tab_label = Gtk.Label(label="Modo")
            notebook.append_page(mode_page, tab_label)
            
            # Mostra todos os novos widgets
            mode_page.show_all()
            
            self._mode_widgets_created = True
            print("Widgets de Pixel Art criados com sucesso na aba 'Modo'")
            
        except Exception as e:
            import traceback
            print(f"Erro ao criar widgets de modo: {e}")
            traceback.print_exc()

    def _create_quality_preset_combo(self):
        """Cria ComboBox de presets de qualidade na janela principal"""
        try:
            # Encontra o Box principal (primeiro filho da window)
            main_box = None
            for child in self.window.get_children():
                if isinstance(child, Gtk.Box):
                    main_box = child
                    break
            
            if not main_box:
                print("Aviso: Não foi possível encontrar Box principal para adicionar preset combo")
                return
            
            # Cria um Box horizontal para label + combo
            preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            preset_box.set_margin_start(10)
            preset_box.set_margin_end(10)
            preset_box.set_margin_top(5)
            preset_box.set_margin_bottom(10)
            
            # Label
            preset_label = Gtk.Label(label="Qualidade:")
            preset_label.set_halign(Gtk.Align.START)
            
            # ComboBox
            self.quality_preset_combo = Gtk.ComboBoxText()
            
            self.quality_preset_combo.append("mobile", "Mobile (144p) - 100x25")
            self.quality_preset_combo.append("low", "Low (360p) - 120x30")
            self.quality_preset_combo.append("medium", "Medium (480p) - 180x45")
            self.quality_preset_combo.append("high", "High (540p) - 240x60")
            self.quality_preset_combo.append("veryhigh", "Very High (720p) - 300x75")
            self.quality_preset_combo.append("custom", "Custom (Manual)")
            
            # Carrega preset atual ou usa padrão medium
            current_preset = self.config.get('Quality', 'preset', fallback='medium')
            
            self.quality_preset_combo.set_active_id(current_preset)
            
            # Conecta handler
            self.quality_preset_combo.connect("changed", self.on_quality_preset_changed)
            
            self.quality_preset_combo.set_hexpand(True)
            
            # Adiciona ao box horizontal
            preset_box.pack_start(preset_label, False, False, 0)
            preset_box.pack_start(self.quality_preset_combo, True, True, 0)
            
            # Insere no Box principal logo APÓS o separador (posição 4)
            # Estrutura: Logo+Título(0), Botões selecionar(1), Label path(2), Separador(3), [NOVO AQUI], Grid conversão(4), ...
            main_box.pack_start(preset_box, False, False, 0)
            main_box.reorder_child(preset_box, 4)  # Coloca após o separador
            
            preset_box.show_all()
            
            print("ComboBox de presets de qualidade criado e inserido")
            
        except Exception as e:
            print(f"Erro ao criar ComboBox de presets: {e}")
            import traceback
            traceback.print_exc()
    
    def on_quality_preset_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id or preset_id == 'custom':
            return
        
        try:
            resolution_presets = {
                'mobile': {'width': 100, 'height': 25, 'aspect': 0.50, 'zoom': 1.0},
                'low': {'width': 120, 'height': 30, 'aspect': 0.50, 'zoom': 0.9},
                'medium': {'width': 180, 'height': 45, 'aspect': 0.48, 'zoom': 0.7},
                'high': {'width': 240, 'height': 60, 'aspect': 0.45, 'zoom': 0.6},
                'veryhigh': {'width': 300, 'height': 75, 'aspect': 0.42, 'zoom': 0.5},
            }
            
            if preset_id in resolution_presets:
                preset = resolution_presets[preset_id]
                self.config.set('Conversor', 'target_width', str(preset['width']))
                self.config.set('Conversor', 'target_height', str(preset['height']))
                self.config.set('Conversor', 'char_aspect_ratio', str(preset['aspect']))
                self.config.set('Quality', 'preset', preset_id)
                self.config.set('Quality', 'player_zoom', str(preset['zoom']))
                self.save_config()
                print(f"Preset '{preset_id}' aplicado: {preset['width']}x{preset['height']}, zoom={preset['zoom']}")
        except Exception as e:
            print(f"Erro ao salvar preset: {e}")
    
    def on_bit_preset_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id or preset_id == 'custom':
            return
        
        bit_presets = {
            '8bit_low': {'pixel_size': 6, 'palette_size': 16},
            '8bit_high': {'pixel_size': 5, 'palette_size': 16},
            '16bit_low': {'pixel_size': 3, 'palette_size': 128},
            '16bit_high': {'pixel_size': 2, 'palette_size': 128},
            '32bit': {'pixel_size': 2, 'palette_size': 256},
            '64bit': {'pixel_size': 1, 'palette_size': 256},
        }
        
        if preset_id not in bit_presets:
            return
        
        preset = bit_presets[preset_id]
        
        if hasattr(self, 'opt_pixel_size_spin') and self.opt_pixel_size_spin:
            self.opt_pixel_size_spin.set_value(preset['pixel_size'])
        
        if hasattr(self, 'opt_palette_size_spin') and self.opt_palette_size_spin:
            self.opt_palette_size_spin.set_value(preset['palette_size'])
        
        print(f"Aplicado preset de bits {preset_id}: pixel_size={preset['pixel_size']}, palette_size={preset['palette_size']}")


    # --- Funções de Seleção ---
    def on_select_file_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione um arquivo de mídia (Vídeo ou Imagem)", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_media = Gtk.FileFilter(); filter_media.set_name("Mídia (mp4, avi, mkv, mov, webm, gif, png, jpg, jpeg, bmp, webp)")
        for ext in ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.webm', '*.gif', '*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']: filter_media.add_pattern(ext)
        dialog.add_filter(filter_media)
        filter_video = Gtk.FileFilter(); filter_video.set_name("Apenas Vídeos (mp4, avi, mkv, mov, webm, gif)")
        for ext in ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.webm', '*.gif']: filter_video.add_pattern(ext)
        dialog.add_filter(filter_video)
        filter_image = Gtk.FileFilter(); filter_image.set_name("Apenas Imagens (png, jpg, jpeg, bmp, webp)")
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']: filter_image.add_pattern(ext)
        dialog.add_filter(filter_image)
        filter_any = Gtk.FileFilter(); filter_any.set_name("Todos (*.*)"); filter_any.add_pattern("*"); dialog.add_filter(filter_any)
        try:
            if os.path.isdir(self.input_dir): dialog.set_current_folder(self.input_dir)
        except Exception: pass
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_file_path = dialog.get_filename()
            self.selected_folder_path = None
            self.selected_path_label.set_text(f"Arquivo: {os.path.basename(self.selected_file_path)}")
            print(f"Arquivo selecionado: {self.selected_file_path}")
        dialog.destroy()
        self.update_button_states()


    def on_select_folder_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione uma pasta com vídeos", parent=self.window, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Selecionar", Gtk.ResponseType.OK)
        try:
            if os.path.isdir(self.input_dir): dialog.set_current_folder(self.input_dir)
        except Exception: pass
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_folder_path = dialog.get_filename()
            self.selected_file_path = None
            self.selected_path_label.set_text(f"Pasta: .../{os.path.basename(self.selected_folder_path)}")
            print(f"Pasta selecionada: {self.selected_folder_path}")
        dialog.destroy()
        self.update_button_states()

    def on_select_ascii_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione um arquivo ASCII (.txt)", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_text = Gtk.FileFilter(); filter_text.set_name("Arquivos de Texto"); filter_text.add_mime_type("text/plain"); filter_text.add_pattern("*.txt"); dialog.add_filter(filter_text)
        filter_any = Gtk.FileFilter(); filter_any.set_name("Todos"); filter_any.add_pattern("*"); dialog.add_filter(filter_any)
        
        try:
            if os.path.isdir(self.output_dir): dialog.set_current_folder(self.output_dir)
        except Exception: pass
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_ascii_path = dialog.get_filename()
            print(f"Arquivo ASCII selecionado: {self.selected_ascii_path}")
            # Opcional: Atualizar label ou mostrar popup? Por enquanto só habilita o botão
        dialog.destroy()
        self.update_button_states()

    def update_button_states(self):
         if not hasattr(self, 'convert_button') or not self.convert_button: return
         file_selected = self.selected_file_path is not None and os.path.exists(self.selected_file_path)
         folder_selected = self.selected_folder_path is not None and os.path.isdir(self.selected_folder_path)
         default_folder_exists = self.input_dir is not None and os.path.isdir(self.input_dir)
         self.convert_button.set_sensitive(file_selected)
         self.play_button.set_sensitive(file_selected)
         self.open_video_button.set_sensitive(file_selected)
         self.convert_all_button.set_sensitive(folder_selected or default_folder_exists)
         self.calibrate_button.set_sensitive(True)
         self.open_webcam_button.set_sensitive(True)
         self.play_ascii_button.set_sensitive(self.selected_ascii_path is not None and os.path.exists(self.selected_ascii_path))

    # --- Handlers de Ação ---
    def on_convert_button_clicked(self, widget):
        if self.selected_file_path:
            thread = threading.Thread(target=self.run_conversion, args=([self.selected_file_path],))
            thread.daemon = True
            thread.start()

    def on_convert_all_button_clicked(self, widget):
        target_folder = self.selected_folder_path if self.selected_folder_path else self.input_dir
        try:
             if not os.path.isdir(target_folder):
                 self.show_error_dialog("Erro", f"Pasta de entrada não encontrada:\n{target_folder}"); return
             videos = [f for f in os.listdir(target_folder) if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm'))]
             if not videos:
                 self.show_error_dialog("Aviso", f"Nenhum vídeo compatível encontrado em:\n{target_folder}"); return
             video_paths = [os.path.join(target_folder, v) for v in videos]
        except Exception as e:
             self.show_error_dialog("Erro ao Listar Vídeos", str(e)); return
        thread = threading.Thread(target=self.run_conversion, args=(video_paths,))
        thread.daemon = True
        thread.start()

    def _is_image_file(self, file_path):
        return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))

    def _is_video_file(self, file_path):
        return file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm'))

    def run_conversion(self, file_paths):
        python_executable = self._get_python_executable()

        if not self.conversion_lock.acquire(blocking=False):
            GLib.idle_add(self.on_conversion_update, "Outra conversão já está em andamento...")
            return

        total = len(file_paths); output_files = []
        GLib.idle_add(self.on_conversion_update, f"Iniciando conversão de {total} arquivo(s)...")

        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)
            output_filename = os.path.splitext(file_name)[0] + ".txt"
            output_filepath = os.path.join(self.output_dir, output_filename)
            GLib.idle_add(self.on_conversion_update, f"({i+1}/{total}): Convertendo {file_name}...")

            # Check conversion mode
            conversion_mode = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()
            
            if self._is_image_file(file_path):
                if conversion_mode == 'pixelart':
                    cmd = [python_executable, PIXEL_ART_IMAGE_CONVERTER_SCRIPT, "--image", file_path, "--config", self.config_path]
                    script_name = PIXEL_ART_IMAGE_CONVERTER_SCRIPT
                else:  # ASCII mode
                    cmd = [python_executable, IMAGE_CONVERTER_SCRIPT, "--image", file_path, "--config", self.config_path]
                    script_name = IMAGE_CONVERTER_SCRIPT
            else:  # Video file
                if conversion_mode == 'pixelart':
                    cmd = [python_executable, PIXEL_ART_CONVERTER_SCRIPT, "--video", file_path, "--config", self.config_path]
                    script_name = PIXEL_ART_CONVERTER_SCRIPT
                else:  # ASCII mode
                    cmd = [python_executable, CONVERTER_SCRIPT, "--video", file_path, "--config", self.config_path]
                    script_name = CONVERTER_SCRIPT

            try:
                print(f"Executando: {shlex.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                print(f"--- Saída ({file_name}) ---\n{result.stdout.strip()}")
                if result.stderr.strip(): print(f"--- Erros ({file_name}) ---\n{result.stderr.strip()}")
                print("-" * (len(file_name) + 24))
                GLib.idle_add(self.on_conversion_update, f"OK ({i+1}/{total}): {file_name} convertido.")
                output_files.append(output_filepath)
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout or 'Erro desconhecido'
                error_msg = f"ERRO ({i+1}/{total}) {file_name}:\n{error_output.strip()}"
                print(error_msg)
                GLib.idle_add(self.on_conversion_update, error_msg.split('\n')[0])
            except FileNotFoundError:
                 error_msg = f"ERRO: Script '{script_name}' ou Python '{python_executable}' não encontrado."
                 print(error_msg); GLib.idle_add(self.on_conversion_update, error_msg); break
            except Exception as e:
                error_msg = f"ERRO FATAL {file_name}: {e}"
                print(error_msg); GLib.idle_add(self.on_conversion_update, error_msg)

        final_message = f"Conversão em lote finalizada ({len(output_files)}/{total} sucesso)."
        GLib.idle_add(self.on_conversion_update, final_message)
        if output_files: GLib.idle_add(self.show_completion_popup, output_files)
        self.conversion_lock.release()

    def on_conversion_update(self, message):
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.set_text(message)
        return False

    def show_completion_popup(self, output_files):
         if not self.window or not self.window.is_visible(): return False
         dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text="Conversão Concluída")
         files_str = "\n".join([os.path.basename(f) for f in output_files])
         dialog.format_secondary_text(f"Arquivo(s) gerado(s) em:\n'{self.output_dir}':\n\n{files_str}")
         dialog.connect("response", lambda d, r: d.destroy())
         dialog.show_all()
         return False

    def on_play_button_clicked(self, widget):
        """Reproduz no modo selecionado no ComboBox"""
        mode_id = self.play_mode_combo.get_active_id()
        if mode_id:
            self._play_with_mode(mode_id)
        else:
            self._play_with_mode('terminal')
    
    def _play_with_mode(self, display_mode):
        """Helper method to play video with specified display mode"""
        if not self.selected_file_path:
            return
            
        media_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
        file_path = os.path.join(self.output_dir, media_name)
        if not os.path.exists(file_path):
            self.show_error_dialog("Erro", f"Arquivo ASCII '{os.path.basename(file_path)}' não encontrado.\nConverta o arquivo primeiro.")
            return

        # Create config with display_mode override
        temp_config = configparser.ConfigParser(interpolation=None)
        temp_config.read_dict(self.config)  # Copy current config
        
        # Set the display mode for this playback
        if not temp_config.has_section('Geral'):
            temp_config.add_section('Geral')
        temp_config.set('Geral', 'display_mode', display_mode)
        
        loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']
        
        # Always use subprocess mode to avoid GTK main loop conflicts
        print(f"Launching player ({display_mode}) in subprocess mode")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as tmp_config_file:
            temp_config.write(tmp_config_file)
            temp_config_path = tmp_config_file.name
        
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', temp_config_path]
        
        if loop_enabled:
            cmd_base.append('-l')
        
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', 
                   '--title=Êxtase em 4R73 - Player', '--class=extase-em-4r73', '--'] + cmd_base
            subprocess.Popen(cmd)
        except FileNotFoundError:
            try:
                cmd = ['xterm', '-fn', '6x10', '-maximized', '-title', 'Êxtase em 4R73 - Player', '-hold', '-e'] + cmd_base
                subprocess.Popen(cmd)
            except Exception as e:
                self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal:\n{e}")

    def on_play_ascii_button_clicked(self, widget):
        if self.selected_ascii_path and os.path.exists(self.selected_ascii_path):
            self._launch_player_in_terminal(self.selected_ascii_path)
        else:
            self.show_error_dialog("Erro", "Nenhum arquivo ASCII válido selecionado.")

    def _launch_player_in_terminal(self, file_path):
        """Lança o player.py em um terminal externo maximizado para o arquivo especificado."""
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', self.config_path]
        
        loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']
        if loop_enabled:
            cmd_base.append('-l')
        
        # Obtém zoom do player do config
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            # gnome-terminal com zoom reduzido
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', '--title=Êxtase em 4R73 - Player', '--class=extase-em-4r73', '--'] + cmd_base
            print(f"Executando player (ASCII) com zoom {player_zoom}: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            print("Aviso: gnome-terminal não encontrado. Tentando xterm...")
            try:
                # xterm com fonte pequena
                cmd = ['xterm', '-fn', '6x10', '-maximized', '-title', 'Êxtase em 4R73 - Player', '-hold', '-e'] + cmd_base
                print(f"Executando player (xterm com fonte pequena): {shlex.join(cmd)}")
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compatível encontrado.")
            except Exception as e_xterm:
                self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal:\n{e_xterm}")
        except Exception as e_gnome:
            self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal:\n{e_gnome}")

    def on_open_video_clicked(self, widget):
         if self.selected_file_path:
             if not os.path.exists(self.selected_file_path):
                 self.show_error_dialog("Erro", f"Vídeo '{os.path.basename(self.selected_file_path)}' não encontrado."); return
             self.open_path(self.selected_file_path)

    def on_open_folder_clicked(self, widget):
        if not os.path.isdir(self.output_dir):
            self.show_error_dialog("Aviso", f"Pasta de saída '{self.output_dir}' ainda não existe.")
            return
        self.open_path(self.output_dir)

    def open_path(self, path):
         try:
             abs_path = os.path.abspath(path)
             print(f"Tentando abrir: {abs_path}")
             if platform.system() == "Windows": os.startfile(abs_path)
             elif platform.system() == "Darwin": subprocess.Popen(["open", abs_path])
             else:
                 result = subprocess.run(["xdg-open", abs_path], check=False, capture_output=True, text=True)
                 if result.returncode != 0:
                      print(f"xdg-open falhou ({result.stderr.strip()}). Tentando gvfs-open...")
                      result_gvfs = subprocess.run(["gvfs-open", abs_path], check=False, capture_output=True, text=True)
                      if result_gvfs.returncode != 0:
                           raise OSError(f"xdg-open e gvfs-open falharam. Último erro: {result_gvfs.stderr.strip()}")
         except FileNotFoundError: self.show_error_dialog("Erro", f"Comando 'xdg-open'/'gvfs-open' não encontrado.")
         except Exception as e: self.show_error_dialog("Erro ao Abrir", f"Não foi possível abrir '{os.path.basename(path)}':\n{e}")

    def on_calibrate_button_clicked(self, widget):
        video_to_calibrate = self.selected_file_path
        cmd_args = []
        if video_to_calibrate and os.path.exists(video_to_calibrate):
            cmd_args = ["--video", video_to_calibrate]
            print(f"Calibrador usará o vídeo: {os.path.basename(video_to_calibrate)}")
        else:
            if video_to_calibrate: print(f"Aviso: Vídeo selecionado '{video_to_calibrate}' não encontrado.")
            print("Nenhum vídeo válido selecionado. Calibrador usará webcam (fonte 0).")
        
        self._launch_calibrator_in_terminal(cmd_args)

    def on_open_webcam_button_clicked(self, widget):
        """Abre a webcam otimizada em tempo real."""
        print("Abrindo Webcam Otimizada (Real-Time ASCII)...")
        self._launch_webcam_in_terminal()

    def _launch_webcam_in_terminal(self):
        """Lança o realtime_ascii.py (webcam otimizada) em um terminal externo maximizado."""
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, REALTIME_SCRIPT, "--config", self.config_path]
        
        # Obtém zoom do config para otimizar visualização
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', 
                   '--title=Êxtase em 4R73 - Webcam Real-Time', 
                   '--class=extase-em-4r73', '--'] + cmd_base
            print(f"Executando webcam otimizada com zoom {player_zoom}: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            print("Aviso: gnome-terminal não encontrado. Tentando xterm...")
            try:
                cmd = ['xterm', '-fn', '6x10', '-maximized', 
                       '-title', 'Êxtase em 4R73 - Webcam', '-e'] + cmd_base
                print(f"Executando webcam (xterm com fonte pequena): {shlex.join(cmd)}")
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compatível encontrado.")
            except Exception as e_xterm:
                self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal:\n{e_xterm}")
        except Exception as e_gnome:
            self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal:\n{e_gnome}")

    def _launch_calibrator_in_terminal(self, extra_args):
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, CALIBRATOR_SCRIPT, "--config", self.config_path] + extra_args
        
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize', '--title=Êxtase em 4R73 - Calibrador', '--class=extase-em-4r73', '--'] + cmd_base
            print(f"Executando calibrador com zoom {player_zoom}: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            print("Aviso: gnome-terminal não encontrado. Tentando xterm...")
            try:
                base_font_size = 12
                font_size = int(base_font_size * player_zoom)
                cmd = ['xterm', '-fa', f'Mono-{font_size}', '-maximized', '-title', 'Êxtase em 4R73 - Calibrador', '-e'] + cmd_base
                print(f"Executando calibrador (xterm) com fonte {font_size}: {shlex.join(cmd)}")
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compatível encontrado.")
            except Exception as e:
                 self.show_error_dialog("Erro Calibrador", f"Erro ao lançar xterm: {e}")
        except Exception as e:
             self.show_error_dialog("Erro Calibrador", f"Erro ao lançar gnome-terminal: {e}")

    def _read_pipe(self, pipe, output_stream):
        try:
            for line in iter(pipe.readline, ''): output_stream.write(line); output_stream.flush()
        except Exception: pass
        finally:
             if pipe:
                 try: pipe.close()
                 except Exception: pass

    def on_quit_button_clicked(self, widget):
        print("Botão Sair pressionado. Encerrando GTK...")
        Gtk.main_quit()

    def on_options_button_clicked(self, widget):
        """Abre a janela de opções e carrega os valores atuais."""
        # Carrega valores do config
        try:
            # Player
            loop_val_str = self.config.get('Player', 'loop', fallback='nao').lower()
            loop_val = loop_val_str in ['sim', 'yes', 'true', '1', 'on']
            self.opt_loop_check.set_active(loop_val)
            
            # Conversor
            width_val = self.config.getint('Conversor', 'target_width', fallback=120)
            height_val = self.config.getint('Conversor', 'target_height', fallback=0)
            sobel_val = self.config.getint('Conversor', 'sobel_threshold', fallback=100)
            aspect_val = self.config.getfloat('Conversor', 'char_aspect_ratio', fallback=0.95)
            
            self.opt_width_spin.set_value(width_val)
            self.opt_height_spin.set_value(height_val)
            self.opt_sobel_spin.set_value(sobel_val)
            self.opt_aspect_spin.set_value(aspect_val)
            
            # Luminance Ramp
            default_ramp = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
            luminance_val = self.config.get('Conversor', 'luminance_ramp', fallback=default_ramp)
            self.opt_luminance_entry.set_text(luminance_val)

            # Chroma Key
            h_min = self.config.getint('ChromaKey', 'h_min', fallback=35)
            h_max = self.config.getint('ChromaKey', 'h_max', fallback=85)
            s_min = self.config.getint('ChromaKey', 's_min', fallback=40)
            s_max = self.config.getint('ChromaKey', 's_max', fallback=255)
            v_min = self.config.getint('ChromaKey', 'v_min', fallback=40)
            v_max = self.config.getint('ChromaKey', 'v_max', fallback=255)

            self.opt_h_min_spin.set_value(h_min)
            self.opt_h_max_spin.set_value(h_max)
            self.opt_s_min_spin.set_value(s_min)
            self.opt_s_max_spin.set_value(s_max)
            self.opt_v_min_spin.set_value(v_min)
            self.opt_v_max_spin.set_value(v_max)

            erode = self.config.getint('ChromaKey', 'erode', fallback=2)
            dilate = self.config.getint('ChromaKey', 'dilate', fallback=2)
            self.opt_erode_spin.set_value(erode)
            self.opt_dilate_spin.set_value(dilate)

            # Mode and Pixel Art settings
            mode_val = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()
            pixel_size_val = self.config.getint('PixelArt', 'pixel_size', fallback=2)
            palette_size_val = self.config.getint('PixelArt', 'color_palette_size', fallback=16)
            fixed_palette_val = self.config.getboolean('PixelArt', 'use_fixed_palette', fallback=False)
            
            # Create mode widgets if they don't exist yet
            if not hasattr(self, '_mode_widgets_created') or not self._mode_widgets_created:
                self._create_mode_widgets()
            
            # Set mode radio buttons (only if widgets were created successfully)
            if hasattr(self, 'opt_mode_pixelart_radio') and self.opt_mode_pixelart_radio:
                if mode_val == 'pixelart':
                    self.opt_mode_pixelart_radio.set_active(True)
                else:
                    self.opt_mode_ascii_radio.set_active(True)
                
                # Set pixel art values
                if self.opt_pixel_size_spin:
                    self.opt_pixel_size_spin.set_value(pixel_size_val)
                if self.opt_palette_size_spin:
                    self.opt_palette_size_spin.set_value(palette_size_val)
                if self.opt_fixed_palette_check:
                    self.opt_fixed_palette_check.set_active(fixed_palette_val)
            
        except Exception as e:
            print(f"Erro ao carregar opções: {e}")
            
        self.options_dialog.show_all()

    def on_options_cancel_clicked(self, widget):
        self.options_dialog.hide()

    def on_options_restore_clicked(self, widget):
        """Restaura os valores padrão nos widgets (não salva automaticamente)."""
        # Player
        self.opt_loop_check.set_active(False) # Default loop = nao
        
        # Conversor
        self.opt_width_spin.set_value(120)
        self.opt_height_spin.set_value(0)  # 0 = auto
        self.opt_sobel_spin.set_value(100)
        self.opt_aspect_spin.set_value(0.95) # Ajustado conforme pedido do usuário (era 0.45 no código antigo, mas user pediu 0.95)
        
        default_ramp = "$@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        self.opt_luminance_entry.set_text(default_ramp)

        # Chroma Key (Valores padrão do user request)
        self.opt_h_min_spin.set_value(35)
        self.opt_h_max_spin.set_value(85)
        self.opt_s_min_spin.set_value(40)
        self.opt_s_max_spin.set_value(255)
        self.opt_v_min_spin.set_value(40)
        self.opt_v_max_spin.set_value(255)
        self.opt_erode_spin.set_value(2)
        self.opt_dilate_spin.set_value(2)

        print("Valores padrão restaurados na interface (clique em OK para salvar).")

    def on_options_save_clicked(self, widget):
        # Salva valores
        try:
            # Player
            if 'Player' not in self.config: self.config.add_section('Player')
            self.config.set('Player', 'loop', 'sim' if self.opt_loop_check.get_active() else 'nao')
            
            # Conversor
            if 'Conversor' not in self.config: self.config.add_section('Conversor')
            self.config.set('Conversor', 'target_width', str(int(self.opt_width_spin.get_value())))
            self.config.set('Conversor', 'target_height', str(int(self.opt_height_spin.get_value())))
            self.config.set('Conversor', 'sobel_threshold', str(int(self.opt_sobel_spin.get_value())))
            self.config.set('Conversor', 'char_aspect_ratio', str(self.opt_aspect_spin.get_value()))
            self.config.set('Conversor', 'luminance_ramp', self.opt_luminance_entry.get_text())

            # Chroma Key
            if 'ChromaKey' not in self.config: self.config.add_section('ChromaKey')
            self.config.set('ChromaKey', 'h_min', str(int(self.opt_h_min_spin.get_value())))
            self.config.set('ChromaKey', 'h_max', str(int(self.opt_h_max_spin.get_value())))
            self.config.set('ChromaKey', 's_min', str(int(self.opt_s_min_spin.get_value())))
            self.config.set('ChromaKey', 's_max', str(int(self.opt_s_max_spin.get_value())))
            self.config.set('ChromaKey', 'v_min', str(int(self.opt_v_min_spin.get_value())))
            self.config.set('ChromaKey', 'v_max', str(int(self.opt_v_max_spin.get_value())))
            self.config.set('ChromaKey', 'erode', str(int(self.opt_erode_spin.get_value())))
            self.config.set('ChromaKey', 'dilate', str(int(self.opt_dilate_spin.get_value())))

            # Mode and Pixel Art
            if hasattr(self, 'opt_mode_pixelart_radio') and self.opt_mode_pixelart_radio:
                if 'Mode' not in self.config: self.config.add_section('Mode')
                mode_val = 'pixelart' if self.opt_mode_pixelart_radio.get_active() else 'ascii'
                self.config.set('Mode', 'conversion_mode', mode_val)
                
                if 'PixelArt' not in self.config: self.config.add_section('PixelArt')
                self.config.set('PixelArt', 'pixel_size', str(int(self.opt_pixel_size_spin.get_value())))
                self.config.set('PixelArt', 'color_palette_size', str(int(self.opt_palette_size_spin.get_value())))
                self.config.set('PixelArt', 'use_fixed_palette', 'true' if self.opt_fixed_palette_check.get_active() else 'false')

            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print("Configurações salvas com sucesso.")
            
        except Exception as e:
            self.show_error_dialog("Erro ao Salvar", f"Não foi possível salvar as configurações:\n{e}")
        
        self.options_dialog.hide()

    def on_test_converter_clicked(self, widget):
        """Abre preview das configurações do conversor em tempo real."""
        # Primeiro salva as configurações atuais temporariamente
        try:
            if 'Conversor' not in self.config: self.config.add_section('Conversor')
            self.config.set('Conversor', 'target_width', str(int(self.opt_width_spin.get_value())))
            self.config.set('Conversor', 'target_height', str(int(self.opt_height_spin.get_value())))
            self.config.set('Conversor', 'sobel_threshold', str(int(self.opt_sobel_spin.get_value())))
            self.config.set('Conversor', 'char_aspect_ratio', str(self.opt_aspect_spin.get_value()))
            self.config.set('Conversor', 'luminance_ramp', self.opt_luminance_entry.get_text())
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print("Configurações salvas temporariamente para preview.")
        except Exception as e:
            print(f"Erro ao salvar configurações para teste: {e}")
        
        # Lança o calibrador com o vídeo selecionado (ou webcam se nenhum)
        video_to_test = self.selected_file_path
        cmd_args = []
        if video_to_test and os.path.exists(video_to_test) and self._is_video_file(video_to_test):
            cmd_args = ["--video", video_to_test]
            print(f"Preview usará o vídeo: {os.path.basename(video_to_test)}")
        else:
            print("Nenhum vídeo válido selecionado. Preview usará webcam.")
        
        self._launch_calibrator_in_terminal(cmd_args)

    def on_test_chroma_clicked(self, widget):
        """Abre preview das configurações de chroma key em tempo real."""
        try:
            if 'ChromaKey' not in self.config: self.config.add_section('ChromaKey')
            self.config.set('ChromaKey', 'h_min', str(int(self.opt_h_min_spin.get_value())))
            self.config.set('ChromaKey', 'h_max', str(int(self.opt_h_max_spin.get_value())))
            self.config.set('ChromaKey', 's_min', str(int(self.opt_s_min_spin.get_value())))
            self.config.set('ChromaKey', 's_max', str(int(self.opt_s_max_spin.get_value())))
            self.config.set('ChromaKey', 'v_min', str(int(self.opt_v_min_spin.get_value())))
            self.config.set('ChromaKey', 'v_max', str(int(self.opt_v_max_spin.get_value())))
            self.config.set('ChromaKey', 'erode', str(int(self.opt_erode_spin.get_value())))
            self.config.set('ChromaKey', 'dilate', str(int(self.opt_dilate_spin.get_value())))

            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print("Configurações de Chroma Key salvas temporariamente para preview.")
        except Exception as e:
            print(f"Erro ao salvar configurações de chroma para teste: {e}")
        
        # Lança o calibrador com o vídeo selecionado (ou webcam se nenhum)
        video_to_test = self.selected_file_path
        cmd_args = []
        if video_to_test and os.path.exists(video_to_test) and self._is_video_file(video_to_test):
            cmd_args = ["--video", video_to_test]
            print(f"Preview Chroma usará o vídeo: {os.path.basename(video_to_test)}")
        else:
            print("Nenhum vídeo válido selecionado. Preview Chroma usará webcam.")
        
        self._launch_calibrator_in_terminal(cmd_args)

    def show_error_dialog(self, title, text):
        # Garante execução na thread principal do GTK
        GLib.idle_add(self._do_show_error_dialog, title, str(text))

    def _do_show_error_dialog(self, title, text):
        if not hasattr(self, 'window') or not self.window or not self.window.is_visible():
             print(f"AVISO: Janela principal não visível/inicializada. Erro '{title}' não mostrado em diálogo.")
             return False
        dialog = Gtk.MessageDialog(transient_for=self.window, flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text=title)
        max_len = 600 # Aumentado um pouco
        secondary_text = str(text)
        secondary_text = (secondary_text[:max_len] + '...') if len(secondary_text) > max_len else secondary_text
        dialog.format_secondary_text(secondary_text)
        dialog.connect("response", lambda d, response_id: d.destroy())
        dialog.show_all()
        return False

# --- Função Principal de Execução ---
def run_app():
    GLib.set_prgname("extase-em-4r73")
    GLib.set_application_name("Êxtase em 4R73")

    # Verifica dependências GTK antes de instanciar App
    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk # Tenta importar Gtk para confirmar
    except Exception as e:
        print(f"Erro Crítico: GTK 3.0 (`gi`) não encontrado ou configuração incorreta. {e}", file=sys.stderr)
        print("Verifique a instalação: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0", file=sys.stderr)
        sys.exit(1)

    app = None
    try:
        logger.info("Instanciando a classe App...")
        app = App()
        if hasattr(app, 'initialization_failed') and app.initialization_failed:
             print("Inicialização da App falhou (detalhes acima). Encerrando sem Gtk.main().")
             sys.exit(1) # Sai se __init__ marcou falha
        logger.info("Instanciação da App concluída.")

    except Exception as e:
         print(f"Erro Crítico durante instanciação da App: {e}")
         traceback.print_exc(file=sys.stderr) # Imprime traceback completo
         # Tenta mostrar diálogo de erro final
         try:
             error_dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text="Erro Crítico na Inicialização")
             error_dialog.format_secondary_text(f"Não foi possível instanciar a aplicação:\n{e}")
             error_dialog.connect("response", lambda d, r: Gtk.main_quit()) # Usa main_quit
             error_dialog.run()
             error_dialog.destroy()
         except Exception as gtk_err: print(f"Não foi possível mostrar diálogo de erro GTK: {gtk_err}")
         sys.exit(1)


    # Verifica se app e app.window foram criados com sucesso
    if app and hasattr(app, 'window') and app.window:
        try:
            logger.info("Iniciando loop principal GTK (Gtk.main())...")
            Gtk.main()
            logger.info("Loop principal GTK finalizado.")
        except KeyboardInterrupt:
            print("\nEncerrando via Ctrl+C (KeyboardInterrupt).")
            Gtk.main_quit()
        except Exception as e:
             print(f"Erro Inesperado no loop principal GTK: {e}")
             traceback.print_exc(file=sys.stderr)
             Gtk.main_quit() # Tenta sair
    else:
        if not (hasattr(app, 'initialization_failed') and app.initialization_failed):
             print("Falha ao inicializar a aplicação (App ou Window inválidos). Encerrando.")
        # Se initialization_failed=True, a mensagem de erro já foi dada no __init__
        sys.exit(1) # Garante a saída

if __name__ == "__main__":
     # Garante que o diretório de trabalho seja o do script raiz (main.py)
     # Isso ajuda a resolver caminhos relativos como 'src/...' ou 'config.ini'
     # Nota: O lançador .desktop já define o 'Path', mas isso é uma segurança extra.
     # script_dir = os.path.dirname(os.path.abspath(__file__)) # __file__ aqui é main.py
     # os.chdir(script_dir)
     # print(f"Diretório de trabalho definido para: {os.getcwd()}") # Log para debug
     run_app()
