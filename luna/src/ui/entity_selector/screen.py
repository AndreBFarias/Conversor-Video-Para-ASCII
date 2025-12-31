import gzip
import json
import logging

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from config import APP_DIR
from src.core.entity_loader import ENTITIES_DIR, REGISTRY_PATH
from src.ui.banner import parse_colored_frame

from .helpers import _get_current_theme_colors, _get_entity_theme_colors

logger = logging.getLogger(__name__)


class EntitySelectorScreen(Screen):
    BINDINGS = [
        Binding("left,a", "previous", "Anterior", priority=True),
        Binding("right,d", "next", "Proxima", priority=True),
        Binding("enter", "select", "Selecionar", priority=True),
        Binding("escape", "default_luna", "Default Luna", priority=True),
    ]

    CSS = """
    EntitySelectorScreen {
        align: center middle;
    }

    #entity-container {
        width: 95;
        height: auto;
        padding: 2 4;
    }

    #entity-banner {
        width: 100%;
        min-height: 24;
        height: auto;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    #entity-name {
        width: 100%;
        height: 3;
        text-align: center;
        content-align: center middle;
        text-style: bold;
        padding: 1 0;
    }

    #entity-description {
        width: 100%;
        height: auto;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    #entity-status {
        width: 100%;
        height: 3;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    #navigation-hint {
        width: 100%;
        height: 3;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }
    """

    def __init__(self):
        super().__init__()
        self.entities = []
        self.current_index = 0
        self.selected_entity = "luna"

    def compose(self) -> ComposeResult:
        with Vertical(id="entity-container"):
            yield Static("", id="entity-banner", markup=False)
            yield Static("", id="entity-name")
            yield Static("", id="entity-description")
            yield Static("", id="entity-status")
            yield Static("<- | -> Navegar  |  Enter Selecionar  |  Esc Default Luna", id="navigation-hint")

    def on_mount(self) -> None:
        self._apply_dynamic_theme()
        self._load_entities()
        if self.entities:
            self.call_after_refresh(self._display_current_entity)

    def _apply_dynamic_theme(self, entity_id: str | None = None) -> None:
        try:
            if entity_id:
                theme = _get_entity_theme_colors(entity_id)
            else:
                theme = _get_current_theme_colors()

            background = theme.get("background", "#282a36")
            primary = theme.get("primary_color", "#bd93f9")
            secondary = theme.get("secondary_color", "#ff79c6")
            accent = theme.get("accent_color", "#50fa7b")
            text_primary = theme.get("text_primary", "#f8f8f2")
            text_secondary = theme.get("text_secondary", "#6272a4")
            gradient_start = theme.get("gradient_start", "#44475a")

            self.styles.background = background

            container = self.query_one("#entity-container", Vertical)
            container.styles.background = gradient_start
            container.styles.border = ("heavy", primary)

            banner = self.query_one("#entity-banner", Static)
            banner.styles.color = primary

            name = self.query_one("#entity-name", Static)
            name.styles.color = text_primary

            desc = self.query_one("#entity-description", Static)
            desc.styles.color = text_secondary

            status = self.query_one("#entity-status", Static)
            status.styles.color = accent

            hint = self.query_one("#navigation-hint", Static)
            hint.styles.color = secondary
        except Exception as e:
            logger.debug(f"Erro ao aplicar tema dinamico: {e}")

    def _load_entities(self) -> None:
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                registry = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar registry: {e}")
            self.entities = []
            return

        entities_data = registry.get("entities", {})

        for entity_id, entity_info in entities_data.items():
            config_path = ENTITIES_DIR / entity_id / "config.json"

            try:
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Erro ao carregar config de {entity_id}: {e}")
                continue

            persona = config.get("persona", {})
            archetype_list = persona.get("archetype", [])
            archetype_str = ", ".join(archetype_list) if archetype_list else "Sem descricao"

            self.entities.append(
                {
                    "id": entity_id,
                    "name": entity_info.get("name", entity_id.capitalize()),
                    "available": entity_info.get("available", False),
                    "gender": entity_info.get("gender", "neutral"),
                    "archetype": archetype_str,
                    "config": config,
                }
            )

        if not self.entities:
            logger.error("Nenhuma entidade carregada")
            self.entities = [
                {
                    "id": "luna",
                    "name": "Luna",
                    "available": True,
                    "gender": "feminine",
                    "archetype": "engenheira_gotica",
                    "config": {},
                }
            ]

    def _load_banner(self, entity_name: str) -> str:
        animations_dir = ENTITIES_DIR / entity_name.lower() / "animations"
        banner_file = animations_dir / f"{entity_name}_observando.txt"
        banner_file_gz = animations_dir / f"{entity_name}_observando.txt.gz"

        if not banner_file.exists() and not banner_file_gz.exists():
            animations_dir = APP_DIR / "src" / "assets" / "panteao" / "entities" / "luna" / "animations"
            banner_file = animations_dir / f"{entity_name}_observando.txt"
            banner_file_gz = animations_dir / f"{entity_name}_observando.txt.gz"

        try:
            if banner_file_gz.exists():
                with gzip.open(banner_file_gz, "rt", encoding="utf-8") as f:
                    content = f.read()
            elif banner_file.exists():
                with open(banner_file, encoding="utf-8") as f:
                    content = f.read()
            else:
                return self._get_fallback_banner(entity_name)

            lines = content.split("\n")

            first_frame_lines = []
            in_frame = False
            frame_line_count = 0
            max_frame_lines = 22

            for line in lines:
                if line.strip() == "[FRAME]":
                    if in_frame:
                        break
                    in_frame = True
                    continue

                if in_frame:
                    if frame_line_count >= max_frame_lines:
                        break
                    first_frame_lines.append(line)
                    frame_line_count += 1

            if not first_frame_lines:
                for i, line in enumerate(lines):
                    if i == 0:
                        continue
                    if i > max_frame_lines:
                        break
                    if line.strip() and not line.strip().startswith("["):
                        first_frame_lines.append(line)

            banner_text = "\n".join(first_frame_lines[:22])

            return banner_text if banner_text.strip() else self._get_fallback_banner(entity_name)

        except Exception as e:
            logger.error(f"Erro ao carregar banner de {entity_name}: {e}")
            return self._get_fallback_banner(entity_name)

    def _get_fallback_banner(self, entity_name: str) -> str:
        return f"""
    +=======================+
    |                       |
    |       {entity_name:^15}       |
    |                       |
    +=======================+
        """

    def _display_current_entity(self) -> None:
        if not self.entities:
            return

        entity = self.entities[self.current_index]

        self._apply_dynamic_theme(entity["id"])

        container = self.query_one("#entity-container", Vertical)

        if not entity["available"]:
            container.add_class("unavailable")
            theme = _get_entity_theme_colors(entity["id"])
            text_secondary = theme.get("text_secondary", "#6272a4")
            self.query_one("#entity-banner", Static).styles.color = text_secondary
            self.query_one("#entity-name", Static).styles.color = text_secondary
            self.query_one("#entity-status", Static).styles.color = text_secondary
        else:
            container.remove_class("unavailable")

        banner = self._load_banner(entity["name"])
        banner_widget = self.query_one("#entity-banner", Static)
        colored_banner = parse_colored_frame(banner, 90)
        banner_widget.update(colored_banner)

        self.query_one("#entity-name", Static).update(f"{entity['name']}")

        self.query_one("#entity-description", Static).update(f"{entity['archetype']}")

        if entity["available"]:
            status_text = f"[{self.current_index + 1}/{len(self.entities)}] Disponivel"
            self.query_one("#entity-status", Static).update(status_text)
        else:
            status_text = f"[{self.current_index + 1}/{len(self.entities)}] Indisponivel"
            self.query_one("#entity-status", Static).update(status_text)

    def action_previous(self) -> None:
        if not self.entities:
            return
        self.current_index = (self.current_index - 1) % len(self.entities)
        self._display_current_entity()

    def action_next(self) -> None:
        if not self.entities:
            return
        self.current_index = (self.current_index + 1) % len(self.entities)
        self._display_current_entity()

    def action_select(self) -> None:
        if not self.entities:
            self.dismiss("luna")
            return

        entity = self.entities[self.current_index]

        if not entity["available"]:
            return

        self.selected_entity = entity["id"]
        self.dismiss(self.selected_entity)

    def action_default_luna(self) -> None:
        self.selected_entity = "luna"
        self.dismiss(self.selected_entity)

    def get_selected_entity(self) -> str:
        return self.selected_entity
