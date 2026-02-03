import os
import subprocess

from ..constants import GTK_CALIBRATOR_SCRIPT, GTK_FULLSCREEN_PLAYER_SCRIPT


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
        self.logger.info("Abrindo Webcam GTK (Real-Time ASCII)...")
        self._launch_webcam_gtk()

    def _launch_webcam_gtk(self):
        python_executable = self._get_python_executable()
        cmd = [python_executable, GTK_FULLSCREEN_PLAYER_SCRIPT,
               "--config", self.config_path]

        try:
            self.logger.info(f"Executando webcam GTK: {cmd}")
            subprocess.Popen(cmd)
        except Exception as e:
            self.show_error_dialog("Erro Webcam", f"Nao foi possivel abrir a webcam:\n{e}")

    def _launch_gtk_calibrator(self, extra_args: list):
        python_executable = self._get_python_executable()
        cmd = [python_executable, GTK_CALIBRATOR_SCRIPT, "--config", self.config_path] + extra_args

        try:
            self.logger.info(f"Executando calibrador GTK: {cmd}")
            result = subprocess.run(cmd)
            self.reload_config()
            self.logger.info("Calibrador GTK fechado. Configuracoes recarregadas.")
        except Exception as e:
            self.logger.error(f"Erro ao lancar calibrador GTK: {e}")
            self.show_error_dialog("Erro Calibrador", f"Nao foi possivel abrir o calibrador:\n{e}")
