"""
Onboarding - Sistema de primeiro acesso.

Guia o usuario no primeiro contato:
- Coleta nome e preferencias
- Reveal progressivo de elementos UI
- Registro de rosto opcional
- Suporte a multiplas entidades

Classes principais:
    OnboardingProcess: Processo de onboarding
    OnboardingDialogues: Dialogos do CSV

NOTA: Este arquivo e um wrapper de compatibilidade.
A implementacao real esta em src/soul/onboarding/
"""

from src.soul.onboarding import (
    EVENTS_DIR,
    FACES_DIR,
    PROFILE_PATH,
    USER_DIR,
    OnboardingDialogues,
    OnboardingFlow,
    OnboardingProcess,
    activate_voice_mode,
    apply_entity_styles_inline,
    ensure_directories,
    extract_name,
    falar_onboarding,
    finish_onboarding,
    get_name,
    get_profile_preference,
    handle_button_click,
    handle_text_input,
    hide_all_for_onboarding,
    log_event,
    pause_listening,
    register_face_from_last_capture,
    reload_ui_for_entity,
    reset_profile,
    resume_listening,
    reveal_all,
    reveal_element,
    run_act_one,
    run_act_two,
    save_profile_update,
    verify_first_run,
    wait_for_button_click,
    wait_for_text_input,
)

__all__ = [
    "OnboardingProcess",
    "OnboardingFlow",
    "OnboardingDialogues",
    "run_act_one",
    "run_act_two",
    "register_face_from_last_capture",
    "finish_onboarding",
    "verify_first_run",
    "reset_profile",
    "save_profile_update",
    "get_profile_preference",
    "get_name",
    "log_event",
    "ensure_directories",
    "USER_DIR",
    "PROFILE_PATH",
    "EVENTS_DIR",
    "FACES_DIR",
    "reveal_element",
    "hide_all_for_onboarding",
    "reveal_all",
    "reload_ui_for_entity",
    "apply_entity_styles_inline",
    "falar_onboarding",
    "pause_listening",
    "resume_listening",
    "activate_voice_mode",
    "wait_for_text_input",
    "wait_for_button_click",
    "handle_text_input",
    "handle_button_click",
    "extract_name",
]
