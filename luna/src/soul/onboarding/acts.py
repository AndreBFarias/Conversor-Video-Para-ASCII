from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING

import cv2

from src.soul.onboarding.input_handlers import extract_name, wait_for_button_click, wait_for_text_input
from src.soul.onboarding.profile import EVENTS_DIR, get_profile_preference, log_event, save_profile_update
from src.soul.onboarding.tts_helpers import activate_voice_mode, falar_onboarding, pause_listening, resume_listening
from src.soul.onboarding.ui_helpers import reveal_all, reveal_element
from src.soul.user_profiler import get_user_profiler

if TYPE_CHECKING:
    from src.soul.onboarding.core import OnboardingProcess

logger = logging.getLogger(__name__)


async def run_act_one(process: OnboardingProcess):
    if hasattr(process.app, "boca") and process.app.boca:
        logger.info("TTS disponivel para onboarding")
        if process.use_premium_tts and process.app.boca.elevenlabs_disponivel:
            logger.info("ElevenLabs sera usado para voz premium")
    else:
        logger.warning("TTS nao disponivel - onboarding em modo texto")

    logger.info("[PASSO 0] ESTATICA - TV static por 3 segundos")
    await asyncio.sleep(3)

    reveal_element(process, "main_input")

    entity_config = process.entity_loader.get_config() if process.entity_loader else {}
    entity_name = entity_config.get("name", "Luna")

    if process.selected_entity != "luna":
        saudacao_custom = f"Bem-vindo ao terminal de {entity_name}. Como devo te chamar, mortal?"
        await falar_onboarding(process, saudacao_custom, stability=0.28, style=0.68, speed=1.12)
    else:
        frase_nome = process.dialogues.get_frase(1, process.user_name)
        await falar_onboarding(process, frase_nome, stability=0.28, style=0.68, speed=1.12)

    input_task = asyncio.create_task(wait_for_text_input(process, timeout=90))
    user_response = await input_task

    if not user_response:
        user_response = "Explorador"

    log_event("input_name_raw", user_response)
    save_profile_update({"nome_completo_input": user_response})

    name = extract_name(user_response)
    process.user_name = name
    save_profile_update({"nome": name})

    profiler = get_user_profiler()
    nome_analise = profiler.analyze_name(user_response)
    save_profile_update(
        {
            "nome_analise": {
                "genero_provavel": nome_analise.genero_provavel,
                "confianca_genero": nome_analise.confianca_genero,
                "possiveis_origens": nome_analise.possiveis_origens,
                "diminutivos_comuns": nome_analise.diminutivos_comuns,
                "tratamento_sugerido": nome_analise.tratamento_sugerido,
            }
        }
    )
    logger.info(
        f"[ONBOARDING] Analise do nome: genero={nome_analise.genero_provavel} ({nome_analise.confianca_genero:.0%}), origens={nome_analise.possiveis_origens}"
    )

    if process.static_overlay:
        process.static_overlay.reveal_banner()

    if process.selected_entity != "luna":
        entity_name = entity_config.get("name", "Luna")
        frase_prazer = f"{process.user_name}, um prazer. Eu sou {entity_name}."
        await falar_onboarding(process, frase_prazer, stability=0.28, style=0.72, speed=1.15)
    else:
        frase_prazer = process.dialogues.get_frase(3, process.user_name)
        await falar_onboarding(process, frase_prazer, stability=0.28, style=0.72, speed=1.15)

    reveal_element(process, "toggle_voice_call")
    frase_voz = process.dialogues.get_frase(5, process.user_name)
    await falar_onboarding(process, frase_voz, stability=0.28, style=0.72, speed=1.12)

    voice_task = asyncio.create_task(wait_for_button_click(process, "toggle_voice_call", timeout=12))
    try:
        clicked = await voice_task
    except Exception:
        clicked = False

    if clicked:
        activate_voice_mode(process)
        resume_listening(process)
        logger.debug("[ONBOARDING] Escuta ativada para input de voz")
        sentiment = await wait_for_text_input(process, timeout=20)
        pause_listening(process)
        logger.debug("[ONBOARDING] Escuta pausada apos input de voz")
        if sentiment:
            log_event("input_sentiment", sentiment)
            save_profile_update({"preferencias": {"permite_voz": True}})
    else:
        recusa_voz = process.dialogues.get_recusa(4)
        if recusa_voz:
            await falar_onboarding(process, recusa_voz, speed=1.15)
        save_profile_update({"preferencias": {"permite_voz": False}})

    reveal_element(process, "attach_file")


