import os
import subprocess
import threading
import shlex
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from ..constants import (
    CONVERTER_SCRIPT, IMAGE_CONVERTER_SCRIPT,
    PIXEL_ART_CONVERTER_SCRIPT, PIXEL_ART_IMAGE_CONVERTER_SCRIPT,
    VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
)


class ConversionActionsMixin:
    def _is_image_file(self, file_path: str) -> bool:
        return file_path.lower().endswith(IMAGE_EXTENSIONS)

    def _is_video_file(self, file_path: str) -> bool:
        return file_path.lower().endswith(VIDEO_EXTENSIONS)

    def on_convert_button_clicked(self, widget):
        if self.selected_file_path:
            thread = threading.Thread(target=self.run_conversion, args=([self.selected_file_path],))
            thread.daemon = True
            thread.start()

    def on_convert_all_button_clicked(self, widget):
        target_folder = self.selected_folder_path if self.selected_folder_path else self.input_dir
        try:
            if not os.path.isdir(target_folder):
                self.show_error_dialog("Erro", f"Pasta de entrada nao encontrada:\n{target_folder}")
                return

            videos = [f for f in os.listdir(target_folder) if f.lower().endswith(VIDEO_EXTENSIONS)]
            if not videos:
                self.show_error_dialog("Aviso", f"Nenhum video compativel encontrado em:\n{target_folder}")
                return

            video_paths = [os.path.join(target_folder, v) for v in videos]
        except Exception as e:
            self.show_error_dialog("Erro ao Listar Videos", str(e))
            return

        thread = threading.Thread(target=self.run_conversion, args=(video_paths,))
        thread.daemon = True
        thread.start()

    def run_conversion(self, file_paths: list):
        python_executable = self._get_python_executable()

        if not self.conversion_lock.acquire(blocking=False):
            GLib.idle_add(self.on_conversion_update, "Outra conversao ja esta em andamento...")
            return

        total = len(file_paths)
        output_files = []
        GLib.idle_add(self._update_progress, 0.0, f"Iniciando conversao de {total} arquivo(s)...")

        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)
            output_filename = os.path.splitext(file_name)[0] + ".txt"
            output_filepath = os.path.join(self.output_dir, output_filename)
            progress = i / total
            GLib.idle_add(self._update_progress, progress, f"({i+1}/{total}): {file_name}")

            conversion_mode = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()

            if self._is_image_file(file_path):
                if conversion_mode == 'pixelart':
                    cmd = [python_executable, PIXEL_ART_IMAGE_CONVERTER_SCRIPT, "--image", file_path, "--config", self.config_path]
                    script_name = PIXEL_ART_IMAGE_CONVERTER_SCRIPT
                else:
                    cmd = [python_executable, IMAGE_CONVERTER_SCRIPT, "--image", file_path, "--config", self.config_path]
                    script_name = IMAGE_CONVERTER_SCRIPT
            else:
                if conversion_mode == 'pixelart':
                    cmd = [python_executable, PIXEL_ART_CONVERTER_SCRIPT, "--video", file_path, "--config", self.config_path]
                    script_name = PIXEL_ART_CONVERTER_SCRIPT
                else:
                    cmd = [python_executable, CONVERTER_SCRIPT, "--video", file_path, "--config", self.config_path]
                    script_name = CONVERTER_SCRIPT

            try:
                self.logger.info(f"Executando: {shlex.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                self.logger.info(f"Saida ({file_name}): {result.stdout.strip()}")
                if result.stderr.strip():
                    self.logger.warning(f"Erros ({file_name}): {result.stderr.strip()}")
                progress = (i + 1) / total
                GLib.idle_add(self._update_progress, progress, f"OK: {file_name}")
                output_files.append(output_filepath)
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout or 'Erro desconhecido'
                error_msg = f"ERRO ({i+1}/{total}) {file_name}:\n{error_output.strip()}"
                self.logger.error(error_msg)
                GLib.idle_add(self._update_progress, (i + 1) / total, f"ERRO: {file_name}")
            except FileNotFoundError:
                error_msg = f"ERRO: Script '{script_name}' ou Python '{python_executable}' nao encontrado."
                self.logger.error(error_msg)
                GLib.idle_add(self._update_progress, 0.0, "ERRO: Script nao encontrado")
                break
            except Exception as e:
                error_msg = f"ERRO FATAL {file_name}: {e}"
                self.logger.error(error_msg)
                GLib.idle_add(self._update_progress, (i + 1) / total, f"ERRO: {file_name}")

        final_message = f"Concluído: {len(output_files)}/{total} sucesso"
        GLib.idle_add(self._update_progress, 1.0, final_message)
        GLib.idle_add(self.update_button_states)
        if output_files:
            GLib.idle_add(self.show_completion_popup, output_files)
        self.conversion_lock.release()

    def _update_progress(self, fraction: float, text: str):
        if hasattr(self, 'conversion_progress') and self.conversion_progress:
            self.conversion_progress.set_fraction(fraction)
            self.conversion_progress.set_text(text)
        return False

    def on_conversion_update(self, message: str):
        if hasattr(self, 'conversion_progress') and self.conversion_progress:
            self.conversion_progress.set_text(message)
        return False

    def show_completion_popup(self, output_files: list):
        if not self.window or not self.window.is_visible():
            return False

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Conversao Concluida"
        )
        files_str = "\n".join([os.path.basename(f) for f in output_files])
        dialog.format_secondary_text(f"Arquivo(s) gerado(s) em:\n'{self.output_dir}':\n\n{files_str}")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show_all()
        return False
