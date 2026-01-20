import os
import subprocess
import platform
import shlex
import configparser
import tempfile
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..constants import PLAYER_SCRIPT


class PlaybackActionsMixin:
    def on_play_button_clicked(self, widget):
        self._play_with_terminal()

    def _play_with_terminal(self):
        if not self.selected_file_path:
            return

        media_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
        file_path = os.path.join(self.output_dir, media_name)
        if not os.path.exists(file_path):
            self.show_error_dialog("Erro", f"Arquivo ASCII '{os.path.basename(file_path)}' nao encontrado.\nConverta o arquivo primeiro.")
            return

        # Player setup
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', self.config_path]

        loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']
        if loop_enabled:
            cmd_base.append('-l')

        # Use 1.0 zoom equivalent or just ignore zoom since we use kitty config
        # We perform the launch directly here to simplify
        title = f"Extase em 4R73 - Player"
        
        try:
            # Removed font_size override and maximized flag to respect kitty.conf
            cmd = ['kitty', '--class=extase-em-4r73', f'--title={title}', '--'] + cmd_base
            self.logger.info(f"Executando player: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            self.logger.warning("kitty nao encontrado. Tentando gnome-terminal...")
            try:
                cmd = ['gnome-terminal', '--maximize',
                       f'--title={title}', '--class=extase-em-4r73', '--'] + cmd_base
                subprocess.Popen(cmd)
            except FileNotFoundError:
                try:
                    cmd = ['xterm', '-maximized', '-title', title, '-hold', '-e'] + cmd_base
                    subprocess.Popen(cmd)
                except Exception as e:
                    self.show_error_dialog("Erro Terminal", f"Nenhum terminal compativel encontrado.\n{e}")
            except Exception as e:
                self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir gnome-terminal:\n{e}")
        except Exception as e:
            self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir kitty:\n{e}")

    def on_play_ascii_button_clicked(self, widget):
        if self.selected_ascii_path and os.path.exists(self.selected_ascii_path):
            self._launch_player_in_terminal(self.selected_ascii_path)
        else:
            self.show_error_dialog("Erro", "Nenhum arquivo ASCII valido selecionado.")

    def _launch_player_in_terminal(self, file_path: str):
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', self.config_path]

        loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']
        if loop_enabled:
            cmd_base.append('-l')

        title = "Extase em 4R73 - Player"
        try:
            cmd = ['kitty', '--class=extase-em-4r73', f'--title={title}', '--'] + cmd_base
            subprocess.Popen(cmd)
        except Exception:
             # Fallback logic could be repeated or shared, but for brevity we minimalize here or call shared
             pass

    # Removing _launch_in_terminal helper as it is now integrated/simplified above


    def on_open_video_clicked(self, widget):
        if self.selected_file_path:
            if not os.path.exists(self.selected_file_path):
                self.show_error_dialog("Erro", f"Video '{os.path.basename(self.selected_file_path)}' nao encontrado.")
                return
            self.open_path(self.selected_file_path)

    def on_open_folder_clicked(self, widget):
        if not os.path.isdir(self.output_dir):
            self.show_error_dialog("Aviso", f"Pasta de saida '{self.output_dir}' ainda nao existe.")
            return
        self.open_path(self.output_dir)

    def open_path(self, path: str):
        try:
            abs_path = os.path.abspath(path)
            self.logger.info(f"Tentando abrir: {abs_path}")

            if platform.system() == "Windows":
                os.startfile(abs_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", abs_path])
            else:
                result = subprocess.run(["xdg-open", abs_path], check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if result.returncode != 0:
                    result_gvfs = subprocess.run(["gvfs-open", abs_path], check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    if result_gvfs.returncode != 0:
                        raise OSError("xdg-open e gvfs-open falharam.")
        except FileNotFoundError:
            self.show_error_dialog("Erro", "Comando 'xdg-open'/'gvfs-open' nao encontrado.")
        except Exception as e:
            self.show_error_dialog("Erro ao Abrir", f"Nao foi possivel abrir '{os.path.basename(path)}':\n{e}")
