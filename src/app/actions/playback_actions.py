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
        mode_id = self.play_mode_combo.get_active_id()
        if mode_id:
            self._play_with_mode(mode_id)
        else:
            self._play_with_mode('terminal')

    def _play_with_mode(self, display_mode: str):
        if not self.selected_file_path:
            return

        media_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
        file_path = os.path.join(self.output_dir, media_name)
        if not os.path.exists(file_path):
            self.show_error_dialog("Erro", f"Arquivo ASCII '{os.path.basename(file_path)}' nao encontrado.\nConverta o arquivo primeiro.")
            return

        temp_config = configparser.ConfigParser(interpolation=None)
        temp_config.read_dict(self.config)

        if not temp_config.has_section('Geral'):
            temp_config.add_section('Geral')
        temp_config.set('Geral', 'display_mode', display_mode)

        loop_enabled = self.config.get('Player', 'loop', fallback='nao').lower() in ['sim', 'yes', 'true', '1', 'on']

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as tmp_config_file:
            temp_config.write(tmp_config_file)
            temp_config_path = tmp_config_file.name

        python_executable = self._get_python_executable()
        cmd_base = [python_executable, PLAYER_SCRIPT, '-f', file_path, '--config', temp_config_path]

        if loop_enabled:
            cmd_base.append('-l')

        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)
        self._launch_in_terminal(cmd_base, player_zoom, "Player")

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

        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)
        self._launch_in_terminal(cmd_base, player_zoom, "Player")

    def _launch_in_terminal(self, cmd_base: list, zoom: float, title_suffix: str):
        try:
            cmd = ['gnome-terminal', f'--zoom={zoom}', '--maximize',
                   f'--title=Extase em 4R73 - {title_suffix}', '--class=extase-em-4r73', '--'] + cmd_base
            self.logger.info(f"Executando: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            self.logger.warning("gnome-terminal nao encontrado. Tentando xterm...")
            try:
                cmd = ['xterm', '-fn', '6x10', '-maximized',
                       f'-title', f'Extase em 4R73 - {title_suffix}', '-hold', '-e'] + cmd_base
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compativel encontrado.")
            except Exception as e:
                self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")
        except Exception as e:
            self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")

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
                result = subprocess.run(["xdg-open", abs_path], check=False, capture_output=True, text=True)
                if result.returncode != 0:
                    result_gvfs = subprocess.run(["gvfs-open", abs_path], check=False, capture_output=True, text=True)
                    if result_gvfs.returncode != 0:
                        raise OSError(f"xdg-open e gvfs-open falharam.")
        except FileNotFoundError:
            self.show_error_dialog("Erro", "Comando 'xdg-open'/'gvfs-open' nao encontrado.")
        except Exception as e:
            self.show_error_dialog("Erro ao Abrir", f"Nao foi possivel abrir '{os.path.basename(path)}':\n{e}")
