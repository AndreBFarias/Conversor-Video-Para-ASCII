import os
import subprocess
import shlex

from ..constants import CALIBRATOR_SCRIPT, GTK_CALIBRATOR_SCRIPT, REALTIME_SCRIPT


class CalibrationActionsMixin:
    def on_calibrate_button_clicked(self, widget):
        video_to_calibrate = self.selected_file_path
        cmd_args = []
        if video_to_calibrate and os.path.exists(video_to_calibrate):
            cmd_args = ["--video", video_to_calibrate]
            self.logger.info(f"Calibrador usara o video: {os.path.basename(video_to_calibrate)}")
        else:
            if video_to_calibrate:
                self.logger.warning(f"Video selecionado '{video_to_calibrate}' nao encontrado.")
            self.logger.info("Nenhum video valido selecionado. Calibrador usara webcam (fonte 0).")

        self._launch_gtk_calibrator(cmd_args)

    def on_open_webcam_button_clicked(self, widget):
        self.logger.info("Abrindo Webcam Otimizada (Real-Time ASCII)...")
        self._launch_webcam_in_terminal()

    def _launch_webcam_in_terminal(self):
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, REALTIME_SCRIPT, "--config", self.config_path]
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize',
                   '--title=Extase em 4R73 - Webcam Real-Time',
                   '--class=extase-em-4r73', '--'] + cmd_base
            self.logger.info(f"Executando webcam otimizada: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            self.logger.warning("gnome-terminal nao encontrado. Tentando xterm...")
            try:
                cmd = ['xterm', '-fn', '6x10', '-maximized',
                       '-title', 'Extase em 4R73 - Webcam', '-e'] + cmd_base
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compativel encontrado.")
            except Exception as e:
                self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")
        except Exception as e:
            self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")

    def _launch_gtk_calibrator(self, extra_args: list):
        python_executable = self._get_python_executable()
        cmd = [python_executable, GTK_CALIBRATOR_SCRIPT, "--config", self.config_path] + extra_args

        try:
            self.logger.info(f"Executando calibrador GTK: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except Exception as e:
            self.logger.error(f"Erro ao lancar calibrador GTK: {e}. Tentando fallback OpenCV...")
            self._launch_calibrator_in_terminal(extra_args)

    def _launch_calibrator_in_terminal(self, extra_args: list):
        python_executable = self._get_python_executable()
        cmd_base = [python_executable, CALIBRATOR_SCRIPT, "--config", self.config_path] + extra_args
        player_zoom = self.config.getfloat('Quality', 'player_zoom', fallback=0.7)

        try:
            cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize',
                   '--title=Extase em 4R73 - Calibrador', '--class=extase-em-4r73', '--'] + cmd_base
            self.logger.info(f"Executando calibrador OpenCV (fallback): {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            self.logger.warning("gnome-terminal nao encontrado. Tentando xterm...")
            try:
                base_font_size = 12
                font_size = int(base_font_size * player_zoom)
                cmd = ['xterm', '-fa', f'Mono-{font_size}', '-maximized',
                       '-title', 'Extase em 4R73 - Calibrador', '-e'] + cmd_base
                subprocess.Popen(cmd)
            except FileNotFoundError:
                self.show_error_dialog("Erro Terminal", "Nenhum terminal compativel encontrado.")
            except Exception as e:
                self.show_error_dialog("Erro Calibrador", f"Erro ao lancar xterm: {e}")
        except Exception as e:
            self.show_error_dialog("Erro Calibrador", f"Erro ao lancar gnome-terminal: {e}")
