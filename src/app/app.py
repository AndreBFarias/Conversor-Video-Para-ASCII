import os
import sys
import configparser
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gdk

from .constants import UI_FILE, LOGO_FILE, CONFIG_PATH, ROOT_DIR
from .actions.file_actions import FileActionsMixin
from .actions.conversion_actions import ConversionActionsMixin
from .actions.playback_actions import PlaybackActionsMixin
from .actions.calibration_actions import CalibrationActionsMixin
from .actions.options_actions import OptionsActionsMixin


class App(
    FileActionsMixin,
    ConversionActionsMixin,
    PlaybackActionsMixin,
    CalibrationActionsMixin,
    OptionsActionsMixin
):
    def __init__(self, logger):
        self.logger = logger
        self.initialization_failed = False
        self.builder = Gtk.Builder()

        try:
            if not os.path.exists(UI_FILE):
                ui_rel_path = os.path.relpath(UI_FILE, ROOT_DIR)
                raise FileNotFoundError(f"Arquivo UI '{ui_rel_path}' nao encontrado.")
            self.builder.add_from_file(UI_FILE)
        except (GLib.Error, FileNotFoundError) as e:
            self._show_init_error("Erro Critico UI", f"Nao foi possivel carregar a interface:\n{e}")
            self.initialization_failed = True
            return

        self.window = self.builder.get_object("main_window")
        if not self.window:
            self._show_init_error("Erro Critico UI", "Objeto 'main_window' nao encontrado em main.glade.")
            self.initialization_failed = True
            return

        self.window.set_title("Extase em 4R73")
        self.window.set_wmclass("extase-em-4r73", "Extase em 4R73")
        self.window.connect("destroy", Gtk.main_quit)
        self._apply_custom_css()
        self._setup_logo_and_title()

        self.builder.connect_signals(self)
        self.config = configparser.ConfigParser(interpolation=None)
        self.config_path = CONFIG_PATH

        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Arquivo config.ini nao encontrado em '{self.config_path}'")
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config.read_file(f)
            if not self.config.sections():
                raise configparser.NoSectionError("Nenhuma secao lida (arquivo vazio?)")

            self.input_dir = self.config.get('Pastas', 'input_dir', fallback='videos_entrada')
            self.output_dir = self.config.get('Pastas', 'output_dir', fallback='videos_saida')
            self.input_dir = os.path.abspath(os.path.join(ROOT_DIR, self.input_dir))
            self.output_dir = os.path.abspath(os.path.join(ROOT_DIR, self.output_dir))
            os.makedirs(self.input_dir, exist_ok=True)
            os.makedirs(self.output_dir, exist_ok=True)
        except (FileNotFoundError, configparser.Error) as e:
            self._show_init_error("Erro Critico de Configuracao", f"Nao foi possivel ler config.ini:\n{e}")
            self.initialization_failed = True
            return

        if not self._get_widgets():
            self.initialization_failed = True
            return

        self.selected_file_path = None
        self.selected_folder_path = None
        self.selected_ascii_path = None
        self.conversion_lock = threading.Lock()
        self._mode_widgets_created = False

        self._create_quality_preset_combo()
        self.update_button_states()
        self.window.show_all()

    def _apply_custom_css(self):
        css = b"""
        progressbar {
            min-height: 28px;
        }
        progressbar trough {
            min-height: 28px;
        }
        progressbar progress {
            min-height: 28px;
        }
        #config_button_large {
            background: none;
            border: none;
            box-shadow: none;
            margin-bottom: 12px;
        }
        #config_button_large:hover {
            background: alpha(@theme_fg_color, 0.1);
        }
        #convert_button, #convert_all_button {
            border: 2px solid #81c995;
            color: #81c995;
        }
        #convert_button:disabled, #convert_all_button:disabled {
            border: 2px solid #81c995;
            color: #81c995;
            opacity: 0.6;
        }
        #convert_button:hover, #convert_all_button:hover {
            background: alpha(#81c995, 0.2);
        }
        .file-selected {
            color: #81c995;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _setup_logo_and_title(self):
        try:
            logo_widget = self.builder.get_object("logo_image")
            title_widget = self.builder.get_object("title_label")
            if logo_widget and title_widget:
                if os.path.exists(LOGO_FILE):
                    pixbuf_logo = GdkPixbuf.Pixbuf.new_from_file_at_size(LOGO_FILE, 77, 77)
                    logo_widget.set_from_pixbuf(pixbuf_logo)
                    pixbuf_icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_FILE)
                    self.window.set_icon(pixbuf_icon)
                title_widget.set_markup(
                    "<span font_desc='Sans Bold 24' foreground='#EAEAEA'>"
                    "Êxtase em <span foreground='#81c995'>4R73</span></span>"
                )
        except Exception as e:
            self.logger.warning(f"Erro ao carregar assets: {e}")

    def _get_widgets(self) -> bool:
        try:
            self.status_label = None
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
            self.options_button = self.builder.get_object("config_button_large")

            self.options_dialog = self.builder.get_object("options_dialog")
            self.options_notebook = self.builder.get_object("options_notebook")
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

            self.conversion_progress = self.builder.get_object("conversion_progress")

            self.opt_mode_ascii_radio = None
            self.opt_mode_pixelart_radio = None
            self.opt_pixel_size_spin = None
            self.opt_palette_size_spin = None
            self.opt_fixed_palette_check = None

            self.opt_clear_screen_check = self.builder.get_object("opt_clear_screen_check")
            self.opt_show_fps_check = self.builder.get_object("opt_show_fps_check")
            self.opt_speed_combo = self.builder.get_object("opt_speed_combo")

            self.pref_input_folder = self.builder.get_object("pref_input_folder")
            self.pref_output_folder = self.builder.get_object("pref_output_folder")
            self.pref_engine_combo = self.builder.get_object("pref_engine_combo")
            self.pref_quality_combo = self.builder.get_object("pref_quality_combo")
            self.pref_format_combo = self.builder.get_object("pref_format_combo")

            self.opt_luminance_preset_combo = self.builder.get_object("opt_luminance_preset_combo")

            required_widgets = [
                self.selected_path_label, self.convert_button,
                self.convert_all_button, self.play_mode_combo, self.play_button,
                self.open_video_button, self.open_folder_button, self.calibrate_button,
                self.open_webcam_button, self.select_ascii_button, self.play_ascii_button,
                self.options_button, self.options_dialog, self.options_notebook,
                self.opt_loop_check, self.opt_width_spin
            ]
            if None in required_widgets:
                raise TypeError("Um ou mais widgets essenciais nao foram encontrados no .glade")
            return True

        except Exception as e:
            self._show_init_error("Erro Critico de UI", f"Falha ao obter componentes:\n{e}")
            return False

    def _get_python_executable(self) -> str:
        venv_python = os.path.join(ROOT_DIR, "venv", "bin", "python3")
        if os.path.exists(venv_python):
            return venv_python
        self.logger.warning("Executavel Python do venv nao encontrado, usando sys.executable.")
        return sys.executable

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.logger.info("Configuracoes salvas com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao salvar config: {e}")

    def _show_init_error(self, title: str, text: str):
        self.logger.error(f"Erro de Inicializacao: {title} - {text}")
        try:
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=title
            )
            dialog.format_secondary_text(str(text))
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.run()
        except Exception as e:
            self.logger.error(f"Falha ao mostrar dialogo de erro: {e}")
        self.initialization_failed = True

    def show_error_dialog(self, title: str, text: str):
        GLib.idle_add(self._do_show_error_dialog, title, str(text))

    def _do_show_error_dialog(self, title: str, text: str):
        if not hasattr(self, 'window') or not self.window or not self.window.is_visible():
            self.logger.warning(f"Janela nao visivel. Erro '{title}' nao mostrado.")
            return False
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title
        )
        max_len = 600
        secondary_text = (text[:max_len] + '...') if len(text) > max_len else text
        dialog.format_secondary_text(secondary_text)
        dialog.connect("response", lambda d, response_id: d.destroy())
        dialog.show_all()
        return False

    def on_quit_button_clicked(self, widget):
        self.logger.info("Botao Sair pressionado. Encerrando GTK...")
        Gtk.main_quit()
