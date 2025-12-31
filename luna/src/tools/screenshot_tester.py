import subprocess
import time
from datetime import datetime
from pathlib import Path

SCREENSHOTS_DIR = Path("src/logs/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(name: str = "test") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
    subprocess.run(["scrot", "-u", str(filepath)], check=True)
    return filepath


def capture_after_delay(name: str, delay: float = 2.0) -> Path:
    time.sleep(delay)
    return capture_screenshot(name)


def get_window_id(window_name: str = "Luna") -> str:
    result = subprocess.run(["xdotool", "search", "--name", window_name], capture_output=True, text=True)
    return result.stdout.strip().split("\n")[0] if result.stdout else ""


def focus_window(window_id: str) -> bool:
    if not window_id:
        return False
    subprocess.run(["xdotool", "windowactivate", window_id])
    time.sleep(0.3)
    return True


def capture_luna_state(state_name: str) -> dict:
    wid = get_window_id()
    if not focus_window(wid):
        return {"success": False, "error": "Window not found"}

    filepath = capture_screenshot(state_name)
    return {"success": True, "filepath": str(filepath), "window_id": wid, "timestamp": datetime.now().isoformat()}
