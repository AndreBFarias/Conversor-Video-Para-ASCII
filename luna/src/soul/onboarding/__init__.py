from src.soul.onboarding.acts import finish_onboarding, register_face_from_last_capture, run_act_one, run_act_two
from src.soul.onboarding.core import OnboardingFlow, OnboardingProcess
from src.soul.onboarding.dialogues import OnboardingDialogues
from src.soul.onboarding.input_handlers import (
    extract_name,
    handle_button_click,
    handle_text_input,
    wait_for_button_click,
    wait_for_text_input,
)
from src.soul.onboarding.profile import (
    EVENTS_DIR,
    FACES_DIR,
    PROFILE_PATH,
    USER_DIR,
    ensure_directories,
    get_name,
    get_profile_preference,
    log_event,
    reset_profile,
    save_profile_update,
    verify_first_run,
)
from src.soul.onboarding.tts_helpers import activate_voice_mode, falar_onboarding, pause_listening, resume_listening
from src.soul.onboarding.ui_helpers import (
    apply_entity_styles_inline,
    hide_all_for_onboarding,
    reload_ui_for_entity,
    reveal_all,
    reveal_element,
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
