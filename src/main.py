# -*- coding: utf-8 -*-
import os
import sys
import traceback
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.utils.logger import setup_logger
from src.app import App

logger = setup_logger()


def run_app():
    GLib.set_prgname("extase-em-4r73")
    GLib.set_application_name("Extase em 4R73")

    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
    except Exception as e:
        logger.critical(f"GTK 3.0 nao encontrado: {e}")
        print("Verifique: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0", file=sys.stderr)
        sys.exit(1)

    app = None
    try:
        logger.info("Instanciando a classe App...")
        app = App(logger)
        if hasattr(app, 'initialization_failed') and app.initialization_failed:
            logger.error("Inicializacao da App falhou. Encerrando.")
            sys.exit(1)
        logger.info("Instanciacao da App concluida.")

    except Exception as e:
        logger.critical(f"Erro durante instanciacao da App: {e}")
        traceback.print_exc(file=sys.stderr)
        try:
            error_dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text="Erro Critico na Inicializacao"
            )
            error_dialog.format_secondary_text(f"Nao foi possivel instanciar a aplicacao:\n{e}")
            error_dialog.connect("response", lambda d, r: Gtk.main_quit())
            error_dialog.run()
            error_dialog.destroy()
        except Exception as gtk_err:
            logger.error(f"Nao foi possivel mostrar dialogo GTK: {gtk_err}")
        sys.exit(1)

    if app and hasattr(app, 'window') and app.window:
        try:
            logger.info("Iniciando loop principal GTK...")
            Gtk.main()
            logger.info("Loop principal GTK finalizado.")
        except KeyboardInterrupt:
            logger.info("Encerrando via Ctrl+C.")
            Gtk.main_quit()
        except Exception as e:
            logger.error(f"Erro no loop principal GTK: {e}")
            traceback.print_exc(file=sys.stderr)
            Gtk.main_quit()
    else:
        if not (hasattr(app, 'initialization_failed') and app.initialization_failed):
            logger.error("Falha ao inicializar a aplicacao. Encerrando.")
        sys.exit(1)


if __name__ == "__main__":
    run_app()


# "A liberdade e o reconhecimento de que nada e garantido." - Thomas Sowell
