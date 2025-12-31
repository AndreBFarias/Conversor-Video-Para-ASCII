from __future__ import annotations

import threading

import config
from src.core.entity_loader import EntityLoader, get_active_entity
from src.core.logging_config import get_logger

from .loader import auto_compress_all_animations, clear_animation_cache, load_animation_frames_from_file

logger = get_logger(__name__)

_IDLE_ANIMATIONS = {"observando", "idle", "dormindo", "waiting"}


class AnimationController:
    def __init__(self, app):
        self.app = app
        self.animations = {}
        self.animation_timer = None
        self.current_animation_frames = []
        self.current_frame_index = 0
        self.is_animating = False
        self.is_fullscreen = False
        self.current_animation = "observando"

        active_entity_id = get_active_entity()
        self.entity_loader = EntityLoader(active_entity_id)
        logger.info(f"AnimationController inicializado com entidade: {active_entity_id}")

    def load_all_animations(self):
        auto_compress_all_animations()

        logger.info("Carregando animacoes...")

        entity_name = self.entity_loader.get_config().get("name", "Luna")
        entity_anim_dir = self.entity_loader.entity_data.get("animations_dir")
        fallback_dir = config.APP_DIR / "src" / "assets" / "panteao" / "entities" / "luna" / "animations"

        fallback_count = 0
        for sentiment, legacy_path in config.EMOTION_MAP.items():
            animation_loaded = False

            if entity_anim_dir and entity_anim_dir.exists():
                entity_anim_path = entity_anim_dir / f"{entity_name}_{sentiment}.txt"
                entity_anim_path_gz = entity_anim_dir / f"{entity_name}_{sentiment}.txt.gz"

                if entity_anim_path_gz.exists():
                    self.animations[sentiment] = load_animation_frames_from_file(entity_anim_path)
                    animation_loaded = True
                    logger.debug(f"Carregada animacao {sentiment} de {entity_name} (panteao)")
                elif entity_anim_path.exists():
                    self.animations[sentiment] = load_animation_frames_from_file(entity_anim_path)
                    animation_loaded = True
                    logger.debug(f"Carregada animacao {sentiment} de {entity_name} (panteao)")

            if not animation_loaded:
                luna_fallback = fallback_dir / f"Luna_{sentiment}.txt"
                luna_fallback_gz = fallback_dir / f"Luna_{sentiment}.txt.gz"

                if luna_fallback_gz.exists():
                    self.animations[sentiment] = load_animation_frames_from_file(luna_fallback)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] {entity_name}_{sentiment} -> Luna_{sentiment}.txt.gz")
                elif luna_fallback.exists():
                    self.animations[sentiment] = load_animation_frames_from_file(luna_fallback)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] {entity_name}_{sentiment} -> Luna_{sentiment}.txt")
                elif legacy_path.exists():
                    self.animations[sentiment] = load_animation_frames_from_file(legacy_path)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] Carregada animacao legacy {legacy_path.name}")

        for action, legacy_path in config.ACTION_ANIMATIONS.items():
            action_loaded = False

            if entity_anim_dir and entity_anim_dir.exists():
                entity_action_path = entity_anim_dir / f"{entity_name}_{action}.txt"
                entity_action_path_gz = entity_anim_dir / f"{entity_name}_{action}.txt.gz"

                if entity_action_path_gz.exists():
                    self.animations[action] = load_animation_frames_from_file(entity_action_path)
                    action_loaded = True
                    logger.debug(f"Carregada acao {action} de {entity_name} (panteao)")
                elif entity_action_path.exists():
                    self.animations[action] = load_animation_frames_from_file(entity_action_path)
                    action_loaded = True
                    logger.debug(f"Carregada acao {action} de {entity_name} (panteao)")

            if not action_loaded:
                luna_fallback = fallback_dir / f"Luna_{action}.txt"
                luna_fallback_gz = fallback_dir / f"Luna_{action}.txt.gz"

                if luna_fallback_gz.exists():
                    self.animations[action] = load_animation_frames_from_file(luna_fallback)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] {entity_name}_{action} -> Luna_{action}.txt.gz")
                elif luna_fallback.exists():
                    self.animations[action] = load_animation_frames_from_file(luna_fallback)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] {entity_name}_{action} -> Luna_{action}.txt")
                elif legacy_path.exists():
                    self.animations[action] = load_animation_frames_from_file(legacy_path)
                    fallback_count += 1
                    logger.debug(f"[FALLBACK] Carregada acao legacy {legacy_path.name}")

        if fallback_count > 0:
            logger.info(
                f"{len(self.animations)} animacoes carregadas para {entity_name} ({fallback_count} usando fallback Luna)"
            )
        else:
            logger.info(f"{len(self.animations)} animacoes carregadas para {entity_name} (todas originais)")

    def reload_for_entity(self, entity_id: str):
        logger.info(f"Recarregando animacoes para entidade: {entity_id}")

        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer = None

        self.is_animating = False
        self.entity_loader = EntityLoader(entity_id)
        self.animations.clear()
        self.current_animation_frames = []
        self.current_frame_index = 0

        clear_animation_cache()
        self.load_all_animations()

        logger.info(f"Animacoes recarregadas para {entity_id}. Reiniciando animacao 'observando'.")
        self.run_animation("observando")

    def _safe_ui_call(self, func, *args):
        if hasattr(self.app, "_thread_id") and threading.get_ident() != self.app._thread_id:
            self.app.call_from_thread(func, *args)
        else:
            func(*args)

    def run_fullscreen_animation(self, sentiment: str):
        from .fullscreen import run_fullscreen_animation

        run_fullscreen_animation(self, sentiment)

    def end_fullscreen(self, with_transition: bool = True):
        from .fullscreen import end_fullscreen

        end_fullscreen(self, with_transition)

    def run_animation(self, sentiment: str):
        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer = None

        self.is_animating = False

        if sentiment:
            normalized = sentiment.replace(".txt", "").replace(".gz", "")
            entity_id = get_active_entity()
            entity_prefixes = [
                f"{entity_id.capitalize()}_",
                f"{entity_id}_",
                "Luna_",
                "Eris_",
                "Juno_",
                "Mars_",
                "Lars_",
                "Somn_",
            ]
            for prefix in entity_prefixes:
                if normalized.startswith(prefix):
                    normalized = normalized[len(prefix) :]
                    break
            self.current_animation = normalized
            logger.debug(f"Iniciando animacao: {normalized}")
            self.is_animating = True

            entity_name = self.entity_loader.get_config().get("name", "Luna")
            emotion_text = f"[{entity_name} esta {normalized}]"
            try:
                emotion_label = self.app.query_one("#emotion-label")
                if hasattr(self.app, "_thread_id") and threading.get_ident() != self.app._thread_id:
                    self.app.call_from_thread(emotion_label.update, emotion_text)
                else:
                    emotion_label.update(emotion_text)
                logger.debug(f"Emotion label atualizado: {emotion_text}")
            except Exception as e:
                logger.debug(f"Nao foi possivel atualizar emotion-label: {e}")

            frames_tuple = self.animations.get(normalized)
            if not frames_tuple or not frames_tuple[0]:
                logger.warning(f"Nenhum frame encontrado para a animacao: {normalized}. Usando 'observando'.")
                normalized = "observando"
                self.current_animation = normalized
                frames_tuple = self.animations.get(normalized)
                if not frames_tuple or not frames_tuple[0]:
                    logger.error("Falha critica: Animacao 'observando' tambem nao encontrada!")
                    self.is_animating = False
                    return

            frames, file_rate = frames_tuple
            self.current_animation_frames = frames
            self.current_frame_index = 0

            if normalized in ("ver", "olhando", "curiosa"):
                rate = config.ANIM_FPS_VER
            elif normalized == "piscando":
                rate = 240.0
            else:
                rate = file_rate

            try:
                interval = 1.0 / float(rate)
                if interval <= 0:
                    raise ValueError("Taxa deve ser positiva")
            except (ValueError, ZeroDivisionError, TypeError) as e:
                logger.warning(
                    f"Taxa de quadros invalida ({rate}) para '{sentiment}'. Usando padrao {config.FRAME_RATE}. Erro: {e}"
                )
                interval = 1.0 / config.FRAME_RATE

            self.animation_timer = self.app.set_interval(interval, self._update_animation_frame)

    def _update_animation_frame(self) -> None:
        from src.ui.banner import parse_colored_frame

        if not self.current_animation_frames:
            logger.warning("Sem frames para animar")
            return

        self.is_animating = True
        total_frames = len(self.current_animation_frames)

        if self.current_frame_index >= total_frames:
            anim_lower = (self.current_animation or "").lower()
            is_idle = anim_lower in _IDLE_ANIMATIONS

            if is_idle:
                self.current_frame_index = 0
            else:
                logger.debug(f"Animacao '{self.current_animation}' terminou, transicao para observando")
                if self.animation_timer:
                    self.animation_timer.stop()
                    self.animation_timer = None
                self.is_animating = False

                async def transition_and_observe():
                    from src.ui.banner import run_tv_static_transition

                    await run_tv_static_transition(self.app, duration=0.5, steps=12)
                    self.run_animation("observando")

                self.app.run_worker(transition_and_observe(), exclusive=True, thread=False)
                return

        frame = self.current_animation_frames[self.current_frame_index]

        try:
            ascii_pane = self.app.query_one("#ascii-pane")
            width = ascii_pane.size.width if ascii_pane.size.width > 0 else 80
            height = ascii_pane.size.height if ascii_pane.size.height > 0 else 30
        except Exception:
            width = 80
            height = 30

        colored_text = parse_colored_frame(frame, width, height)

        def do_update():
            try:
                if hasattr(self.app, "screen_stack") and len(self.app.screen_stack) > 1:
                    return
                self.app._update_ascii_pane(colored_text)
            except Exception as e:
                logger.debug(f"Erro ao atualizar ASCII pane: {e}")

        if hasattr(self.app, "_thread_id") and threading.get_ident() != self.app._thread_id:
            self.app.call_from_thread(do_update)
        else:
            do_update()

        self.current_frame_index += 1
