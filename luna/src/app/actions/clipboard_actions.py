import logging
from typing import TYPE_CHECKING

import pyperclip

from src.ui import ChatMessage, MultilineInput
from src.ui.glitch_button import GlitchButton

if TYPE_CHECKING:
    from ..luna_app import TemploDaAlma

logger = logging.getLogger(__name__)


class ClipboardActionsMixin:
    def action_copy(self: "TemploDaAlma") -> None:
        focused = self.focused
        if hasattr(focused, "selected_text") and focused.selected_text:
            try:
                pyperclip.copy(focused.selected_text)
                self.notify("Copiado!", timeout=1)
                logger.debug("Texto copiado para clipboard")
            except Exception as e:
                logger.error(f"Erro ao copiar: {e}")
                self.notify("Erro ao copiar", severity="error", timeout=2)
        elif hasattr(focused, "value") and focused.value:
            try:
                pyperclip.copy(focused.value)
                self.notify("Copiado!", timeout=1)
                logger.debug("Valor do input copiado")
            except Exception as e:
                logger.error(f"Erro ao copiar: {e}")

    def action_paste(self: "TemploDaAlma") -> None:
        try:
            text = pyperclip.paste()
            if text:
                main_input = self.query_one("#main_input", MultilineInput)
                main_input.insert_text_at_cursor(text)
                logger.debug(f"Texto colado: {len(text)} caracteres")
        except Exception as e:
            logger.error(f"Erro ao colar: {e}")
            self.notify("Erro ao colar", severity="error", timeout=2)

    def action_select_all(self: "TemploDaAlma") -> None:
        focused = self.focused
        if focused and hasattr(focused, "id"):
            if focused.id == "chat-list" or "chat" in str(type(focused)):
                self._select_all_chat_messages()
                return
        try:
            main_input = self.query_one("#main_input", MultilineInput)
            main_input.action_select_all()
            logger.debug("Selecionado todo o texto do input")
        except Exception as e:
            logger.debug(f"Nao foi possivel selecionar tudo: {e}")

    def _select_all_chat_messages(self: "TemploDaAlma") -> None:
        try:
            chat_list = self.query_one("#chat-list")
            messages = chat_list.query(ChatMessage)
            all_text = []
            for msg in messages:
                all_text.append(msg.get_text_content())
            if all_text:
                full_text = "\n\n".join(all_text)
                pyperclip.copy(full_text)
                self.notify("Todas as mensagens copiadas", timeout=2)
                logger.debug(f"Copiadas {len(all_text)} mensagens")
        except Exception as e:
            logger.error(f"Erro ao selecionar todas mensagens: {e}")

    def action_focus_next_block(self: "TemploDaAlma") -> None:
        focus_order = ["#menu-pane", "#chat-list", "#main_input", "#input-container"]
        current_focused = self.focused
        current_block = None

        for block_id in focus_order:
            try:
                block = self.query_one(block_id)
                if current_focused and (current_focused == block or block.is_ancestor_of(current_focused)):
                    current_block = block_id
                    break
            except Exception:
                continue

        if current_block:
            current_idx = focus_order.index(current_block)
            next_idx = (current_idx + 1) % len(focus_order)
        else:
            next_idx = 0

        for i in range(len(focus_order)):
            try_idx = (next_idx + i) % len(focus_order)
            try:
                next_block = self.query_one(focus_order[try_idx])
                if focus_order[try_idx] == "#menu-pane":
                    first_btn = next_block.query_one(GlitchButton)
                    if first_btn:
                        first_btn.focus()
                        return
                elif focus_order[try_idx] == "#input-container":
                    input_field = self.query_one("#main_input", MultilineInput)
                    input_field.focus()
                    return
                else:
                    next_block.focus()
                    return
            except Exception:
                continue

    def action_focus_prev_block(self: "TemploDaAlma") -> None:
        focus_order = ["#menu-pane", "#chat-list", "#main_input", "#input-container"]
        current_focused = self.focused
        current_block = None

        for block_id in focus_order:
            try:
                block = self.query_one(block_id)
                if current_focused and (current_focused == block or block.is_ancestor_of(current_focused)):
                    current_block = block_id
                    break
            except Exception:
                continue

        if current_block:
            current_idx = focus_order.index(current_block)
            prev_idx = (current_idx - 1) % len(focus_order)
        else:
            prev_idx = len(focus_order) - 1

        for i in range(len(focus_order)):
            try_idx = (prev_idx - i) % len(focus_order)
            try:
                prev_block = self.query_one(focus_order[try_idx])
                if focus_order[try_idx] == "#menu-pane":
                    first_btn = prev_block.query_one(GlitchButton)
                    if first_btn:
                        first_btn.focus()
                        return
                elif focus_order[try_idx] == "#input-container":
                    input_field = self.query_one("#main_input", MultilineInput)
                    input_field.focus()
                    return
                else:
                    prev_block.focus()
                    return
            except Exception:
                continue
