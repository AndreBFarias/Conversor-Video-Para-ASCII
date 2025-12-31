from __future__ import annotations

import asyncio
import logging
import random

from rich.style import Style
from rich.text import Text

import config
from src.ui.banner.helpers import STATIC_CHARS, create_entity_banner
from src.ui.banner.tv_static import TVTarget, get_tv_engine
from src.ui.status_decrypt import get_entity_status_text

logger = logging.getLogger(__name__)


async def run_tv_static_transition(app, duration: float = None, steps: int = 20):
    if duration is None:
        duration = config.GLITCH_CONFIG.get("TV_TRANSITION_DURATION", 1.2)

    engine = get_tv_engine(app)
    await engine.run(
        targets={TVTarget.BANNER, TVTarget.ASCII, TVTarget.STATUS, TVTarget.EMOTION},
        duration=duration,
        steps=steps,
        pattern="pulse",
    )


async def run_tv_static_effect(app, duration=2.0, steps=30):
    engine = get_tv_engine(app)
    await engine.run(targets={TVTarget.ALL}, duration=duration, steps=steps, pattern="pulse")


def run_tv_static_effect_sync(app):
    app.run_worker(run_tv_static_effect(app, 1.0, 15), exclusive=False, thread=False)


async def run_loading_screen(app, duration: float = 4.0):
    try:
        welcome_pane = app.query_one("#welcome-pane")
        ascii_pane = app.query_one("#ascii-pane")
        status_label = app.query_one("#status-label")
        emotion_label = app.query_one("#emotion-label")
    except Exception as e:
        logger.debug(f"Widgets nao encontrados para loading screen: {e}")
        return

    app.refresh(layout=True)
    await asyncio.sleep(0.1)

    for _ in range(10):
        if ascii_pane.size.width > 0 and ascii_pane.size.height > 0:
            break
        app.refresh(layout=True)
        await asyncio.sleep(0.05)

    engine = get_tv_engine(app)
    base_colors, accent_color, _ = engine._get_colors()

    w_ascii, h_ascii = engine._get_widget_dims("ascii-pane")
    w_banner, h_banner = engine._get_widget_dims("welcome-pane")

    status_label.remove_class("status-hidden")
    status_label.add_class("status-visible")

    steps = int(duration * 12)
    loading_msgs = [
        "[Inicializando sistemas...]",
        "[Carregando consciência...]",
        "[Sintonizando frequências...]",
        "[Calibrando percepção...]",
        "[Despertando...]",
    ]

    for i in range(steps):
        welcome_pane.update(engine.generate_static_text(w_banner, h_banner, 1.0))
        ascii_pane.update(engine.generate_static_text(w_ascii, h_ascii, 1.0))

        if i % 8 == 0:
            msg_idx = min(i // 8, len(loading_msgs) - 1)
            status_label.update(loading_msgs[msg_idx])

        if hasattr(emotion_label, "update"):
            static_emotion = f"[{''.join(random.choices(STATIC_CHARS[:8], k=15))}]"
            emotion_label.update(static_emotion)

        await asyncio.sleep(duration / steps)


async def run_startup_sequence(app, on_ready_callback=None):
    await run_loading_screen(app, duration=4.0)

    if on_ready_callback:
        on_ready_callback()

    await asyncio.sleep(0.1)
    await run_tv_static_transition(app, duration=0.6, steps=12)


async def run_shutdown_sequence(app, duration: float = 0.8):
    engine = get_tv_engine(app)
    await engine.run(
        targets={TVTarget.BANNER, TVTarget.ASCII, TVTarget.STATUS, TVTarget.EMOTION},
        duration=duration,
        steps=20,
        pattern="fade_in",
    )

    try:
        base_colors, accent_color, _ = engine._get_colors()

        welcome_pane = app.query_one("#welcome-pane")
        ascii_pane = app.query_one("#ascii-pane")
        w_banner, h_banner = engine._get_widget_dims("welcome-pane")
        w_ascii, h_ascii = engine._get_widget_dims("ascii-pane")

        final_banner = Text()
        for row in range(h_banner):
            line = "".join(random.choice(STATIC_CHARS) for _ in range(w_banner))
            final_banner.append(line, Style(color=accent_color, dim=True))
            if row < h_banner - 1:
                final_banner.append("\n")
        welcome_pane.update(final_banner)

        final_ascii = Text()
        for row in range(h_ascii):
            line = "".join(random.choice(STATIC_CHARS) for _ in range(w_ascii))
            final_ascii.append(line, Style(color=accent_color, dim=True))
            if row < h_ascii - 1:
                final_ascii.append("\n")
        ascii_pane.update(final_ascii)
    except Exception as e:
        logger.debug(f"Erro ao finalizar shutdown sequence: {e}")

    await asyncio.sleep(0.1)


async def run_voice_toggle_transition(app, activating: bool, duration: float = 0.3):
    audio_viz = app.query_one("#audio-visualizer")
    welcome_pane = app.query_one("#welcome-pane")

    if activating:
        engine = get_tv_engine(app)
        await engine.run(
            targets={TVTarget.BANNER}, duration=duration, steps=8, pattern="quick_pulse", restore_after=False
        )
        welcome_pane.add_class("hidden")
        welcome_pane.styles.display = "none"
        audio_viz.remove_class("hidden")
        audio_viz.styles.display = "block"
        logger.info("[VOZ] Banner escondido, AudioVisualizer visivel")
    else:
        audio_viz.add_class("hidden")
        audio_viz.styles.display = "none"
        welcome_pane.remove_class("hidden")
        welcome_pane.styles.display = "block"
        logger.info("[VOZ] AudioVisualizer escondido, Banner visivel")
        await run_banner_only_static(app, duration=0.3)


async def run_emotion_transition(app, duration: float = 0.5):
    engine = get_tv_engine(app)
    await engine.run(targets={TVTarget.BANNER, TVTarget.ASCII}, duration=duration, steps=12, pattern="quick_pulse")


async def run_banner_only_static(app, duration: float = 0.5):
    engine = get_tv_engine(app)
    await engine.run(targets={TVTarget.BANNER}, duration=duration, steps=15, pattern="quick_pulse")


async def run_startup_static(app, duration: float = 1.2):
    engine = get_tv_engine(app)

    try:
        base_colors, accent_color, _ = engine._get_colors()

        welcome_pane = app.query_one("#welcome-pane")
        ascii_pane = app.query_one("#ascii-pane")
        status_label = app.query_one("#status-label")
        emotion_label = app.query_one("#emotion-label")

        w_banner, h_banner = engine._get_widget_dims("welcome-pane")
        w_ascii, h_ascii = engine._get_widget_dims("ascii-pane")

        initial_banner = Text()
        for row in range(h_banner):
            line = "".join(random.choice(STATIC_CHARS) for _ in range(w_banner))
            initial_banner.append(line, Style(color=accent_color, dim=True))
            if row < h_banner - 1:
                initial_banner.append("\n")
        welcome_pane.update(initial_banner)

        initial_ascii = Text()
        for row in range(h_ascii):
            line = "".join(random.choice(STATIC_CHARS) for _ in range(w_ascii))
            initial_ascii.append(line, Style(color=accent_color, dim=True))
            if row < h_ascii - 1:
                initial_ascii.append("\n")
        ascii_pane.update(initial_ascii)

        if hasattr(status_label, "set_text"):
            status_label.set_text("".join(random.choice(STATIC_CHARS) for _ in range(20)), animate=False)
        if hasattr(emotion_label, "set_text"):
            emotion_label.set_text("".join(random.choice(STATIC_CHARS) for _ in range(25)), animate=False)

        app.refresh()
        await asyncio.sleep(0.3)

    except Exception as e:
        logger.warning(f"[STARTUP] Erro ao preencher static inicial: {e}")

    await engine.run(
        targets={TVTarget.BANNER, TVTarget.ASCII, TVTarget.STATUS, TVTarget.EMOTION},
        duration=duration,
        steps=25,
        pattern="fade_out",
    )

    try:
        welcome_pane = app.query_one("#welcome-pane")
        welcome_pane.update(create_entity_banner())

        status_label = app.query_one("#status-label")
        if hasattr(status_label, "set_text"):
            status_label.set_text("", animate=False)
        else:
            status_label.update("")
        status_label.add_class("status-hidden")
        status_label.remove_class("status-visible")

        emotion_label = app.query_one("#emotion-label")
        if hasattr(emotion_label, "set_text"):
            emotion_label.set_text(get_entity_status_text("observando"), animate=False)
    except Exception as e:
        logger.debug(f"Erro ao restaurar widgets apos startup static: {e}")


async def run_fade_out_effect(app):
    try:
        await run_tv_static_transition(app, duration=0.8, steps=15)
        if hasattr(app, "run_animation"):
            app.run_animation("observando")
    except Exception as e:
        logger.warning(f"Erro no fade out effect: {e}")
