import os
import subprocess
import threading
import shlex
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf
import numpy as np

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

        # Perguntar modo de conversao
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Modo de Conversão em Lote"
        )
        dialog.format_secondary_text(f"Encontrados {len(videos)} vídeos.\nComo deseja prosseguir?")
        dialog.add_buttons(
            "Config. Atual (Rápido)", 100,
            "Ajustar Video a Video", 101,
            "Cancelar", Gtk.ResponseType.CANCEL
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.CANCEL:
            return
        
        interactive_mode = (response == 101)

        thread = threading.Thread(target=self.run_conversion, args=(video_paths, interactive_mode))
        thread.daemon = True
        thread.start()

    def run_conversion(self, file_paths: list, interactive: bool = False):
        python_executable = self._get_python_executable()
        self.reload_config()

        if not self.conversion_lock.acquire(blocking=False):
            GLib.idle_add(self.on_conversion_update, "Outra conversao ja esta em andamento...")
            return

        total = len(file_paths)
        output_files = []
        GLib.idle_add(self._update_progress, 0.0, f"Iniciando conversao de {total} arquivo(s)...")

        output_format = self.config.get('Output', 'format', fallback='txt').lower()
        chroma_override = None

        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)

            # Modo Interativo: Abrir Calibrador antes de converter
            if interactive:
                GLib.idle_add(self._update_progress, i / total, f"Aguardando calibração: {file_name}")
                try:
                    self._launch_gtk_calibrator(["--video", file_path])
                except Exception as e:
                    self.logger.error(f"Erro ao abrir calibrador para {file_name}: {e}")

                self.reload_config()

                chroma_override = {
                    'h_min': self.config.getint('ChromaKey', 'h_min', fallback=35),
                    'h_max': self.config.getint('ChromaKey', 'h_max', fallback=85),
                    's_min': self.config.getint('ChromaKey', 's_min', fallback=40),
                    's_max': self.config.getint('ChromaKey', 's_max', fallback=255),
                    'v_min': self.config.getint('ChromaKey', 'v_min', fallback=40),
                    'v_max': self.config.getint('ChromaKey', 'v_max', fallback=255),
                    'erode': self.config.getint('ChromaKey', 'erode', fallback=2),
                    'dilate': self.config.getint('ChromaKey', 'dilate', fallback=2)
                }
                self.logger.info(f"Valores HSV calibrados para {file_name}: {chroma_override}")
            else:
                chroma_override = None
                self.reload_config()

            if output_format == 'mp4':
                output_filename = os.path.splitext(file_name)[0] + "_ascii.mp4"
            elif output_format == 'gif':
                output_filename = os.path.splitext(file_name)[0] + "_ascii.gif"
            elif output_format == 'html':
                output_filename = os.path.splitext(file_name)[0] + "_player.html"
            else:
                output_filename = os.path.splitext(file_name)[0] + ".txt"

            output_filepath = os.path.join(self.output_dir, output_filename)
            progress = i / total
            GLib.idle_add(self._update_progress, progress, f"({i+1}/{total}): {file_name}")

            conversion_mode = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()

            if output_format == 'mp4' and not self._is_image_file(file_path):
                gpu_enabled = self.config.getboolean('Conversor', 'gpu_enabled', fallback=False)
                
                try:
                    def progress_cb(current, total_frames, frame_data=None):
                        sub_progress = (i + (current / total_frames)) / total
                        GLib.idle_add(self._update_progress, sub_progress, f"({i+1}/{total}): {file_name} - Frame {current}/{total_frames}")
                        if frame_data is not None:
                            GLib.idle_add(self._update_thumbnail, frame_data)

                    if gpu_enabled:
                        try:
                            from src.core.gpu_converter import converter_video_para_mp4_gpu
                            output_file = converter_video_para_mp4_gpu(file_path, self.output_dir, self.config, progress_callback=progress_cb, chroma_override=chroma_override)
                            self.logger.info(f"Video MP4 (GPU) gerado: {output_file}")
                        except ImportError:
                            self.logger.error("GPU Converter nao encontrado ou dependencia faltando (cupy). Caindo para CPU.")
                            from src.core.mp4_converter import converter_video_para_mp4
                            output_file = converter_video_para_mp4(file_path, self.output_dir, self.config, progress_callback=progress_cb, chroma_override=chroma_override)
                            self.logger.info(f"Video MP4 (CPU fallback) gerado: {output_file}")
                        except Exception as e:
                             raise e
                    else:
                        from src.core.mp4_converter import converter_video_para_mp4
                        output_file = converter_video_para_mp4(file_path, self.output_dir, self.config, progress_callback=progress_cb, chroma_override=chroma_override)
                        self.logger.info(f"Video MP4 (CPU) gerado: {output_file}")

                    output_files.append(output_file)
                except Exception as e:
                    self.logger.error(f"Erro ao converter {file_name} para MP4: {e}")
                    GLib.idle_add(self.on_conversion_update, f"Erro: {file_name} - {e}")
                continue

            if output_format == 'gif' and not self._is_image_file(file_path):
                from src.core.gif_converter import converter_video_para_gif
                try:
                    def progress_cb(current, total_frames, frame_data=None):
                        sub_progress = (i + (current / total_frames)) / total
                        GLib.idle_add(self._update_progress, sub_progress, f"({i+1}/{total}): {file_name} - Frame {current}/{total_frames}")
                        if frame_data is not None:
                            GLib.idle_add(self._update_thumbnail, frame_data)

                    output_file = converter_video_para_gif(file_path, self.output_dir, self.config, progress_callback=progress_cb, chroma_override=chroma_override)
                    output_files.append(output_file)
                    self.logger.info(f"GIF gerado: {output_file}")
                except Exception as e:
                    self.logger.error(f"Erro ao converter {file_name} para GIF: {e}")
                    GLib.idle_add(self.on_conversion_update, f"Erro: {file_name} - {e}")
                continue

            if output_format == 'html' and not self._is_image_file(file_path):
                from src.core.html_converter import converter_video_para_html
                try:
                    def progress_cb(current, total_frames, frame_data=None):
                        sub_progress = (i + (current / total_frames)) / total
                        GLib.idle_add(self._update_progress, sub_progress, f"({i+1}/{total}): {file_name} - Frame {current}/{total_frames}")
                        if frame_data is not None:
                            GLib.idle_add(self._update_thumbnail, frame_data)

                    output_file = converter_video_para_html(file_path, self.output_dir, self.config, progress_callback=progress_cb, chroma_override=chroma_override)
                    output_files.append(output_file)
                    self.logger.info(f"HTML gerado: {output_file}")
                except Exception as e:
                    self.logger.error(f"Erro ao converter {file_name} para HTML: {e}")
                    GLib.idle_add(self.on_conversion_update, f"Erro: {file_name} - {e}")
                continue

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

            if chroma_override and script_name == CONVERTER_SCRIPT:
                cmd.extend([
                    "--h-min", str(chroma_override['h_min']),
                    "--h-max", str(chroma_override['h_max']),
                    "--s-min", str(chroma_override['s_min']),
                    "--s-max", str(chroma_override['s_max']),
                    "--v-min", str(chroma_override['v_min']),
                    "--v-max", str(chroma_override['v_max']),
                    "--erode", str(chroma_override['erode']),
                    "--dilate", str(chroma_override['dilate'])
                ])

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
        GLib.idle_add(self._hide_thumbnail)
        GLib.idle_add(self.update_button_states)
        if output_files:
            GLib.idle_add(self.show_completion_popup, output_files)
        self.conversion_lock.release()

    def _update_progress(self, fraction: float, text: str):
        if hasattr(self, 'conversion_progress') and self.conversion_progress:
            self.conversion_progress.set_fraction(fraction)
            self.conversion_progress.set_text(text)
        return False

    def _update_thumbnail(self, frame_array: np.ndarray):
        if not hasattr(self, 'preview_thumbnail') or not self.preview_thumbnail:
            return False

        import time
        if not hasattr(self, '_last_thumbnail_update'):
            self._last_thumbnail_update = 0

        current_time = time.time()
        if current_time - self._last_thumbnail_update < 0.1:
            return False

        self._last_thumbnail_update = current_time

        if frame_array is None or frame_array.size == 0:
            self.preview_thumbnail.set_visible(False)
            return False

        height, width = frame_array.shape[:2]
        max_width = 400
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            frame_array = frame_array.copy()
            import cv2
            frame_array = cv2.resize(frame_array, (new_width, new_height), interpolation=cv2.INTER_AREA)
            height, width = new_height, new_width

        if len(frame_array.shape) == 2:
            rgb_array = np.stack([frame_array] * 3, axis=-1)
        elif frame_array.shape[2] == 3:
            rgb_array = frame_array[:, :, ::-1]
        else:
            rgb_array = frame_array[:, :, :3][:, :, ::-1]

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            rgb_array.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            width,
            height,
            width * 3
        )

        self.preview_thumbnail.set_from_pixbuf(pixbuf)
        self.preview_thumbnail.set_visible(True)
        
        if hasattr(self, 'preview_frame') and self.preview_frame:
            self.preview_frame.set_visible(True)
            
        return False

    def _hide_thumbnail(self):
        if hasattr(self, 'preview_thumbnail') and self.preview_thumbnail:
            self.preview_thumbnail.set_visible(False)
        if hasattr(self, 'preview_frame') and self.preview_frame:
            self.preview_frame.set_visible(False)
            
        # Forcar redimensionamento da janela para o minimo possivel (compactar)
        if hasattr(self, 'window') and self.window:
            # Reseta qualquer requisicao de tamanho anterior que possa estar segurando a janela aberta
            self.window.set_size_request(-1, -1)
            self.window.resize(1, 1)
            # Forcar processamento de eventos pendentes para garantir o resize
            while Gtk.events_pending():
                Gtk.main_iteration()
            
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
