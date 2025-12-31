import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..constants import QUALITY_PRESETS, BIT_PRESETS, DEFAULT_LUMINANCE_RAMP


class OptionsActionsMixin:
    def _create_mode_widgets(self):
        try:
            if not hasattr(self, 'options_notebook') or not self.options_notebook:
                return

            notebook = self.options_notebook

            mode_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            mode_page.set_margin_start(15)
            mode_page.set_margin_end(15)
            mode_page.set_margin_top(15)
            mode_page.set_margin_bottom(15)

            mode_frame = Gtk.Frame(label="Modo de Conversao")
            mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            mode_box.set_margin_start(10)
            mode_box.set_margin_end(10)
            mode_box.set_margin_top(10)
            mode_box.set_margin_bottom(10)

            self.opt_mode_ascii_radio = Gtk.RadioButton.new_with_label_from_widget(None, "ASCII Art")
            self.opt_mode_pixelart_radio = Gtk.RadioButton.new_with_label_from_widget(self.opt_mode_ascii_radio, "Pixel Art")

            mode_box.pack_start(self.opt_mode_ascii_radio, False, False, 0)
            mode_box.pack_start(self.opt_mode_pixelart_radio, False, False, 0)
            mode_frame.add(mode_box)

            pixelart_frame = Gtk.Frame(label="Configuracoes Pixel Art")
            pixelart_grid = Gtk.Grid()
            pixelart_grid.set_column_spacing(10)
            pixelart_grid.set_row_spacing(5)
            pixelart_grid.set_margin_start(10)
            pixelart_grid.set_margin_end(10)
            pixelart_grid.set_margin_top(10)
            pixelart_grid.set_margin_bottom(10)

            bit_preset_label = Gtk.Label(label="Preset de Bits:")
            bit_preset_label.set_halign(Gtk.Align.START)
            self.opt_bit_preset_combo = Gtk.ComboBoxText()
            self.opt_bit_preset_combo.append("8bit_low", "8-bit Low (16 cores, px:6)")
            self.opt_bit_preset_combo.append("8bit_high", "8-bit High (16 cores, px:5)")
            self.opt_bit_preset_combo.append("16bit_low", "16-bit Low (128 cores, px:3)")
            self.opt_bit_preset_combo.append("16bit_high", "16-bit High (128 cores, px:2)")
            self.opt_bit_preset_combo.append("32bit", "32-bit (256 cores, px:2)")
            self.opt_bit_preset_combo.append("64bit", "64-bit (256 cores, px:1)")
            self.opt_bit_preset_combo.append("custom", "Custom (Manual)")
            self.opt_bit_preset_combo.connect("changed", self.on_bit_preset_changed)

            pixel_size_label = Gtk.Label(label="Tamanho do Pixel:")
            pixel_size_label.set_halign(Gtk.Align.START)
            self.opt_pixel_size_spin = Gtk.SpinButton()
            self.opt_pixel_size_spin.set_range(1, 16)
            self.opt_pixel_size_spin.set_increments(1, 1)
            self.opt_pixel_size_spin.set_value(2)

            palette_size_label = Gtk.Label(label="Tamanho da Paleta:")
            palette_size_label.set_halign(Gtk.Align.START)
            self.opt_palette_size_spin = Gtk.SpinButton()
            self.opt_palette_size_spin.set_range(2, 256)
            self.opt_palette_size_spin.set_increments(1, 8)
            self.opt_palette_size_spin.set_value(16)

            self.opt_fixed_palette_check = Gtk.CheckButton.new_with_label("Usar Paleta Fixa (Retro)")

            pixelart_grid.attach(bit_preset_label, 0, 0, 1, 1)
            pixelart_grid.attach(self.opt_bit_preset_combo, 1, 0, 1, 1)
            pixelart_grid.attach(pixel_size_label, 0, 1, 1, 1)
            pixelart_grid.attach(self.opt_pixel_size_spin, 1, 1, 1, 1)
            pixelart_grid.attach(palette_size_label, 0, 2, 1, 1)
            pixelart_grid.attach(self.opt_palette_size_spin, 1, 2, 1, 1)
            pixelart_grid.attach(self.opt_fixed_palette_check, 0, 3, 2, 1)

            pixelart_frame.add(pixelart_grid)

            mode_page.pack_start(mode_frame, False, False, 0)
            mode_page.pack_start(pixelart_frame, False, False, 0)

            tab_label = Gtk.Label(label="Modo")
            notebook.append_page(mode_page, tab_label)
            mode_page.show_all()

            self._mode_widgets_created = True

        except Exception as e:
            import traceback
            self.logger.error(f"Erro ao criar widgets de modo: {e}")
            traceback.print_exc()

    def _create_quality_preset_combo(self):
        try:
            main_box = None
            for child in self.window.get_children():
                if isinstance(child, Gtk.Box):
                    main_box = child
                    break

            if not main_box:
                return

            preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            preset_box.set_margin_start(10)
            preset_box.set_margin_end(10)
            preset_box.set_margin_top(5)
            preset_box.set_margin_bottom(10)

            preset_label = Gtk.Label(label="Qualidade:")
            preset_label.set_halign(Gtk.Align.START)

            self.quality_preset_combo = Gtk.ComboBoxText()
            self.quality_preset_combo.append("mobile", "Mobile (144p) - 100x25")
            self.quality_preset_combo.append("low", "Low (360p) - 120x30")
            self.quality_preset_combo.append("medium", "Medium (480p) - 180x45")
            self.quality_preset_combo.append("high", "High (540p) - 240x60")
            self.quality_preset_combo.append("veryhigh", "Very High (720p) - 300x75")
            self.quality_preset_combo.append("custom", "Custom (Manual)")

            current_preset = self.config.get('Quality', 'preset', fallback='medium')
            self.quality_preset_combo.set_active_id(current_preset)
            self.quality_preset_combo.connect("changed", self.on_quality_preset_changed)
            self.quality_preset_combo.set_hexpand(True)

            preset_box.pack_start(preset_label, False, False, 0)
            preset_box.pack_start(self.quality_preset_combo, True, True, 0)

            main_box.pack_start(preset_box, False, False, 0)
            main_box.reorder_child(preset_box, 4)
            preset_box.show_all()

        except Exception as e:
            import traceback
            self.logger.error(f"Erro ao criar ComboBox de presets: {e}")
            traceback.print_exc()

    def on_quality_preset_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id or preset_id == 'custom':
            return

        try:
            if preset_id in QUALITY_PRESETS:
                preset = QUALITY_PRESETS[preset_id]
                self.config.set('Conversor', 'target_width', str(preset['width']))
                self.config.set('Conversor', 'target_height', str(preset['height']))
                self.config.set('Conversor', 'char_aspect_ratio', str(preset['aspect']))
                self.config.set('Quality', 'preset', preset_id)
                self.config.set('Quality', 'player_zoom', str(preset['zoom']))
                self.save_config()
        except Exception as e:
            self.logger.error(f"Erro ao salvar preset: {e}")

    def on_bit_preset_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id or preset_id == 'custom':
            return

        if preset_id not in BIT_PRESETS:
            return

        preset = BIT_PRESETS[preset_id]

        if hasattr(self, 'opt_pixel_size_spin') and self.opt_pixel_size_spin:
            self.opt_pixel_size_spin.set_value(preset['pixel_size'])

        if hasattr(self, 'opt_palette_size_spin') and self.opt_palette_size_spin:
            self.opt_palette_size_spin.set_value(preset['palette_size'])

    def on_options_button_clicked(self, widget):
        try:
            loop_val_str = self.config.get('Player', 'loop', fallback='nao').lower()
            loop_val = loop_val_str in ['sim', 'yes', 'true', '1', 'on']
            self.opt_loop_check.set_active(loop_val)

            width_val = self.config.getint('Conversor', 'target_width', fallback=120)
            height_val = self.config.getint('Conversor', 'target_height', fallback=0)
            sobel_val = self.config.getint('Conversor', 'sobel_threshold', fallback=100)
            aspect_val = self.config.getfloat('Conversor', 'char_aspect_ratio', fallback=0.95)

            self.opt_width_spin.set_value(width_val)
            self.opt_height_spin.set_value(height_val)
            self.opt_sobel_spin.set_value(sobel_val)
            self.opt_aspect_spin.set_value(aspect_val)

            luminance_val = self.config.get('Conversor', 'luminance_ramp', fallback=DEFAULT_LUMINANCE_RAMP)
            self.opt_luminance_entry.set_text(luminance_val)

            h_min = self.config.getint('ChromaKey', 'h_min', fallback=35)
            h_max = self.config.getint('ChromaKey', 'h_max', fallback=85)
            s_min = self.config.getint('ChromaKey', 's_min', fallback=40)
            s_max = self.config.getint('ChromaKey', 's_max', fallback=255)
            v_min = self.config.getint('ChromaKey', 'v_min', fallback=40)
            v_max = self.config.getint('ChromaKey', 'v_max', fallback=255)

            self.opt_h_min_spin.set_value(h_min)
            self.opt_h_max_spin.set_value(h_max)
            self.opt_s_min_spin.set_value(s_min)
            self.opt_s_max_spin.set_value(s_max)
            self.opt_v_min_spin.set_value(v_min)
            self.opt_v_max_spin.set_value(v_max)

            erode = self.config.getint('ChromaKey', 'erode', fallback=2)
            dilate = self.config.getint('ChromaKey', 'dilate', fallback=2)
            self.opt_erode_spin.set_value(erode)
            self.opt_dilate_spin.set_value(dilate)

            mode_val = self.config.get('Mode', 'conversion_mode', fallback='ascii').lower()
            pixel_size_val = self.config.getint('PixelArt', 'pixel_size', fallback=2)
            palette_size_val = self.config.getint('PixelArt', 'color_palette_size', fallback=16)
            fixed_palette_val = self.config.getboolean('PixelArt', 'use_fixed_palette', fallback=False)

            if not hasattr(self, '_mode_widgets_created') or not self._mode_widgets_created:
                self._create_mode_widgets()

            if hasattr(self, 'opt_mode_pixelart_radio') and self.opt_mode_pixelart_radio:
                if mode_val == 'pixelart':
                    self.opt_mode_pixelart_radio.set_active(True)
                else:
                    self.opt_mode_ascii_radio.set_active(True)

                if self.opt_pixel_size_spin:
                    self.opt_pixel_size_spin.set_value(pixel_size_val)
                if self.opt_palette_size_spin:
                    self.opt_palette_size_spin.set_value(palette_size_val)
                if self.opt_fixed_palette_check:
                    self.opt_fixed_palette_check.set_active(fixed_palette_val)

        except Exception as e:
            self.logger.error(f"Erro ao carregar opcoes: {e}")

        self.options_dialog.show_all()

    def on_options_cancel_clicked(self, widget):
        self.options_dialog.hide()

    def on_options_restore_clicked(self, widget):
        self.opt_loop_check.set_active(False)
        self.opt_width_spin.set_value(120)
        self.opt_height_spin.set_value(0)
        self.opt_sobel_spin.set_value(100)
        self.opt_aspect_spin.set_value(0.95)
        self.opt_luminance_entry.set_text(DEFAULT_LUMINANCE_RAMP)
        self.opt_h_min_spin.set_value(35)
        self.opt_h_max_spin.set_value(85)
        self.opt_s_min_spin.set_value(40)
        self.opt_s_max_spin.set_value(255)
        self.opt_v_min_spin.set_value(40)
        self.opt_v_max_spin.set_value(255)
        self.opt_erode_spin.set_value(2)
        self.opt_dilate_spin.set_value(2)

    def on_options_save_clicked(self, widget):
        try:
            if 'Player' not in self.config:
                self.config.add_section('Player')
            self.config.set('Player', 'loop', 'sim' if self.opt_loop_check.get_active() else 'nao')

            if 'Conversor' not in self.config:
                self.config.add_section('Conversor')
            self.config.set('Conversor', 'target_width', str(int(self.opt_width_spin.get_value())))
            self.config.set('Conversor', 'target_height', str(int(self.opt_height_spin.get_value())))
            self.config.set('Conversor', 'sobel_threshold', str(int(self.opt_sobel_spin.get_value())))
            self.config.set('Conversor', 'char_aspect_ratio', str(self.opt_aspect_spin.get_value()))
            self.config.set('Conversor', 'luminance_ramp', self.opt_luminance_entry.get_text())

            if 'ChromaKey' not in self.config:
                self.config.add_section('ChromaKey')
            self.config.set('ChromaKey', 'h_min', str(int(self.opt_h_min_spin.get_value())))
            self.config.set('ChromaKey', 'h_max', str(int(self.opt_h_max_spin.get_value())))
            self.config.set('ChromaKey', 's_min', str(int(self.opt_s_min_spin.get_value())))
            self.config.set('ChromaKey', 's_max', str(int(self.opt_s_max_spin.get_value())))
            self.config.set('ChromaKey', 'v_min', str(int(self.opt_v_min_spin.get_value())))
            self.config.set('ChromaKey', 'v_max', str(int(self.opt_v_max_spin.get_value())))
            self.config.set('ChromaKey', 'erode', str(int(self.opt_erode_spin.get_value())))
            self.config.set('ChromaKey', 'dilate', str(int(self.opt_dilate_spin.get_value())))

            if hasattr(self, 'opt_mode_pixelart_radio') and self.opt_mode_pixelart_radio:
                if 'Mode' not in self.config:
                    self.config.add_section('Mode')
                mode_val = 'pixelart' if self.opt_mode_pixelart_radio.get_active() else 'ascii'
                self.config.set('Mode', 'conversion_mode', mode_val)

                if 'PixelArt' not in self.config:
                    self.config.add_section('PixelArt')
                self.config.set('PixelArt', 'pixel_size', str(int(self.opt_pixel_size_spin.get_value())))
                self.config.set('PixelArt', 'color_palette_size', str(int(self.opt_palette_size_spin.get_value())))
                self.config.set('PixelArt', 'use_fixed_palette', 'true' if self.opt_fixed_palette_check.get_active() else 'false')

            self.save_config()

        except Exception as e:
            self.show_error_dialog("Erro ao Salvar", f"Nao foi possivel salvar as configuracoes:\n{e}")

        self.options_dialog.hide()

    def on_test_converter_clicked(self, widget):
        try:
            if 'Conversor' not in self.config:
                self.config.add_section('Conversor')
            self.config.set('Conversor', 'target_width', str(int(self.opt_width_spin.get_value())))
            self.config.set('Conversor', 'target_height', str(int(self.opt_height_spin.get_value())))
            self.config.set('Conversor', 'sobel_threshold', str(int(self.opt_sobel_spin.get_value())))
            self.config.set('Conversor', 'char_aspect_ratio', str(self.opt_aspect_spin.get_value()))
            self.config.set('Conversor', 'luminance_ramp', self.opt_luminance_entry.get_text())
            self.save_config()
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuracoes para teste: {e}")

        video_to_test = self.selected_file_path
        cmd_args = []
        if video_to_test and hasattr(self, '_is_video_file') and self._is_video_file(video_to_test):
            cmd_args = ["--video", video_to_test]

        self._launch_calibrator_in_terminal(cmd_args)

    def on_test_chroma_clicked(self, widget):
        try:
            if 'ChromaKey' not in self.config:
                self.config.add_section('ChromaKey')
            self.config.set('ChromaKey', 'h_min', str(int(self.opt_h_min_spin.get_value())))
            self.config.set('ChromaKey', 'h_max', str(int(self.opt_h_max_spin.get_value())))
            self.config.set('ChromaKey', 's_min', str(int(self.opt_s_min_spin.get_value())))
            self.config.set('ChromaKey', 's_max', str(int(self.opt_s_max_spin.get_value())))
            self.config.set('ChromaKey', 'v_min', str(int(self.opt_v_min_spin.get_value())))
            self.config.set('ChromaKey', 'v_max', str(int(self.opt_v_max_spin.get_value())))
            self.config.set('ChromaKey', 'erode', str(int(self.opt_erode_spin.get_value())))
            self.config.set('ChromaKey', 'dilate', str(int(self.opt_dilate_spin.get_value())))
            self.save_config()
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuracoes de chroma para teste: {e}")

        video_to_test = self.selected_file_path
        cmd_args = []
        if video_to_test and hasattr(self, '_is_video_file') and self._is_video_file(video_to_test):
            cmd_args = ["--video", video_to_test]

        self._launch_calibrator_in_terminal(cmd_args)
