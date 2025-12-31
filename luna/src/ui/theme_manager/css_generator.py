from __future__ import annotations

from .utils import hex_to_rgba


def generate_css_overrides(
    entity_id: str,
    primary: str,
    secondary: str,
    accent: str,
    background: str,
    glow: str,
    text_primary: str,
    text_secondary: str,
) -> str:
    primary_bg = hex_to_rgba(primary, 0.08)
    secondary_bg = hex_to_rgba(secondary, 0.18)
    accent_bg = hex_to_rgba(accent, 0.25)
    primary_subtle = hex_to_rgba(primary, 0.1)
    accent_darker = hex_to_rgba(accent, 0.15)
    hover_bg = hex_to_rgba(text_secondary, 0.3)

    css = f"""
/* Theme Override - {entity_id} */

Screen {{
    background: {background};
    color: {text_primary};
}}

#ascii-container {{
    border: heavy {text_secondary};
    background: {background};
}}

#menu-pane {{
    border: heavy {text_secondary};
    background: {background};
}}

#chat-area {{
    border: heavy {text_secondary};
    background: {background};
}}

#input-container {{
    border: heavy {text_secondary};
    background: {background};
}}

#right-pane {{
    background: {background};
}}

#welcome-pane {{
    background: {background};
}}

#chat-list {{
    background: {background};
}}

#canone-title {{
    color: {primary};
}}

#history-title {{
    color: {primary};
}}

.luna-sender {{
    color: {primary};
}}

.message-luna {{
    border-left: wide {primary};
    background: {primary_bg};
}}

Button {{
    color: {primary};
    background: transparent;
}}

Button:hover {{
    color: {glow};
    background: {hover_bg};
}}

Button:focus {{
    background: {hover_bg};
}}

Button.-active {{
    background: {primary};
    color: {background};
}}

GlitchButton {{
    color: {primary};
    background: transparent;
}}

GlitchButton:hover {{
    background: {hover_bg};
    color: {glow};
}}

#back-button:hover {{
    background: {hover_bg};
}}

#canone-tabs Tab {{
    color: {text_secondary};
    background: transparent;
}}

#canone-tabs Tab:hover {{
    background: {hover_bg};
    color: {primary};
}}

#canone-tabs Tab.-active {{
    color: {primary};
    background: {hover_bg};
}}

#canone-tabs Underline {{
    background: {primary};
}}

#canone-tabs TabPane {{
    background: {background};
}}

#btn-save-canone {{
    background: {accent};
    color: {background};
}}

#btn-save-canone:hover {{
    background: {accent};
}}

#emotion-label {{
    color: {primary};
}}

#status-label {{
    color: {primary};
}}

.onboarding-revealed {{
    border: heavy {secondary};
    background: {secondary_bg};
    color: {secondary};
}}

.glitch-reveal {{
    color: {accent};
    border: double {accent};
    background: {accent_bg};
}}

.revealed-stable {{
    border: solid {primary};
    background: {primary_subtle};
}}

#canone-modal {{
    border-left: wide {primary};
}}

#history-list > ListItem {{
    background: transparent;
}}

#history-list > ListItem:hover {{
    background: {hover_bg};
    border-left: wide {primary};
}}

#history-list > ListItem:focus {{
    background: {hover_bg};
    border-left: double {glow};
}}

#history-list > ListItem.-selected {{
    background: {hover_bg};
}}

Select {{
    background: {background};
    border: tall {text_secondary};
}}

Select:focus {{
    border: tall {primary};
}}

Input {{
    background: {background};
    border: tall {text_secondary};
}}

Input:focus {{
    border: tall {primary};
}}

Switch {{
    background: {text_secondary};
}}

Switch.-on {{
    background: {primary};
}}

VerticalScroll {{
    scrollbar-background: {background};
    scrollbar-color: {text_secondary};
    scrollbar-color-hover: {primary};
    scrollbar-color-active: {glow};
}}

MarkdownH1, MarkdownH2, MarkdownH3, MarkdownH4, MarkdownH5, MarkdownH6 {{
    color: {primary};
}}

#status-label {{
    background: {background};
    color: {primary};
}}

#emotion-label {{
    background: {background};
    color: {primary};
}}

VerticalScroll#chat-list {{
    background: {background};
}}

#history-container {{
    background: {background};
}}

#history-list {{
    background: {background};
}}

#audio-visualizer {{
    background: {background};
}}

VoiceTrainerScreen {{
    background: {background};
}}

HistoryScreen {{
    background: {background};
}}

#status-area {{
    background: {background};
}}

#main_input {{
    background: {background};
}}

#main_input:focus {{
    background: {background};
}}

.code-block:hover .code-hint {{
    color: {primary};
}}

.code-block.copied .code-block-container {{
    border: round {accent};
}}

.message-container.copied {{
    border: round {accent};
}}

.msg-text.copied {{
    background: {accent_darker};
    color: {accent};
}}
"""
    return css