async def run_act_two(process: OnboardingProcess):
    process.app.reveal_menu()

    await asyncio.sleep(0.5)
    reveal_element(process, "ver_historico")
    frase_relicario = process.dialogues.get_frase(4, process.user_name)
    await falar_onboarding(process, frase_relicario, stability=0.32, style=0.62, speed=1.18)

    await asyncio.sleep(0.5)
    reveal_element(process, "olhar")
    reveal_element(process, "nova_conversa")

    vision_task = asyncio.create_task(wait_for_button_click(process, "olhar", timeout=8))
    try:
        clicked_vision = await vision_task
    except (asyncio.CancelledError, asyncio.TimeoutError):
        clicked_vision = False

    if clicked_vision:
        save_profile_update({"preferencias": {"permite_camera": True}})
        for _ in range(50):
            await asyncio.sleep(0.2)
            if process.app.app_state == "IDLE":
                break
        await asyncio.sleep(1.0)
        await register_face_from_last_capture(process)
    else:
        save_profile_update({"preferencias": {"permite_camera": False}})

    await asyncio.sleep(0.5)
    reveal_element(process, "editar_alma")
    frase_custodia = process.dialogues.get_frase(10, process.user_name)
    await falar_onboarding(process, frase_custodia, stability=0.28, style=0.7, speed=1.15)

    await asyncio.sleep(0.5)
    reveal_element(process, "canone")
    reveal_element(process, "quit")
    frase_canone = process.dialogues.get_frase(11, process.user_name)
    await falar_onboarding(process, frase_canone, stability=0.3, style=0.65, speed=1.18)

    await asyncio.sleep(0.8)
    frase_final = process.dialogues.get_frase(12, process.user_name)
    await falar_onboarding(process, frase_final, stability=0.25, style=0.75, speed=1.1)


async def register_face_from_last_capture(process: OnboardingProcess):
    try:
        if not hasattr(process.app, "visao") or not process.app.visao:
            logger.warning("[ONBOARDING] Visao nao disponivel para registro de rosto")
            return

        logger.info("[ONBOARDING] Registrando rosto apos captura de visao...")

        loop = asyncio.get_running_loop()
        frame = await loop.run_in_executor(None, process.app.visao.capturar_frame)

        if frame is None:
            logger.warning("[ONBOARDING] Frame nao disponivel para registro")
            return

        success = process.app.visao.registrar_rosto_imediato(process.user_name, frame)
        if success:
            logger.info(f"[ONBOARDING] Rosto de '{process.user_name}' registrado")
            save_profile_update({"rosto_registrado": True})

        cv2_success, jpg = cv2.imencode(".jpg", frame)
        if cv2_success:
            filename = EVENTS_DIR / f"onboarding_face_{datetime.now().timestamp()}.jpg"
            with open(filename, "wb") as f:
                f.write(jpg)
            logger.info(f"[ONBOARDING] Foto salva: {filename}")

        frases_reacao = [
            f"Agora te reconheço, {process.user_name}.",
            f"Guardei seu rosto na memória, {process.user_name}.",
            f"Você não sera esquecido, {process.user_name}.",
        ]
        await falar_onboarding(process, random.choice(frases_reacao), speed=1.15)

    except Exception as e:
        logger.error(f"[ONBOARDING] Erro ao registrar rosto: {e}")


async def finish_onboarding(process: OnboardingProcess):
    save_profile_update(
        {
            "onboarding_completo": True,
            "completed_at": datetime.now().isoformat(),
            "active_entity": process.selected_entity,
        }
    )
    logger.info(f"Onboarding completed successfully with entity: {process.selected_entity}")
    reveal_all(process)

    permite_voz = get_profile_preference("permite_voz", True)
    if permite_voz:
        activate_voice_mode(process)
        resume_listening(process)
        logger.info("[ONBOARDING] Voz ativada no final do onboarding")

    process.app.call_later(process.app.action_nova_conversa)
