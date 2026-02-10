# -*- coding: utf-8 -*-
from gi.repository import Gtk, GLib


class PostFXActionsMixin:

    def _init_postfx_widgets(self):
        self.chk_bloom = self.builder.get_object("chk_bloom_enabled")
        self.scale_bloom_intensity = self.builder.get_object("scale_bloom_intensity")
        self.spin_bloom_radius = self.builder.get_object("spin_bloom_radius")
        self.spin_bloom_threshold = self.builder.get_object("spin_bloom_threshold")

        self.chk_chromatic = self.builder.get_object("chk_chromatic_enabled")
        self.spin_chromatic_shift = self.builder.get_object("spin_chromatic_shift")

        self.chk_scanlines = self.builder.get_object("chk_scanlines_enabled")
        self.scale_scanlines_intensity = self.builder.get_object("scale_scanlines_intensity")
        self.spin_scanlines_spacing = self.builder.get_object("spin_scanlines_spacing")

        self.chk_glitch = self.builder.get_object("chk_glitch_enabled")
        self.scale_glitch_intensity = self.builder.get_object("scale_glitch_intensity")
        self.spin_glitch_block_size = self.builder.get_object("spin_glitch_block_size")

    def _load_postfx_config(self):
        if not hasattr(self, 'chk_bloom') or self.chk_bloom is None:
            return

        try:
            if self.chk_bloom:
                self.chk_bloom.set_active(
                    self.config.getboolean('PostFX', 'bloom_enabled', fallback=False)
                )
            if self.scale_bloom_intensity:
                self.scale_bloom_intensity.set_value(
                    self.config.getfloat('PostFX', 'bloom_intensity', fallback=0.3)
                )
            if self.spin_bloom_radius:
                self.spin_bloom_radius.set_value(
                    self.config.getint('PostFX', 'bloom_radius', fallback=5)
                )
            if self.spin_bloom_threshold:
                self.spin_bloom_threshold.set_value(
                    self.config.getint('PostFX', 'bloom_threshold', fallback=200)
                )

            if self.chk_chromatic:
                self.chk_chromatic.set_active(
                    self.config.getboolean('PostFX', 'chromatic_enabled', fallback=False)
                )
            if self.spin_chromatic_shift:
                self.spin_chromatic_shift.set_value(
                    self.config.getint('PostFX', 'chromatic_shift', fallback=2)
                )

            if self.chk_scanlines:
                self.chk_scanlines.set_active(
                    self.config.getboolean('PostFX', 'scanlines_enabled', fallback=False)
                )
            if self.scale_scanlines_intensity:
                self.scale_scanlines_intensity.set_value(
                    self.config.getfloat('PostFX', 'scanlines_intensity', fallback=0.3)
                )
            if self.spin_scanlines_spacing:
                self.spin_scanlines_spacing.set_value(
                    self.config.getint('PostFX', 'scanlines_spacing', fallback=2)
                )

            if self.chk_glitch:
                self.chk_glitch.set_active(
                    self.config.getboolean('PostFX', 'glitch_enabled', fallback=False)
                )
            if self.scale_glitch_intensity:
                self.scale_glitch_intensity.set_value(
                    self.config.getfloat('PostFX', 'glitch_intensity', fallback=0.1)
                )
            if self.spin_glitch_block_size:
                self.spin_glitch_block_size.set_value(
                    self.config.getint('PostFX', 'glitch_block_size', fallback=8)
                )

        except Exception as e:
            self.logger.warning(f"Erro ao carregar config PostFX: {e}")

    def _save_postfx_config(self):
        if not self.config.has_section('PostFX'):
            self.config.add_section('PostFX')

        if hasattr(self, 'chk_bloom') and self.chk_bloom:
            self.config.set('PostFX', 'bloom_enabled', str(self.chk_bloom.get_active()).lower())
        if hasattr(self, 'scale_bloom_intensity') and self.scale_bloom_intensity:
            self.config.set('PostFX', 'bloom_intensity', str(self.scale_bloom_intensity.get_value()))
        if hasattr(self, 'spin_bloom_radius') and self.spin_bloom_radius:
            self.config.set('PostFX', 'bloom_radius', str(int(self.spin_bloom_radius.get_value())))
        if hasattr(self, 'spin_bloom_threshold') and self.spin_bloom_threshold:
            self.config.set('PostFX', 'bloom_threshold', str(int(self.spin_bloom_threshold.get_value())))

        if hasattr(self, 'chk_chromatic') and self.chk_chromatic:
            self.config.set('PostFX', 'chromatic_enabled', str(self.chk_chromatic.get_active()).lower())
        if hasattr(self, 'spin_chromatic_shift') and self.spin_chromatic_shift:
            self.config.set('PostFX', 'chromatic_shift', str(int(self.spin_chromatic_shift.get_value())))

        if hasattr(self, 'chk_scanlines') and self.chk_scanlines:
            self.config.set('PostFX', 'scanlines_enabled', str(self.chk_scanlines.get_active()).lower())
        if hasattr(self, 'scale_scanlines_intensity') and self.scale_scanlines_intensity:
            self.config.set('PostFX', 'scanlines_intensity', str(self.scale_scanlines_intensity.get_value()))
        if hasattr(self, 'spin_scanlines_spacing') and self.spin_scanlines_spacing:
            self.config.set('PostFX', 'scanlines_spacing', str(int(self.spin_scanlines_spacing.get_value())))

        if hasattr(self, 'chk_glitch') and self.chk_glitch:
            self.config.set('PostFX', 'glitch_enabled', str(self.chk_glitch.get_active()).lower())
        if hasattr(self, 'scale_glitch_intensity') and self.scale_glitch_intensity:
            self.config.set('PostFX', 'glitch_intensity', str(self.scale_glitch_intensity.get_value()))
        if hasattr(self, 'spin_glitch_block_size') and self.spin_glitch_block_size:
            self.config.set('PostFX', 'glitch_block_size', str(int(self.spin_glitch_block_size.get_value())))

    def on_bloom_enabled_toggled(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_bloom_intensity_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_bloom_radius_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_bloom_threshold_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_chromatic_enabled_toggled(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_chromatic_shift_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_scanlines_enabled_toggled(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_scanlines_intensity_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_scanlines_spacing_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_glitch_enabled_toggled(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_glitch_intensity_changed(self, widget):
        self._save_postfx_config()
        self.save_config()

    def on_glitch_block_size_changed(self, widget):
        self._save_postfx_config()
        self.save_config()


# "A simplicidade e a sofisticacao suprema." - Leonardo da Vinci
