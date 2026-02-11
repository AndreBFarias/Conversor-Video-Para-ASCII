import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class FileActionsMixin:
    def on_select_file_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Selecione um arquivo de midia (Video ou Imagem)",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter_media = Gtk.FileFilter()
        filter_media.set_name("Midia (mp4, avi, mkv, mov, webm, gif, png, jpg, jpeg, bmp, webp)")
        for ext in ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.webm', '*.gif', '*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']:
            filter_media.add_pattern(ext)
        dialog.add_filter(filter_media)

        filter_video = Gtk.FileFilter()
        filter_video.set_name("Apenas Videos (mp4, avi, mkv, mov, webm, gif)")
        for ext in ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.webm', '*.gif']:
            filter_video.add_pattern(ext)
        dialog.add_filter(filter_video)

        filter_image = Gtk.FileFilter()
        filter_image.set_name("Apenas Imagens (png, jpg, jpeg, bmp, webp)")
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']:
            filter_image.add_pattern(ext)
        dialog.add_filter(filter_image)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Todos (*.*)")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        try:
            if os.path.isdir(self.input_dir):
                dialog.set_current_folder(self.input_dir)
        except Exception:
            pass

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_file_path = dialog.get_filename()
            self.selected_folder_path = None
            self.selected_path_label.set_text(f"Arquivo: {os.path.basename(self.selected_file_path)}")
            self.selected_path_label.get_style_context().add_class("file-selected")
            self.logger.info(f"Arquivo selecionado: {self.selected_file_path}")
        dialog.destroy()
        self.update_button_states()
        self._refresh_preview()

    def on_select_folder_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Selecione uma pasta com videos",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Selecionar", Gtk.ResponseType.OK)

        try:
            if os.path.isdir(self.input_dir):
                dialog.set_current_folder(self.input_dir)
        except Exception:
            pass

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_folder_path = dialog.get_filename()
            self.selected_file_path = None
            self.selected_path_label.set_text(f"Pasta: .../{os.path.basename(self.selected_folder_path)}")
            self.selected_path_label.get_style_context().add_class("file-selected")
            self.logger.info(f"Pasta selecionada: {self.selected_folder_path}")
        dialog.destroy()
        self.update_button_states()
        self._refresh_preview()

    def on_select_ascii_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Selecione um arquivo ASCII (.txt)",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Arquivos de Texto")
        filter_text.add_mime_type("text/plain")
        filter_text.add_pattern("*.txt")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Todos")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        try:
            if os.path.isdir(self.output_dir):
                dialog.set_current_folder(self.output_dir)
        except Exception:
            pass

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_ascii_path = dialog.get_filename()
            self.logger.info(f"Arquivo ASCII selecionado: {self.selected_ascii_path}")
        dialog.destroy()
        self.update_button_states()

    def update_button_states(self):
        if not hasattr(self, 'convert_button') or not self.convert_button:
            return

        file_selected = self.selected_file_path is not None and os.path.exists(self.selected_file_path)
        folder_selected = self.selected_folder_path is not None and os.path.isdir(self.selected_folder_path)

        ascii_exists = False
        if file_selected and hasattr(self, 'output_dir'):
            media_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + ".txt"
            ascii_path = os.path.join(self.output_dir, media_name)
            ascii_exists = os.path.exists(ascii_path)

        self.convert_button.set_sensitive(file_selected)
        self.play_button.set_sensitive(file_selected and ascii_exists)
        self.open_video_button.set_sensitive(file_selected)
        self.convert_all_button.set_sensitive(folder_selected)
        self.calibrate_button.set_sensitive(True)
        self.open_webcam_button.set_sensitive(True)
        self.play_ascii_button.set_sensitive(
            self.selected_ascii_path is not None and os.path.exists(self.selected_ascii_path)
        )
