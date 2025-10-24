# #3. (CORRIGIDO) Importações voltam para o topo
import cv2
import numpy as np
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import os
import configparser
# import argparse # Não mais necessário
# import sys # Não mais necessário
# import time # Não mais necessário

# Definição de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(os.path.dirname(BASE_DIR), "ui", "calibrator.glade")

class CalibratorWindow(Gtk.Dialog):
    def __init__(self, parent, config, config_path, video_path=None):
        # (REMOVIDO) Importações atrasadas removidas daqui

        Gtk.Dialog.__init__(self, title="Calibrador de Chroma Key", transient_for=parent, flags=0)
        # ... (Restante do __init__ igual, usando cv2 e np diretamente) ...
        self.config = config; self.config_path = config_path
        self.builder = Gtk.Builder()
        try: self.builder.add_from_file(UI_FILE)
        except GLib.Error as e: print(f"Erro UI: {e}"); self.destroy(); return
        self.content_area = self.get_content_area(); self.main_box = self.builder.get_object("calibrator_box")
        self.content_area.add(self.main_box); self.builder.connect_signals(self)
        self.add_button("Salvar e Fechar", Gtk.ResponseType.OK); self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.connect("response", self.on_dialog_response)
        self.is_video_file = video_path is not None
        capture_source = video_path if self.is_video_file else 0
        self.cap = cv2.VideoCapture(capture_source)
        if not self.cap.isOpened():
            print(f"Erro: Não abriu: {capture_source}")
            error_dialog = Gtk.MessageDialog(transient_for=parent, flags=0, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CANCEL, text="Erro Vídeo/Webcam")
            error_dialog.format_secondary_text(f"Não foi possível acessar:\n{capture_source}"); error_dialog.run(); error_dialog.destroy()
            GLib.idle_add(self.destroy); return # Usamos idle_add para destruir após __init__ completar
        self.image_widget = self.builder.get_object("camera_image")
        self.sliders = {'h_min': self.builder.get_object("h_min"), 'h_max': self.builder.get_object("h_max"), 's_min': self.builder.get_object("s_min"), 's_max': self.builder.get_object("s_max"), 'v_min': self.builder.get_object("v_min"), 'v_max': self.builder.get_object("v_max")}
        self.load_initial_values()
        self.update_timer = GLib.timeout_add(100, self.update_frame)
        # self.show_all() # Não é necessário, o .run() no main.py cuida disso

    def load_initial_values(self):
        # ... (sem alterações) ...
        try:
            self.sliders['h_min'].set_value(self.config.getint('ChromaKey', 'h_min')); self.sliders['h_max'].set_value(self.config.getint('ChromaKey', 'h_max'))
            self.sliders['s_min'].set_value(self.config.getint('ChromaKey', 's_min')); self.sliders['s_max'].set_value(self.config.getint('ChromaKey', 's_max'))
            self.sliders['v_min'].set_value(self.config.getint('ChromaKey', 'v_min')); self.sliders['v_max'].set_value(self.config.getint('ChromaKey', 'v_max'))
        except Exception as e: print(f"Aviso Config: {e}"); self.sliders['h_min'].set_value(35); self.sliders['h_max'].set_value(85); self.sliders['s_min'].set_value(40); self.sliders['s_max'].set_value(255); self.sliders['v_min'].set_value(40); self.sliders['v_max'].set_value(255)

    def update_frame(self):
        # (REMOVIDO) Importações atrasadas removidas daqui
        # ... (Restante do update_frame igual) ...
        if not self.cap or not self.cap.isOpened(): return False
        ret, frame = self.cap.read()
        if not ret:
            if self.is_video_file: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); return True
            else: print("Erro webcam?"); GLib.source_remove(self.update_timer); self.update_timer = None; return False # Para o timer
        if frame is None or frame.size == 0: return True
        h_min=int(self.sliders['h_min'].get_value()); h_max=int(self.sliders['h_max'].get_value()); s_min=int(self.sliders['s_min'].get_value()); s_max=int(self.sliders['s_max'].get_value()); v_min=int(self.sliders['v_min'].get_value()); v_max=int(self.sliders['v_max'].get_value())
        lower = np.array([h_min, s_min, v_min]); upper = np.array([h_max, s_max, v_max])
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV); mask = cv2.inRange(hsv, lower, upper)
            result = cv2.bitwise_and(frame, frame, mask=mask); result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            h, w, c = result_rgb.shape
            if w > 0 and h > 0:
                pixbuf = GdkPixbuf.Pixbuf.new_from_data(result_rgb.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * c)
                alloc = self.image_widget.get_allocation(); scaled_pixbuf = pixbuf.scale_simple(alloc.width, alloc.height, GdkPixbuf.InterpType.BILINEAR)
                self.image_widget.set_from_pixbuf(scaled_pixbuf)
        except cv2.error as e: print(f"Erro OpenCV: {e}")
        except Exception as e: print(f"Erro update_frame: {e}"); return False
        return True

    def on_dialog_response(self, widget, response_id):
        # ... (sem alterações) ...
        if self.update_timer: GLib.source_remove(self.update_timer); self.update_timer = None
        if self.cap and self.cap.isOpened(): self.cap.release(); self.cap = None
        if response_id == Gtk.ResponseType.OK:
            try:
                self.config.set('ChromaKey','h_min',str(int(self.sliders['h_min'].get_value()))); self.config.set('ChromaKey','h_max',str(int(self.sliders['h_max'].get_value())))
                self.config.set('ChromaKey','s_min',str(int(self.sliders['s_min'].get_value()))); self.config.set('ChromaKey','s_max',str(int(self.sliders['s_max'].get_value())))
                self.config.set('ChromaKey','v_min',str(int(self.sliders['v_min'].get_value()))); self.config.set('ChromaKey','v_max',str(int(self.sliders['v_max'].get_value())))
                with open(self.config_path, 'w') as configfile: self.config.write(configfile)
                print(f"ChromaKey salvo em {self.config_path}")
            except Exception as e: print(f"Erro ao salvar config: {e}")
        self.destroy() # Destroi o diálogo

    # O método run() é chamado pelo src/main.py

# #3. (REMOVIDO) Bloco if __name__ == "__main__" removido
