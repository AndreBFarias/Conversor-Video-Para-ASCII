from .appearance import AppearanceTracker
from .manager import VoiceProfileManager

_voice_manager: VoiceProfileManager | None = None
_appearance_tracker: AppearanceTracker | None = None


def get_voice_manager() -> VoiceProfileManager:
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceProfileManager()
    return _voice_manager


def get_appearance_tracker() -> AppearanceTracker:
    global _appearance_tracker
    if _appearance_tracker is None:
        _appearance_tracker = AppearanceTracker()
    return _appearance_tracker
