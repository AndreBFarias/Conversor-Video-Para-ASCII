import logging
from collections.abc import Callable

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView

logger = logging.getLogger(__name__)


class ContextMenuItem(ListItem):
    def __init__(self, label: str, shortcut: str = "", callback: Callable | None = None, action: str = ""):
        super().__init__()
        self.label_text = label
        self.shortcut = shortcut
        self.callback = callback
        self.action = action or label.lower().replace(" ", "_")
        self.is_separator = label.startswith("---") or label.startswith("─")

        if self.is_separator:
            self.add_class("separator-item")

    def compose(self):
        if self.is_separator:
            yield Label("─" * 30, classes="context-menu-item-label")
        else:
            text = f"{self.label_text}"
            if self.shortcut:
                text += f"  [{self.shortcut}]"
            yield Label(text, classes="context-menu-item-label")


class ContextMenu(ModalScreen):
    CSS = """
    ContextMenu {
        align: left top;
        background: rgba(0, 0, 0, 0.5);
    }

    #context-menu-container {
        width: 32;
        height: auto;
        max-height: 15;
        background: #2d2f3d;
        border: solid #6272a4;
        padding: 0;
    }

    ContextMenuItem {
        padding: 0 1;
        height: 1;
        background: #2d2f3d;
    }

    ContextMenuItem:hover {
        background: #44475a;
    }

    ContextMenuItem:focus {
        background: #bd93f9;
        color: #282a36;
    }

    .context-menu-item-label {
        width: 100%;
    }

    .separator-item {
        color: #6272a4;
        height: 1;
    }

    .separator-item:hover {
        background: #2d2f3d;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Fechar", show=False),
        Binding("enter", "select_item", "Selecionar", show=False),
    ]

    def __init__(self, items: list[ContextMenuItem] | None = None, x: int = 0, y: int = 0):
        super().__init__()
        self.menu_x = x
        self.menu_y = y
        self.custom_items = items

    def compose(self):
        with Vertical(id="context-menu-container"):
            if self.custom_items:
                yield ListView(*self.custom_items, id="context-list")
            else:
                yield ListView(
                    ContextMenuItem("Copiar", "Ctrl+C", action="copy"),
                    ContextMenuItem("Colar", "Ctrl+V", action="paste"),
                    ContextMenuItem("Selecionar Tudo", "Ctrl+A", action="select_all"),
                    ContextMenuItem("---"),
                    ContextMenuItem("Nova Conversa", "Ctrl+T", action="nova_conversa"),
                    ContextMenuItem("Ver Historico", "Ctrl+H", action="ver_historico"),
                    ContextMenuItem("---"),
                    ContextMenuItem("Sair", "Ctrl+Q", action="quit"),
                    id="context-list",
                )

    def on_mount(self) -> None:
        container = self.query_one("#context-menu-container")
        if self.menu_x > 0 or self.menu_y > 0:
            container.styles.margin = (self.menu_y, 0, 0, self.menu_x)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ContextMenuItem):
            if item.is_separator:
                return

            self.dismiss()

            if item.callback:
                self.app.call_later(item.callback)
            elif item.action:
                action_method = getattr(self.app, f"action_{item.action}", None)
                if action_method:
                    self.app.call_later(action_method)

    def action_select_item(self) -> None:
        try:
            listview = self.query_one("#context-list", ListView)
            if listview.highlighted_child:
                item = listview.highlighted_child
                if isinstance(item, ContextMenuItem) and not item.is_separator:
                    self.dismiss()
                    if item.callback:
                        self.app.call_later(item.callback)
                    elif item.action:
                        action_method = getattr(self.app, f"action_{item.action}", None)
                        if action_method:
                            self.app.call_later(action_method)
        except Exception as e:
            logger.debug(f"Erro ao selecionar item do menu de contexto: {e}")

    def action_dismiss(self) -> None:
        self.dismiss()

    def on_click(self, event) -> None:
        try:
            container = self.query_one("#context-menu-container")
            if not container.region.contains(event.screen_x, event.screen_y):
                self.dismiss()
        except Exception as e:
            logger.debug(f"Erro ao verificar clique fora do menu: {e}")
            self.dismiss()
