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

# Definição de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(BASE_DIR, "ui", "main.glade")
LOGO_FILE = os.path.join(BASE_DIR, "assets", "logo.png")
ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")

# Caminhos para scripts
PYTHON_EXEC = sys.executable
PLAYER_SCRIPT = os.path.join(ROOT_DIR, "main_cli.py")
CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "converter.py")
CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "calibrator.py")
REALTIME_SCRIPT = os.path.join(BASE_DIR, "core", "realtime_ascii.py")


class App:
    def __init__(self):
        self.builder = Gtk.Builder(); # ... (resto do __init__ igual)
        try: self.builder.add_from_file(UI_FILE)
        except GLib.Error as e: print(f"Erro UI: {e}"); Gtk.main_quit(); return
        self.window = self.builder.get_object("main_window"); self.window.connect("destroy", Gtk.main_quit)
        try:
            logo_path_abs = os.path.abspath(LOGO_FILE)
            if os.path.exists(logo_path_abs): self.window.set_icon(GdkPixbuf.Pixbuf.new_from_file(logo_path_abs))
            else: print(f"Aviso Ícone: '{logo_path_abs}' não encontrado.")
        except Exception as e: print(f"Erro Ícone: {e}")
        self.builder.connect_signals(self)
        self.config = configparser.ConfigParser(); self.config_path = CONFIG_PATH
        try:
            if not self.config.read(self.config_path): raise FileNotFoundError(f"config.ini não encontrado: '{self.config_path}'.")
            self.input_dir = os.path.abspath(self.config.get('Pastas', 'input_dir', fallback='videos_entrada'))
            self.output_dir = os.path.abspath(self.config.get('Pastas', 'output_dir', fallback='videos_saida'))
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e: print(f"Erro Config: {e}"); self.show_error_dialog("Erro Configuração", str(e)); Gtk.main_quit(); return
        self.status_label = self.builder.get_object("status_label"); self.selected_path_label = self.builder.get_object("selected_path_label")
        self.convert_button = self.builder.get_object("convert_button"); self.convert_all_button = self.builder.get_object("convert_all_button")
        self.play_button = self.builder.get_object("play_button"); self.open_video_button = self.builder.get_object("open_video_button")
        self.calibrate_button = self.builder.get_object("calibrate_button"); self.selected_file_path = None; self.selected_folder_path = None
        self.conversion_lock = threading.Lock(); self.update_button_states(); self.window.show_all()

    # --- Funções de Seleção ---
    def on_select_file_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione um arquivo", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_video = Gtk.FileFilter(); filter_video.set_name("Vídeos"); filter_video.add_mime_type("video/*"); filter_video.add_pattern("*.mp4"); filter_video.add_pattern("*.avi"); filter_video.add_pattern("*.mkv"); filter_video.add_pattern("*.mov"); dialog.add_filter(filter_video)
        filter_any = Gtk.FileFilter(); filter_any.set_name("Todos"); filter_any.add_pattern("*"); dialog.add_filter(filter_any)
        if os.path.isdir(self.input_dir): dialog.set_current_folder(self.input_dir)
        response = dialog.run()
        if response == Gtk.ResponseType.OK: self.selected_file_path = dialog.get_filename(); self.selected_folder_path = None; self.selected_path_label.set_text(f"Arquivo: {os.path.basename(self.selected_file_path)}"); print(f"Arquivo: {self.selected_file_path}")
        dialog.destroy(); self.update_button_states()

    def on_select_folder_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione uma pasta", parent=self.window, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Selecionar", Gtk.ResponseType.OK)
        if os.path.isdir(self.input_dir): dialog.set_current_folder(self.input_dir)
        response = dialog.run()
        if response == Gtk.ResponseType.OK: self.selected_folder_path = dialog.get_filename(); self.selected_file_path = None; self.selected_path_label.set_text(f"Pasta: .../{os.path.basename(self.selected_folder_path)}"); print(f"Pasta: {self.selected_folder_path}")
        dialog.destroy(); self.update_button_states()

    def update_button_states(self):
         file_selected = self.selected_file_path is not None and os.path.exists(self.selected_file_path); folder_selected = self.selected_folder_path is not None and os.path.isdir(self.selected_folder_path)
         default_folder_exists = os.path.isdir(self.input_dir); self.convert_button.set_sensitive(file_selected); self.play_button.set_sensitive(file_selected)
         self.open_video_button.set_sensitive(file_selected); can_convert_all = folder_selected or default_folder_exists; self.convert_all_button.set_sensitive(can_convert_all); self.calibrate_button.set_sensitive(True)

    # --- Handlers de Ação ---
    def on_convert_button_clicked(self, widget):
        if self.selected_file_path: thread = threading.Thread(target=self.run_conversion, args=([self.selected_file_path],)); thread.daemon = True; thread.start()
    def on_convert_all_button_clicked(self, widget):
        target_folder = self.selected_folder_path if self.selected_folder_path else self.input_dir
        try:
             if not os.path.isdir(target_folder): self.show_error_dialog("Erro", f"Pasta não encontrada:\n{target_folder}"); return
             videos = [f for f in os.listdir(target_folder) if f.endswith(('.mp4', '.avi', '.mkv', '.mov'))]
             if not videos: self.show_error_dialog("Aviso", f"Nenhum vídeo em:\n{target_folder}"); return
             video_paths = [os.path.join(target_folder, v) for v in videos]
        except Exception as e: self.show_error_dialog("Erro Lista", str(e)); return
        thread = threading.Thread(target=self.run_conversion, args=(video_paths,)); thread.daemon = True; thread.start()

    def run_conversion(self, video_paths):
        if not self.conversion_lock.acquire(blocking=False): GLib.idle_add(self.on_conversion_update, "Conversão em andamento..."); return
        total = len(video_paths); output_files = []; GLib.idle_add(self.on_conversion_update, f"Iniciando {total} vídeo(s)...")
        for i, video_path in enumerate(video_paths):
            video_name = os.path.basename(video_path); output_filename = os.path.splitext(video_name)[0] + ".txt"; output_filepath = os.path.join(self.output_dir, output_filename)
            GLib.idle_add(self.on_conversion_update, f"({i+1}/{total}): {video_name}...")
            cmd = [PYTHON_EXEC, CONVERTER_SCRIPT, "--video", video_path, "--config", self.config_path]
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
                print(result.stdout); GLib.idle_add(self.on_conversion_update, f"OK ({i+1}/{total}): {video_name}"); output_files.append(output_filepath)
            except subprocess.CalledProcessError as e:
                # #1. (CORRIGIDO) Lógica para obter a mensagem de erro
                error_output = e.stderr or e.stdout or 'Erro desconhecido no subprocesso'
                error_msg = f"ERRO ({i+1}/{total}) {video_name}: {error_output.strip()}"
                print(error_msg); GLib.idle_add(self.on_conversion_update, error_msg.split('\n')[0])
            except Exception as e:
                error_msg = f"ERRO FATAL {video_name}: {e}"; print(error_msg); GLib.idle_add(self.on_conversion_update, error_msg)
        final_message = f"Lote finalizado ({len(output_files)}/{total} sucesso)."; GLib.idle_add(self.on_conversion_update, final_message)
        if output_files: GLib.idle_add(self.show_completion_popup, output_files)
        self.conversion_lock.release()

    def on_conversion_update(self, message): self.status_label.set_text(message); return False
    def show_completion_popup(self, output_files):
         dialog = Gtk.MessageDialog(transient_for=self.window, flags=0, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text="Conversão Concluída")
         files_str = "\n".join([os.path.basename(f) for f in output_files]); dialog.format_secondary_text(f"Gerado(s) em:\n'{self.output_dir}':\n\n{files_str}"); dialog.run(); dialog.destroy(); return False
    def on_play_button_clicked(self, widget):
        if self.selected_file_path:
            video_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"; file_path = os.path.join(self.output_dir, video_name)
            if not os.path.exists(file_path): self.show_error_dialog("Erro", f"'{os.path.basename(file_path)}' não encontrado.\nConverta primeiro."); return
            cmd = ['gnome-terminal', '--', PYTHON_EXEC, PLAYER_SCRIPT, '-f', file_path]
            try: subprocess.Popen(cmd)
            except FileNotFoundError: print("ERRO: gnome-terminal não encontrado..."); try: cmd = ['xterm', '-e', PYTHON_EXEC, PLAYER_SCRIPT, '-f', file_path]; subprocess.Popen(cmd)
            except FileNotFoundError: print("ERRO: xterm não encontrado."); self.show_error_dialog("Erro", "Nenhum terminal (gnome-terminal/xterm) encontrado.")
            except Exception as e: print(f"Erro terminal: {e}"); self.show_error_dialog("Erro", f"Não foi possível abrir terminal:\n{e}")
    def on_open_video_clicked(self, widget):
         if self.selected_file_path:
             if not os.path.exists(self.selected_file_path): self.show_error_dialog("Erro", f"Vídeo '{os.path.basename(self.selected_file_path)}' não encontrado."); return
             self.open_path(self.selected_file_path)
    def on_open_folder_clicked(self, widget): self.open_path(self.output_dir)
    def open_path(self, path):
         try:
             if platform.system() == "Windows": os.startfile(path)
             elif platform.system() == "Darwin": subprocess.Popen(["open", path])
             else: subprocess.Popen(["xdg-open", path])
         except FileNotFoundError: self.show_error_dialog("Erro", f"Comando 'xdg-open' (ou eq.) não encontrado.")
         except Exception as e: self.show_error_dialog("Erro Abrir", f"Não foi possível abrir '{os.path.basename(path)}':\n{e}")

    def on_calibrate_button_clicked(self, widget):
        video_to_calibrate = self.selected_file_path
        cmd_list = [PYTHON_EXEC, CALIBRATOR_SCRIPT, "--config", self.config_path]
        if video_to_calibrate and os.path.exists(video_to_calibrate):
            cmd_list.extend(["--video", video_to_calibrate])
        cmd_str = shlex.join(cmd_list)
        try:
            print(f"Executando calibrador (shell): {cmd_str}")
            process = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout_thread = threading.Thread(target=self._read_pipe, args=(process.stdout, sys.stdout)); stderr_thread = threading.Thread(target=self._read_pipe, args=(process.stderr, sys.stderr))
            stdout_thread.daemon = True; stderr_thread.daemon = True; stdout_thread.start(); stderr_thread.start()
        except Exception as e: error_msg = f"Erro ao lançar calibrador: {e}"; print(error_msg); self.show_error_dialog("Erro Calibrador", error_msg)

    def on_realtime_button_clicked(self, widget):
        cmd = [PYTHON_EXEC, REALTIME_SCRIPT, "--config", self.config_path]
        term_cmd_prefix = ['gnome-terminal', '--']
        try:
             full_cmd = term_cmd_prefix + cmd; print(f"Executando Realtime: {' '.join(full_cmd)}"); subprocess.Popen(full_cmd)
        except FileNotFoundError: print("ERRO: gnome-terminal não encontrado..."); try: term_cmd_prefix = ['xterm', '-e']; full_cmd = term_cmd_prefix + cmd; print(f"Executando Realtime (xterm): {' '.join(full_cmd)}"); subprocess.Popen(full_cmd)
        except FileNotFoundError: print("ERRO: xterm não encontrado."); self.show_error_dialog("Erro", "Nenhum terminal (gnome-terminal/xterm) encontrado.")
        except Exception as e: print(f"Erro terminal Realtime: {e}"); self.show_error_dialog("Erro", f"Não foi possível abrir terminal:\n{e}")

    def _read_pipe(self, pipe, output_stream):
        try:
            for line in iter(pipe.readline, ''): output_stream.write(line); output_stream.flush()
        finally:
             if pipe: pipe.close()

    def on_quit_button_clicked(self, widget): Gtk.main_quit()
    def show_error_dialog(self, title, text):
        dialog = Gtk.MessageDialog(transient_for=self.window, flags=0, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CANCEL, text=title);
        max_len = 500; secondary_text = (text[:max_len] + '...') if len(text) > max_len else text; dialog.format_secondary_text(secondary_text); dialog.run(); dialog.destroy()

def run_app():
    try: gi.require_version('Gtk', '3.0')
    except ValueError as e: print("Erro Crítico: GTK 3.0 não encontrado.", file=sys.stderr); sys.exit(1)
    app = App(); Gtk.main()

if __name__ == "__main__": run_app()
