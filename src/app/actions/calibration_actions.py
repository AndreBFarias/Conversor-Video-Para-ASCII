import os
import subprocess
import shlex

from ..constants import GTK_CALIBRATOR_SCRIPT, REALTIME_SCRIPT


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
        font_size = max(8, int(12 * player_zoom))
        title = "Extase em 4R73 - Webcam"

        try:
            cmd = ['kitty', '--class=extase-em-4r73', f'--title={title}', '--'] + cmd_base
            self.logger.info(f"Executando webcam otimizada: {shlex.join(cmd)}")
            subprocess.Popen(cmd)
        except FileNotFoundError:
            self.logger.warning("kitty nao encontrado. Tentando gnome-terminal...")
            try:
                cmd = ['gnome-terminal', f'--zoom={player_zoom}', '--maximize',
                       f'--title={title}', '--class=extase-em-4r73', '--'] + cmd_base
                result = subprocess.run(cmd)
                self.reload_config()
                self.logger.info("Calibrador fechado. Configuracoes recarregadas.")
            except FileNotFoundError:
                self.logger.warning("gnome-terminal nao encontrado. Tentando xterm...")
                try:
                    cmd = ['xterm', '-fn', '6x10', '-maximized',
                           '-title', title, '-e'] + cmd_base
                    result = subprocess.run(cmd)
                    self.reload_config()
                    self.logger.info("Calibrador fechado. Configuracoes recarregadas.")
                except FileNotFoundError:
                    self.show_error_dialog("Erro Terminal", "Nenhum terminal compativel encontrado.")
                except Exception as e:
                    self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")
            except Exception as e:
                self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")
        except Exception as e:
            self.show_error_dialog("Erro Terminal", f"Nao foi possivel abrir o terminal:\n{e}")

    def _launch_gtk_calibrator(self, extra_args: list):
        python_executable = self._get_python_executable()
        cmd = [python_executable, GTK_CALIBRATOR_SCRIPT, "--config", self.config_path] + extra_args

        try:
            self.logger.info(f"Executando calibrador GTK: {shlex.join(cmd)}")
            result = subprocess.run(cmd)
            self.reload_config()
            self.logger.info("Calibrador GTK fechado. Configuracoes recarregadas.")
        except Exception as e:
            self.logger.error(f"Erro ao lancar calibrador GTK: {e}")
            self.show_error_dialog("Erro Calibrador", f"Nao foi possivel abrir o calibrador:\n{e}")
