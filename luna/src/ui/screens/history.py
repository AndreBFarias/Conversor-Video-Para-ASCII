from __future__ import annotations

import logging

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from src.soul.personalidade import get_personalidade
from src.ui.screens.base import GlitchLabel

logger = logging.getLogger(__name__)


class HistoryScreen(Screen):
    BINDINGS = [
        Binding(key="escape", action="app.pop_screen", description="Voltar"),
        Binding(key="enter", action="select_session", description="Selecionar"),
        Binding(key="space", action="select_session", description="Selecionar"),
        Binding(key="up", action="focus_previous", description="Anterior"),
        Binding(key="down", action="focus_next", description="Proximo"),
        Binding(key="j", action="focus_next", description="Proximo"),
        Binding(key="k", action="focus_previous", description="Anterior"),
        Binding(key="f5", action="app.nova_conversa", description="Nova Conversa"),
        Binding(key="/", action="focus_search", description="Buscar"),
        Binding(key="d", action="delete_session", description="Deletar"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history_manager = None
        self._current_sessions = []

    def action_select_session(self) -> None:
        try:
            list_view = self.query_one("#history-list", ListView)
            if list_view.highlighted_child and hasattr(list_view.highlighted_child, "session_id"):
                self.dismiss(list_view.highlighted_child.session_id)
        except Exception as e:
            logger.debug(f"Erro ao selecionar sessao: {e}")

    def action_focus_next(self) -> None:
        try:
            list_view = self.query_one("#history-list", ListView)
            list_view.action_cursor_down()
        except Exception as e:
            logger.debug(f"Erro ao focar proximo item: {e}")

    def action_focus_previous(self) -> None:
        try:
            list_view = self.query_one("#history-list", ListView)
            list_view.action_cursor_up()
        except Exception as e:
            logger.debug(f"Erro ao focar item anterior: {e}")

    def action_focus_search(self) -> None:
        try:
            search_input = self.query_one("#history-search", Input)
            search_input.focus()
        except Exception as e:
            logger.debug(f"Erro ao focar campo de busca: {e}")

    def action_delete_session(self) -> None:
        try:
            list_view = self.query_one("#history-list", ListView)
            if list_view.highlighted_child and hasattr(list_view.highlighted_child, "session_id"):
                session_id = list_view.highlighted_child.session_id
                if self._history_manager and self._history_manager.delete_session(session_id):
                    self._refresh_list()
        except Exception as e:
            logger.debug(f"Erro ao deletar sessao: {e}")

    def compose(self) -> ComposeResult:
        with Vertical(id="history-container"):
            with Horizontal(id="history-header"):
                yield Static("Biblioteca das Palavras Conjuradas", id="history-title")
            yield Input(placeholder="Buscar conversas...", id="history-search")
            yield ListView(id="history-list")
            with Horizontal(id="history-footer"):
                yield Button("Eterno Retorno", id="back-button")
                yield Static("[dim]/ buscar | d deletar | Enter selecionar[/dim]", id="history-hints")

    def on_mount(self) -> None:
        from src.core.session_history import get_session_history

        self._history_manager = get_session_history()
        self._refresh_list()

    def _refresh_list(self, query: str = "") -> None:
        from src.core.session_history import TimeGroup

        personalidade = get_personalidade()
        list_view = self.query_one("#history-list", ListView)
        list_view.clear()

        if query:
            sessions = self._history_manager.search_sessions(query)
            self._current_sessions = sessions
            if not sessions:
                list_view.append(ListItem(Label("[dim]Nenhum resultado encontrado[/dim]", classes="empty-message")))
            else:
                for session in sessions:
                    self._add_session_item(list_view, session)
        else:
            grouped = self._history_manager.get_sessions_grouped(force_refresh=True)
            self._current_sessions = []

            for group in [
                TimeGroup.TODAY,
                TimeGroup.YESTERDAY,
                TimeGroup.THIS_WEEK,
                TimeGroup.THIS_MONTH,
                TimeGroup.OLDER,
            ]:
                sessions = grouped.get(group, [])
                if sessions:
                    list_view.append(
                        ListItem(Label(f"[bold magenta]--- {group.value} ---[/bold magenta]", classes="group-header"))
                    )
                    for session in sessions:
                        self._add_session_item(list_view, session)
                        self._current_sessions.append(session)

            if not self._current_sessions:
                msg = personalidade.obter_frase("biblioteca_vazia")
                list_view.append(ListItem(Label(msg, classes="empty-message")))

    def _add_session_item(self, list_view: ListView, session) -> None:
        title = escape(session.title)
        date_str = session.date.strftime("%d/%m %H:%M")
        preview = escape(session.preview[:50]) if session.preview else ""
        msg_count = f"[dim]{session.message_count} msgs[/dim]" if session.message_count else ""

        display_text = f"[b]{title}[/b] {msg_count}\n[dim]{date_str}[/dim]"
        if preview:
            display_text += f" | [italic]{preview}...[/italic]"

        item = ListItem(GlitchLabel(display_text))
        item.session_id = session.session_id
        list_view.append(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "history-search":
            self._refresh_list(event.value)

    def on_list_view_selected(self, event: ListView.Selected):
        if hasattr(event.item, "session_id"):
            self.dismiss(event.item.session_id)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back-button":
            self.app.pop_screen()
