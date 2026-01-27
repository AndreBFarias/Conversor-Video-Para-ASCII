import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..constants import QUALITY_PRESETS, BIT_PRESETS, DEFAULT_LUMINANCE_RAMP, LUMINANCE_RAMPS, FIXED_PALETTES, STYLE_PRESETS


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
            self.opt_fixed_palette_check.connect("toggled", self.on_fixed_palette_toggled)

            fixed_palette_label = Gtk.Label(label="Paleta Fixa:")
            fixed_palette_label.set_halign(Gtk.Align.START)
            self.opt_fixed_palette_combo = Gtk.ComboBoxText()
            for palette_id, palette_data in FIXED_PALETTES.items():
                self.opt_fixed_palette_combo.append(palette_id, palette_data['name'])
            self.opt_fixed_palette_combo.set_active(0)
            self.opt_fixed_palette_combo.set_sensitive(False)

            pixelart_grid.attach(bit_preset_label, 0, 0, 1, 1)
            pixelart_grid.attach(self.opt_bit_preset_combo, 1, 0, 1, 1)
            pixelart_grid.attach(pixel_size_label, 0, 1, 1, 1)
            pixelart_grid.attach(self.opt_pixel_size_spin, 1, 1, 1, 1)
            pixelart_grid.attach(palette_size_label, 0, 2, 1, 1)
            pixelart_grid.attach(self.opt_palette_size_spin, 1, 2, 1, 1)
            pixelart_grid.attach(self.opt_fixed_palette_check, 0, 3, 2, 1)
            pixelart_grid.attach(fixed_palette_label, 0, 4, 1, 1)
            pixelart_grid.attach(self.opt_fixed_palette_combo, 1, 4, 1, 1)

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
            self.quality_combo = self.builder.get_object("quality_combo")
            self.radio_mode_ascii = self.builder.get_object("radio_mode_ascii")
            self.radio_mode_pixelart = self.builder.get_object("radio_mode_pixelart")

            if self.quality_combo:
                current_preset = self.config.get('Quality', 'preset', fallback='custom')
                preset_map = {'custom': 0, 'mobile': 1, 'low': 2, 'medium': 3, 'high': 4, 'veryhigh': 5}
                self.quality_combo.set_active(preset_map.get(current_preset, 0))

            if self.radio_mode_ascii and self.radio_mode_pixelart:
                current_mode = self.config.get('Mode', 'conversion_mode', fallback='ascii')
                if current_mode == 'pixelart':
                    self.radio_mode_pixelart.set_active(True)
                else:
                    self.radio_mode_ascii.set_active(True)

        except Exception as e:
            self.logger.error(f"Erro ao configurar combos: {e}")

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

    def on_quality_combo_changed(self, combo):
        active = combo.get_active()
        preset_names = ['custom', 'mobile', 'low', 'medium', 'high', 'veryhigh']

        if 0 <= active < len(preset_names):
            preset_id = preset_names[active]

            if preset_id == 'custom':
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
                    self.logger.info(f"Preset de qualidade alterado: {preset_id}")
            except Exception as e:
                self.logger.error(f"Erro ao aplicar preset: {e}")

    def on_mode_combo_changed(self, combo):
        active = combo.get_active()
        mode = 'ascii' if active == 0 else 'pixelart'

        try:
            if 'Mode' not in self.config:
                self.config.add_section('Mode')
            self.config.set('Mode', 'conversion_mode', mode)
            self.save_config()
            self.logger.info(f"Modo de conversao alterado: {mode}")
        except Exception as e:
            self.logger.error(f"Erro ao alterar modo: {e}")

    def on_mode_radio_toggled(self, radio):
        if not radio.get_active():
            return

        mode = 'ascii' if radio == self.radio_mode_ascii else 'pixelart'

        try:
            if 'Mode' not in self.config:
                self.config.add_section('Mode')
            self.config.set('Mode', 'conversion_mode', mode)
            self.save_config()
            self.logger.info(f"Modo de conversao alterado: {mode}")
        except Exception as e:
            self.logger.error(f"Erro ao alterar modo: {e}")

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

    def on_luminance_preset_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id:
            return

        if preset_id == 'custom':
            if hasattr(self, 'opt_luminance_entry') and self.opt_luminance_entry:
                self.opt_luminance_entry.set_sensitive(True)
            return

        if preset_id in LUMINANCE_RAMPS:
            ramp = LUMINANCE_RAMPS[preset_id]['ramp']
            if hasattr(self, 'opt_luminance_entry') and self.opt_luminance_entry:
                self.opt_luminance_entry.set_text(ramp)
                self.opt_luminance_entry.set_sensitive(False)

    def on_fixed_palette_toggled(self, check):
        is_active = check.get_active()
        if hasattr(self, 'opt_fixed_palette_combo') and self.opt_fixed_palette_combo:
            self.opt_fixed_palette_combo.set_sensitive(is_active)

    def on_pref_style_combo_changed(self, combo):
        preset_id = combo.get_active_id()
        if not preset_id or preset_id not in STYLE_PRESETS:
            return

        preset = STYLE_PRESETS[preset_id]
        
        # Aplicar valores nos widgets
        if hasattr(self, 'opt_sobel_spin') and self.opt_sobel_spin:
             self.opt_sobel_spin.set_value(preset['sobel'])
             
        if hasattr(self, 'opt_aspect_spin') and self.opt_aspect_spin:
             self.opt_aspect_spin.set_value(preset['aspect'])
             
        if 'sharpen_amount' in preset:
             # Sharpen nao tem spin na UI padrao das options?
             # Se nao tiver, setamos no config direto ao salvar, ou ignoramos visualmente?
             # O Session Summary diz "sharpen_enabled = True" e "sharpen_amount = 0.5" 
             # Mas nao vi widget para sharpen no view_file do options_actions.py (soh sobel e aspect)
             # Vamos assumir que soh sobel/aspect/luminance estao expostos
             pass
             
        if hasattr(self, 'opt_luminance_entry') and self.opt_luminance_entry:
             self.opt_luminance_entry.set_text(preset['luminance_ramp'])

    def on_options_button_clicked(self, widget):
        try:
            self._check_config_reload()
            self.reload_config()

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

            luminance_val = self.config.get('Conversor', 'luminance_ramp', fallback=DEFAULT_LUMINANCE_RAMP).rstrip('|')
            luminance_preset = self.config.get('Conversor', 'luminance_preset', fallback='standard')
            self.opt_luminance_entry.set_text(luminance_val)

            if hasattr(self, 'opt_luminance_preset_combo') and self.opt_luminance_preset_combo:
                preset_map = {
                    'standard': 0, 'simple': 1, 'blocks': 2, 'minimal': 3,
                    'binary': 4, 'dots': 5, 'detailed': 6, 'letters': 7,
                    'numbers': 8, 'arrows': 9, 'custom': 10
                }
                self.opt_luminance_preset_combo.set_active(preset_map.get(luminance_preset, 0))
                self.opt_luminance_entry.set_sensitive(luminance_preset == 'custom')

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
            fixed_palette_name = self.config.get('PixelArt', 'fixed_palette_name', fallback='gameboy')

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
                if hasattr(self, 'opt_fixed_palette_combo') and self.opt_fixed_palette_combo:
                    palette_keys = list(FIXED_PALETTES.keys())
                    if fixed_palette_name in palette_keys:
                        self.opt_fixed_palette_combo.set_active(palette_keys.index(fixed_palette_name))
                    self.opt_fixed_palette_combo.set_sensitive(fixed_palette_val)

            clear_screen = self.config.getboolean('Player', 'clear_screen', fallback=True)
            show_fps = self.config.getboolean('Player', 'show_fps', fallback=False)
            speed = self.config.get('Player', 'speed', fallback='1.0')

            if hasattr(self, 'opt_clear_screen_check') and self.opt_clear_screen_check:
                self.opt_clear_screen_check.set_active(clear_screen)
            if hasattr(self, 'opt_show_fps_check') and self.opt_show_fps_check:
                self.opt_show_fps_check.set_active(show_fps)
            if hasattr(self, 'opt_speed_combo') and self.opt_speed_combo:
                speed_map = {'0.5': 0, '0.75': 1, '1.0': 2, '1.25': 3, '1.5': 4, '2.0': 5}
                self.opt_speed_combo.set_active(speed_map.get(speed, 2))

            if hasattr(self, 'pref_input_folder') and self.pref_input_folder:
                self.pref_input_folder.set_current_folder(self.input_dir)
            if hasattr(self, 'pref_output_folder') and self.pref_output_folder:
                self.pref_output_folder.set_current_folder(self.output_dir)

            if hasattr(self, 'pref_engine_combo') and self.pref_engine_combo:
                engine = self.config.get('Mode', 'conversion_mode', fallback='ascii')
                self.pref_engine_combo.set_active(0 if engine == 'ascii' else 1)

            if hasattr(self, 'pref_quality_combo') and self.pref_quality_combo:
                quality = self.config.get('Quality', 'preset', fallback='custom')
                quality_map = {'custom': 0, 'mobile': 1, 'low': 2, 'medium': 3, 'high': 4, 'veryhigh': 5}
                self.pref_quality_combo.set_active(quality_map.get(quality, 0))

            if hasattr(self, 'pref_format_combo') and self.pref_format_combo:
                fmt = self.config.get('Output', 'format', fallback='txt')
                fmt_map = {'txt': 0, 'mp4': 1, 'gif': 2, 'html': 3}
                self.pref_format_combo.set_active(fmt_map.get(fmt, 0))

            if hasattr(self, 'pref_theme_combo') and self.pref_theme_combo:
                current_theme = self.config.get('Interface', 'theme', fallback='dark')
                self.pref_theme_combo.set_active_id(current_theme)

            if hasattr(self, 'pref_gpu_switch') and self.pref_gpu_switch:
                gpu_enabled = self.config.getboolean('Conversor', 'gpu_enabled', fallback=True)
                self.pref_gpu_switch.set_active(gpu_enabled)
                
            if hasattr(self, 'pref_render_mode_combo') and self.pref_render_mode_combo:
                render_mode = self.config.get('Conversor', 'gpu_render_mode', fallback='fast')
                self.pref_render_mode_combo.set_active_id(render_mode) or self.pref_render_mode_combo.set_active(0)

            if hasattr(self, 'pref_braille_switch') and self.pref_braille_switch:
                braille_enabled = self.config.getboolean('Conversor', 'braille_enabled', fallback=False)
                self.pref_braille_switch.set_active(braille_enabled)

            if hasattr(self, 'pref_braille_threshold_scale') and self.pref_braille_threshold_scale:
                braille_threshold = self.config.getint('Conversor', 'braille_threshold', fallback=128)
                self.pref_braille_threshold_scale.set_value(braille_threshold)

            if hasattr(self, 'pref_temporal_switch') and self.pref_temporal_switch:
                temporal_enabled = self.config.getboolean('Conversor', 'temporal_coherence_enabled', fallback=False)
                self.pref_temporal_switch.set_active(temporal_enabled)

            if hasattr(self, 'pref_temporal_threshold_scale') and self.pref_temporal_threshold_scale:
                temporal_threshold = self.config.getint('Conversor', 'temporal_threshold', fallback=20)
                self.pref_temporal_threshold_scale.set_value(temporal_threshold)

            if hasattr(self, 'pref_async_switch') and self.pref_async_switch:
                async_enabled = self.config.getboolean('Conversor', 'gpu_async_enabled', fallback=True)
                self.pref_async_switch.set_active(async_enabled)

            if hasattr(self, 'pref_async_num_streams_spin') and self.pref_async_num_streams_spin:
                num_streams = self.config.getint('Conversor', 'gpu_async_num_streams', fallback=4)
                self.pref_async_num_streams_spin.set_value(num_streams)

            if hasattr(self, 'pref_auto_seg_switch') and self.pref_auto_seg_switch:
                auto_seg_enabled = self.config.getboolean('Conversor', 'auto_seg_enabled', fallback=False)
                self.pref_auto_seg_switch.set_active(auto_seg_enabled)

            if hasattr(self, 'opt_edge_boost_check') and self.opt_edge_boost_check:
                edge_boost_enabled = self.config.getboolean('Conversor', 'edge_boost_enabled', fallback=False)
                self.opt_edge_boost_check.set_active(edge_boost_enabled)

            if hasattr(self, 'opt_edge_boost_spin') and self.opt_edge_boost_spin:
                edge_boost_amount = self.config.getint('Conversor', 'edge_boost_amount', fallback=100)
                self.opt_edge_boost_spin.set_value(edge_boost_amount)
                self.opt_edge_boost_spin.set_sensitive(self.opt_edge_boost_check.get_active() if self.opt_edge_boost_check else True)

            if hasattr(self, 'opt_use_edge_chars_check') and self.opt_use_edge_chars_check:
                use_edge_chars = self.config.getboolean('Conversor', 'use_edge_chars', fallback=True)
                self.opt_use_edge_chars_check.set_active(use_edge_chars)

            if hasattr(self, 'opt_font_detection_switch') and self.opt_font_detection_switch:
                font_detection = self.config.getboolean('Preview', 'font_detection_enabled', fallback=True)
                self.opt_font_detection_switch.set_active(font_detection)

            if hasattr(self, 'opt_font_family_combo') and self.opt_font_family_combo:
                from src.utils.terminal_font_detector import list_monospace_fonts

                self.opt_font_family_combo.remove_all()

                self.opt_font_family_combo.append_text('auto')

                available_fonts = list_monospace_fonts()
                for font in available_fonts:
                    self.opt_font_family_combo.append_text(font)

                font_family = self.config.get('Preview', 'font_family', fallback='auto')
                entry = self.opt_font_family_combo.get_child()
                if entry:
                    entry.set_text(font_family)

            if hasattr(self, 'opt_font_size_spin') and self.opt_font_size_spin:
                font_size_str = self.config.get('Preview', 'font_size', fallback='auto')
                if font_size_str == 'auto':
                    self.opt_font_size_spin.set_value(12)
                else:
                    try:
                        font_size = int(font_size_str)
                        self.opt_font_size_spin.set_value(font_size)
                    except ValueError:
                        self.opt_font_size_spin.set_value(12)

            if hasattr(self, 'pref_style_combo') and self.pref_style_combo:
                style = self.config.get('Conversor', 'style_preset', fallback='clean')
                # Map style IDs to combo index? Or use set_active_id for ComboBoxText
                # GtkComboBoxText supports set_active_id
                if not self.pref_style_combo.set_active_id(style):
                    self.pref_style_combo.set_active(0) # Default to first if fail
                
                # Connect signal manually (disconnect first to avoid duplicates if re-opened?)
                # Gtk signals don't automatically deduplicate. 
                # Simpler: id = connect(). Store id? 
                # Or just don't worry too much for now, or check if connected.
                try:
                    self.pref_style_combo.disconnect_by_func(self.on_pref_style_combo_changed)
                except:
                    pass
                self.pref_style_combo.connect("changed", self.on_pref_style_combo_changed)

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

        if hasattr(self, 'opt_clear_screen_check') and self.opt_clear_screen_check:
            self.opt_clear_screen_check.set_active(True)
        if hasattr(self, 'opt_show_fps_check') and self.opt_show_fps_check:
            self.opt_show_fps_check.set_active(False)
        if hasattr(self, 'opt_speed_combo') and self.opt_speed_combo:
            self.opt_speed_combo.set_active(2)

        if hasattr(self, 'pref_engine_combo') and self.pref_engine_combo:
            self.pref_engine_combo.set_active(0)
        if hasattr(self, 'pref_quality_combo') and self.pref_quality_combo:
            self.pref_quality_combo.set_active(0)
        if hasattr(self, 'pref_format_combo') and self.pref_format_combo:
            self.pref_format_combo.set_active(0)

        if hasattr(self, 'pref_theme_combo') and self.pref_theme_combo:
            self.pref_theme_combo.set_active_id('dark')

            
        if hasattr(self, 'pref_gpu_switch') and self.pref_gpu_switch:
            self.pref_gpu_switch.set_active(False)

        if hasattr(self, 'opt_luminance_preset_combo') and self.opt_luminance_preset_combo:
            self.opt_luminance_preset_combo.set_active(0)
            self.opt_luminance_entry.set_sensitive(False)

        if hasattr(self, 'opt_edge_boost_check') and self.opt_edge_boost_check:
            self.opt_edge_boost_check.set_active(False)
        if hasattr(self, 'opt_edge_boost_spin') and self.opt_edge_boost_spin:
            self.opt_edge_boost_spin.set_value(100)
            self.opt_edge_boost_spin.set_sensitive(False)
        if hasattr(self, 'opt_use_edge_chars_check') and self.opt_use_edge_chars_check:
            self.opt_use_edge_chars_check.set_active(True)

        if hasattr(self, 'opt_fixed_palette_combo') and self.opt_fixed_palette_combo:
            self.opt_fixed_palette_combo.set_active(0)
            self.opt_fixed_palette_combo.set_sensitive(False)
        if hasattr(self, 'opt_fixed_palette_check') and self.opt_fixed_palette_check:
            self.opt_fixed_palette_check.set_active(False)

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

            if hasattr(self, 'pref_gpu_switch') and self.pref_gpu_switch:
                gpu_enabled = self.pref_gpu_switch.get_active()
                self.config.set('Conversor', 'gpu_enabled', 'true' if gpu_enabled else 'false')

            if hasattr(self, 'pref_render_mode_combo') and self.pref_render_mode_combo:
                render_mode = self.pref_render_mode_combo.get_active_id() or 'fast'
                self.config.set('Conversor', 'gpu_render_mode', render_mode)

            if hasattr(self, 'pref_braille_switch') and self.pref_braille_switch:
                braille_enabled = self.pref_braille_switch.get_active()
                self.config.set('Conversor', 'braille_enabled', 'true' if braille_enabled else 'false')

            if hasattr(self, 'pref_braille_threshold_scale') and self.pref_braille_threshold_scale:
                braille_threshold = int(self.pref_braille_threshold_scale.get_value())
                self.config.set('Conversor', 'braille_threshold', str(braille_threshold))

            if hasattr(self, 'pref_temporal_switch') and self.pref_temporal_switch:
                temporal_enabled = self.pref_temporal_switch.get_active()
                self.config.set('Conversor', 'temporal_coherence_enabled', 'true' if temporal_enabled else 'false')

            if hasattr(self, 'pref_temporal_threshold_scale') and self.pref_temporal_threshold_scale:
                temporal_threshold = int(self.pref_temporal_threshold_scale.get_value())
                self.config.set('Conversor', 'temporal_threshold', str(temporal_threshold))

            if hasattr(self, 'pref_async_switch') and self.pref_async_switch:
                async_enabled = self.pref_async_switch.get_active()
                self.config.set('Conversor', 'gpu_async_enabled', 'true' if async_enabled else 'false')

            if hasattr(self, 'pref_async_num_streams_spin') and self.pref_async_num_streams_spin:
                num_streams = int(self.pref_async_num_streams_spin.get_value())
                self.config.set('Conversor', 'gpu_async_num_streams', str(num_streams))

            if hasattr(self, 'pref_auto_seg_switch') and self.pref_auto_seg_switch:
                auto_seg_enabled = self.pref_auto_seg_switch.get_active()
                self.config.set('Conversor', 'auto_seg_enabled', 'true' if auto_seg_enabled else 'false')

            if hasattr(self, 'opt_edge_boost_check') and self.opt_edge_boost_check:
                edge_boost_enabled = self.opt_edge_boost_check.get_active()
                self.config.set('Conversor', 'edge_boost_enabled', 'true' if edge_boost_enabled else 'false')

            if hasattr(self, 'opt_edge_boost_spin') and self.opt_edge_boost_spin:
                edge_boost_amount = int(self.opt_edge_boost_spin.get_value())
                self.config.set('Conversor', 'edge_boost_amount', str(edge_boost_amount))

            if hasattr(self, 'opt_use_edge_chars_check') and self.opt_use_edge_chars_check:
                use_edge_chars = self.opt_use_edge_chars_check.get_active()
                self.config.set('Conversor', 'use_edge_chars', 'true' if use_edge_chars else 'false')

            if 'Preview' not in self.config:
                self.config.add_section('Preview')

            if hasattr(self, 'opt_font_detection_switch') and self.opt_font_detection_switch:
                font_detection = self.opt_font_detection_switch.get_active()
                self.config.set('Preview', 'font_detection_enabled', 'true' if font_detection else 'false')

            if hasattr(self, 'opt_font_family_combo') and self.opt_font_family_combo:
                entry = self.opt_font_family_combo.get_child()
                if entry:
                    font_family = entry.get_text().strip()
                else:
                    font_family = self.opt_font_family_combo.get_active_text() or 'auto'

                if not font_family:
                    font_family = 'auto'
                self.config.set('Preview', 'font_family', font_family)

            if hasattr(self, 'opt_font_size_spin') and self.opt_font_size_spin:
                font_size = int(self.opt_font_size_spin.get_value())
                self.config.set('Preview', 'font_size', str(font_size))

            if hasattr(self, 'opt_luminance_preset_combo') and self.opt_luminance_preset_combo:
                preset_id = self.opt_luminance_preset_combo.get_active_id()
                if preset_id:
                    self.config.set('Conversor', 'luminance_preset', preset_id)

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

                if hasattr(self, 'opt_fixed_palette_combo') and self.opt_fixed_palette_combo:
                    palette_id = self.opt_fixed_palette_combo.get_active_id()
                    if palette_id:
                        self.config.set('PixelArt', 'fixed_palette_name', palette_id)

            if hasattr(self, 'opt_clear_screen_check') and self.opt_clear_screen_check:
                self.config.set('Player', 'clear_screen', 'true' if self.opt_clear_screen_check.get_active() else 'false')
            if hasattr(self, 'opt_show_fps_check') and self.opt_show_fps_check:
                self.config.set('Player', 'show_fps', 'true' if self.opt_show_fps_check.get_active() else 'false')
            if hasattr(self, 'opt_speed_combo') and self.opt_speed_combo:
                speed_list = ['0.5', '0.75', '1.0', '1.25', '1.5', '2.0']
                active = self.opt_speed_combo.get_active()
                if 0 <= active < len(speed_list):
                    self.config.set('Player', 'speed', speed_list[active])

            if hasattr(self, 'pref_input_folder') and self.pref_input_folder:
                folder = self.pref_input_folder.get_filename()
                if folder:
                    if 'Pastas' not in self.config:
                        self.config.add_section('Pastas')
                    self.config.set('Pastas', 'input_dir', folder)
                    self.input_dir = folder

            if hasattr(self, 'pref_output_folder') and self.pref_output_folder:
                folder = self.pref_output_folder.get_filename()
                if folder:
                    if 'Pastas' not in self.config:
                        self.config.add_section('Pastas')
                    self.config.set('Pastas', 'output_dir', folder)
                    self.output_dir = folder

            if hasattr(self, 'pref_engine_combo') and self.pref_engine_combo:
                if 'Mode' not in self.config:
                    self.config.add_section('Mode')
                engine = 'ascii' if self.pref_engine_combo.get_active() == 0 else 'pixelart'
                self.config.set('Mode', 'conversion_mode', engine)
                if hasattr(self, 'radio_mode_ascii') and self.radio_mode_ascii:
                    if engine == 'ascii':
                        self.radio_mode_ascii.set_active(True)
                    else:
                        self.radio_mode_pixelart.set_active(True)

            if hasattr(self, 'pref_quality_combo') and self.pref_quality_combo:
                if 'Quality' not in self.config:
                    self.config.add_section('Quality')
                quality_list = ['custom', 'mobile', 'low', 'medium', 'high', 'veryhigh']
                active = self.pref_quality_combo.get_active()
                if 0 <= active < len(quality_list):
                    self.config.set('Quality', 'preset', quality_list[active])
                    if hasattr(self, 'quality_combo') and self.quality_combo:
                        self.quality_combo.set_active(active)

            if hasattr(self, 'pref_style_combo') and self.pref_style_combo:
                style_id = self.pref_style_combo.get_active_id()
                if style_id:
                     self.config.set('Conversor', 'style_preset', style_id)
                     # Apply hidden properties form style preset (sharpen)
                     if style_id in STYLE_PRESETS:
                         preset = STYLE_PRESETS[style_id]
                         if 'sharpen_amount' in preset:
                             self.config.set('Conversor', 'sharpen_amount', str(preset['sharpen_amount']))

            if hasattr(self, 'pref_format_combo') and self.pref_format_combo:
                if 'Output' not in self.config:
                    self.config.add_section('Output')
                fmt_list = ['txt', 'mp4', 'gif', 'html']
                if 0 <= active < len(fmt_list):
                    self.config.set('Output', 'format', fmt_list[active])

            if hasattr(self, 'pref_theme_combo') and self.pref_theme_combo:
                current_theme_id = self.pref_theme_combo.get_active_id()
                if current_theme_id:
                    if 'Interface' not in self.config:
                        self.config.add_section('Interface')
                    self.config.set('Interface', 'theme', current_theme_id)

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

        self._launch_gtk_calibrator(cmd_args)

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

        self._launch_gtk_calibrator(cmd_args)
