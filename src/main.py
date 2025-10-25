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

    UI_FILE = os.path.join(BASE_DIR, "ui", "main.glade")
    LOGO_FILE = os.path.join(BASE_DIR, "assets", "logo.png")
    CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")

    # Caminhos para scripts (usando ROOT_DIR e BASE_DIR)
    # Usa sys.executable para garantir que o Python correto seja usado (do venv se ativo)
    PYTHON_EXEC = sys.executable
    PLAYER_SCRIPT = os.path.join(ROOT_DIR, "main_cli.py")
    CONVERTER_SCRIPT = os.path.join(BASE_DIR, "core", "converter.py")
    CALIBRATOR_SCRIPT = os.path.join(BASE_DIR, "core", "calibrator.py")

except Exception as e:
    print(f"Erro Crítico ao definir caminhos iniciais: {e}")
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
            self.play_button = self.builder.get_object("play_button")
            self.open_video_button = self.builder.get_object("open_video_button")
            self.open_folder_button = self.builder.get_object("open_folder_button")
            self.calibrate_button = self.builder.get_object("calibrate_button")
            if None in [self.status_label, self.selected_path_label, self.convert_button,
                         self.convert_all_button, self.play_button, self.open_video_button,
                         self.open_folder_button, self.calibrate_button]:
                raise TypeError("Um ou mais widgets essenciais não foram encontrados no arquivo .glade.")
        except Exception as e:
             self._show_init_error("Erro Crítico de UI", f"Falha ao obter componentes da interface:\n{e}\n\nVerifique 'src/ui/main.glade'.")
             self.initialization_failed = True; return

        self.selected_file_path = None
        self.selected_folder_path = None
        self.conversion_lock = threading.Lock()
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

    # --- Funções de Seleção ---
    def on_select_file_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Selecione um arquivo de vídeo", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_video = Gtk.FileFilter(); filter_video.set_name("Vídeos"); filter_video.add_mime_type("video/*"); filter_video.add_pattern("*.mp4"); filter_video.add_pattern("*.avi"); filter_video.add_pattern("*.mkv"); filter_video.add_pattern("*.mov"); filter_video.add_pattern("*.webm"); dialog.add_filter(filter_video)
        filter_any = Gtk.FileFilter(); filter_any.set_name("Todos"); filter_any.add_pattern("*"); dialog.add_filter(filter_any)
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

    def run_conversion(self, video_paths):
        python_executable = self._get_python_executable()

        if not self.conversion_lock.acquire(blocking=False):
            GLib.idle_add(self.on_conversion_update, "Outra conversão já está em andamento...")
            return

        total = len(video_paths); output_files = []
        GLib.idle_add(self.on_conversion_update, f"Iniciando conversão de {total} vídeo(s)...")

        for i, video_path in enumerate(video_paths):
            video_name = os.path.basename(video_path)
            output_filename = os.path.splitext(video_name)[0] + ".txt"
            output_filepath = os.path.join(self.output_dir, output_filename)
            GLib.idle_add(self.on_conversion_update, f"({i+1}/{total}): Convertendo {video_name}...")
            cmd = [python_executable, CONVERTER_SCRIPT, "--video", video_path, "--config", self.config_path]

            try:
                print(f"Executando: {shlex.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                print(f"--- Saída ({video_name}) ---\n{result.stdout.strip()}")
                if result.stderr.strip(): print(f"--- Erros ({video_name}) ---\n{result.stderr.strip()}")
                print("-" * (len(video_name) + 24))
                GLib.idle_add(self.on_conversion_update, f"OK ({i+1}/{total}): {video_name} convertido.")
                output_files.append(output_filepath)
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout or 'Erro desconhecido'
                error_msg = f"ERRO ({i+1}/{total}) {video_name}:\n{error_output.strip()}"
                print(error_msg)
                GLib.idle_add(self.on_conversion_update, error_msg.split('\n')[0])
            except FileNotFoundError:
                 error_msg = f"ERRO: Script '{CONVERTER_SCRIPT}' ou Python '{python_executable}' não encontrado."
                 print(error_msg); GLib.idle_add(self.on_conversion_update, error_msg); break
            except Exception as e:
                error_msg = f"ERRO FATAL {video_name}: {e}"
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
        if self.selected_file_path:
            video_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
            file_path = os.path.join(self.output_dir, video_name)
            if not os.path.exists(file_path):
                self.show_error_dialog("Erro", f"Arquivo ASCII '{os.path.basename(file_path)}' não encontrado.\nConverta o vídeo primeiro."); return

            python_executable = self._get_python_executable()
            cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', self.config_path]

            try:
                cmd = ['gnome-terminal', '--'] + cmd_base
                print(f"Executando player: {shlex.join(cmd)}")
                subprocess.Popen(cmd)
            except FileNotFoundError:
                print("Aviso: gnome-terminal não encontrado. Tentando xterm...")
                try:
                    cmd = ['xterm', '-hold', '-e'] + cmd_base # Adicionado -hold para manter a janela aberta
                    print(f"Executando player (xterm): {shlex.join(cmd)}")
                    subprocess.Popen(cmd)
                except FileNotFoundError:
                    print("ERRO: xterm também não encontrado.")
                    self.show_error_dialog("Erro Terminal", "Nenhum terminal compatível (gnome-terminal ou xterm -hold) encontrado.")
                except Exception as e_xterm:
                    print(f"Erro ao abrir xterm: {e_xterm}")
                    self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal (xterm):\n{e_xterm}")
            except Exception as e_gnome:
                print(f"Erro ao abrir gnome-terminal: {e_gnome}")
                self.show_error_dialog("Erro Terminal", f"Não foi possível abrir o terminal (gnome-terminal):\n{e_gnome}")

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
        python_executable = self._get_python_executable()
        cmd_list = [python_executable, CALIBRATOR_SCRIPT, "--config", self.config_path]
        video_arg = None
        if video_to_calibrate and os.path.exists(video_to_calibrate):
            video_arg = video_to_calibrate
            cmd_list.extend(["--video", video_arg])
            print(f"Calibrador usará o vídeo: {os.path.basename(video_arg)}")
        else:
            if video_to_calibrate: print(f"Aviso: Vídeo selecionado '{video_to_calibrate}' não encontrado.")
            print("Nenhum vídeo válido selecionado. Calibrador usará webcam (fonte 0).")

        print(f"Executando calibrador (Processo Separado): {shlex.join(cmd_list)}")
        try:
            process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            stdout_thread = threading.Thread(target=self._read_pipe, args=(process.stdout, sys.stdout)); stderr_thread = threading.Thread(target=self._read_pipe, args=(process.stderr, sys.stderr))
            stdout_thread.daemon = True; stderr_thread.daemon = True
            stdout_thread.start(); stderr_thread.start()
        except FileNotFoundError:
             error_msg = f"ERRO: Script '{CALIBRATOR_SCRIPT}' ou Python '{python_executable}' não encontrado."
             print(error_msg); self.show_error_dialog("Erro Calibrador", error_msg)
        except Exception as e:
            error_msg = f"Erro ao lançar calibrador: {e}"; print(error_msg); self.show_error_dialog("Erro Calibrador", error_msg)

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
        print("Instanciando a classe App...")
        app = App()
        if hasattr(app, 'initialization_failed') and app.initialization_failed:
             print("Inicialização da App falhou (detalhes acima). Encerrando sem Gtk.main().")
             sys.exit(1) # Sai se __init__ marcou falha
        print("Instanciação da App concluída.")

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
            print("Iniciando loop principal GTK (Gtk.main())...")
            Gtk.main()
            print("Loop principal GTK finalizado.")
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
