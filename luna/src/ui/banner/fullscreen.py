from __future__ import annotations

import asyncio
import logging
import pathlib

from rich.style import Style
from rich.text import Text

import config
from src.core.entity_loader import get_active_entity
from src.ui.banner.tv_static import get_tv_engine

logger = logging.getLogger(__name__)


def parse_colored_frame(frame: str, width: int, height: int = 30) -> Text:
    colored_text = Text()
    max_width = max(width - 2, 60)
    max_height = max(height - 2, 20)

    try:
        if "\xa7" in frame:
            frame_lines = frame.split("\n")[:max_height]

            for i, line in enumerate(frame_lines):
                if not line.strip():
                    if i < len(frame_lines) - 1:
                        colored_text.append("\n")
                    continue

                pixels = line.split("\xa7")
                num_pixels = len(pixels)

                char_count = 0
                j = 0
                while j < num_pixels - 1 and char_count < max_width:
                    char = pixels[j]
                    code = pixels[j + 1] if j + 1 < num_pixels else ""

                    if code.isdigit():
                        color_num = int(code)
                        if 0 <= color_num <= 255:
                            colored_text.append(char, Style(color=f"color({color_num})"))
                        else:
                            colored_text.append(char)
                    elif char:
                        colored_text.append(char)

                    char_count += len(char) if char else 0
                    j += 2

                if i < len(frame_lines) - 1:
                    colored_text.append("\n")
        else:
            frame_lines = frame.split("\n")[:max_height]

            for i, line in enumerate(frame_lines):
                truncated_line = line[:max_width]
                for char in truncated_line:
                    if char == "\n":
                        continue
                    color = config.COLOR_MAP.get(char, "#f8f8f2")
                    colored_text.append(char, Style(color=color))

                if i < len(frame_lines) - 1:
                    colored_text.append("\n")
    except Exception as e:
        logger.debug(f"Erro ao parsear frame colorido: {e}")
        colored_text = Text(frame[:500] if len(frame) > 500 else frame)

    return colored_text


async def run_fullscreen_piscando(app, duration: float = 2.5):
    from src.ui.banner.transitions import run_tv_static_transition

    onboarding_overlay = None
    onboarding_was_running = False

    try:
        if hasattr(app, "onboarding") and hasattr(app.onboarding, "static_overlay"):
            onboarding_overlay = app.onboarding.static_overlay
            if onboarding_overlay and onboarding_overlay.running:
                onboarding_was_running = True
                if onboarding_overlay.timer:
                    onboarding_overlay.timer.stop()
                    onboarding_overlay.timer = None
                logger.info("[VER] Onboarding overlay pausado para piscando")

        welcome_pane = app.query_one("#welcome-pane")
        ascii_pane = app.query_one("#ascii-pane")
        status_area = app.query_one("#status-area")
        audio_viz = app.query_one("#audio-visualizer")

        anim_controller = getattr(app, "animation_controller", None)
        if anim_controller:
            if anim_controller.animation_timer:
                anim_controller.animation_timer.stop()
                anim_controller.animation_timer = None
            anim_controller.is_animating = False
            logger.info("[VER] AnimationController pausado")

        ascii_container = app.query_one("#ascii-container")
        ascii_container.add_class("fullscreen-active")

        welcome_pane.add_class("hidden")
        status_area.add_class("hidden")
        audio_viz.add_class("hidden")
        ascii_pane.add_class("fullscreen")

        app.refresh(layout=True)
        await asyncio.sleep(0.05)

        entity_id = get_active_entity()
        entity_name = entity_id.capitalize() if entity_id else "Luna"

        entity_anim_dir = config.ENTITIES_DIR / entity_id / "animations" if entity_id else config.ASCII_ART_DIR
        piscando_path = entity_anim_dir / f"{entity_name}_piscando.txt"

        gz_path = pathlib.Path(str(piscando_path) + ".gz")
        file_exists = piscando_path.exists() or gz_path.exists()

        if not file_exists:
            piscando_path = config.ASCII_ART_DIR / "Luna_piscando.txt"
            gz_path = pathlib.Path(str(piscando_path) + ".gz")
            file_exists = piscando_path.exists() or gz_path.exists()
            logger.info(f"[VER] Fallback para Luna_piscando: {piscando_path}")

        logger.info(
            f"[VER] Carregando animacao piscando de: {piscando_path} (entidade: {entity_name}, existe: {file_exists})"
        )

        if file_exists:
            from src.core.animation import load_animation_frames_from_file

            frames, fps = load_animation_frames_from_file(piscando_path)

            logger.info(f"[VER] Animacao carregada: {len(frames)} frames, {fps} FPS")

            engine = get_tv_engine(app)
            width, _ = engine._get_widget_dims("ascii-pane")
            frame_duration = 1.0 / fps
            total_frames = int(duration * fps)

            logger.info(f"[VER] Executando {total_frames} frames por {duration}s")

            for i in range(min(total_frames, len(frames) * 3)):
                frame = frames[i % len(frames)]
                colored_text = parse_colored_frame(frame, width)
                ascii_pane.update(colored_text)
                await asyncio.sleep(frame_duration)
        else:
            logger.error(f"[VER] Arquivo de animacao NAO encontrado: {piscando_path}")

        ascii_container.remove_class("fullscreen-active")
        ascii_pane.remove_class("fullscreen")
        status_area.remove_class("hidden")

        em_chamada = getattr(app, "em_chamada", False)
        if em_chamada:
            audio_viz.remove_class("hidden")
        else:
            welcome_pane.remove_class("hidden")

        app.refresh(layout=True)
        await asyncio.sleep(0.05)

        await run_tv_static_transition(app, duration=0.5, steps=12)

        if onboarding_was_running and onboarding_overlay:
            onboarding_overlay.timer = app.set_interval(0.12, onboarding_overlay._update_overlay)
            logger.info("[VER] Onboarding overlay retomado")

        logger.info("[VER] Fullscreen piscando concluido")

    except Exception as e:
        logger.warning(f"Erro no fullscreen piscando: {e}")
        try:
            app.query_one("#ascii-container").remove_class("fullscreen-active")
            app.query_one("#ascii-pane").remove_class("fullscreen")
            app.query_one("#welcome-pane").remove_class("hidden")
            app.query_one("#status-area").remove_class("hidden")
        except Exception as e2:
            logger.debug(f"Erro ao restaurar UI apos falha: {e2}")
        if onboarding_was_running and onboarding_overlay:
            try:
                onboarding_overlay.timer = app.set_interval(0.12, onboarding_overlay._update_overlay)
            except Exception as e:
                logger.debug(f"Erro ao retomar onboarding: {e}")
