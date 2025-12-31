import json
import os
import subprocess
import time
from pathlib import Path


class HeadlessRunner:
    def __init__(self, display: str = ":99"):
        self.display = display
        self.xvfb_process = None
        self.luna_process = None

    def start_xvfb(self) -> bool:
        try:
            self.xvfb_process = subprocess.Popen(
                ["Xvfb", self.display, "-screen", "0", "1920x1080x24"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)
            return True
        except FileNotFoundError:
            print("Xvfb not installed. Run: sudo apt install xvfb")
            return False

    def start_luna(self, timeout: int = 20) -> bool:
        env = os.environ.copy()
        env["DISPLAY"] = self.display

        self.luna_process = subprocess.Popen(
            ["./venv/bin/python", "main.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        time.sleep(timeout)
        return self.luna_process.poll() is None

    def capture_logs(self) -> dict:
        logs_dir = Path("src/logs")
        latest_session = max(logs_dir.glob("session_*.log"), default=None)
        latest_events = max(logs_dir.glob("events_*.json"), default=None)

        result = {}
        if latest_session:
            result["session_log"] = latest_session.read_text()[-5000:]
        if latest_events:
            result["events"] = json.loads(latest_events.read_text())

        return result

    def check_startup_success(self) -> dict:
        logs = self.capture_logs()
        session_log = logs.get("session_log", "")

        checks = {
            "process_running": self.luna_process and self.luna_process.poll() is None,
            "ui_mounted": "Montando interface" in session_log,
            "animations_loaded": "animacoes carregadas" in session_log.lower(),
            "no_critical_errors": "CRITICAL" not in session_log,
        }

        return {
            "passed": all(checks.values()),
            "checks": checks,
            "log_tail": session_log[-1000:] if session_log else "",
        }

    def cleanup(self):
        if self.luna_process:
            self.luna_process.terminate()
            self.luna_process.wait(timeout=5)
        if self.xvfb_process:
            self.xvfb_process.terminate()

    def run_test(self) -> dict:
        if not self.start_xvfb():
            return {"passed": False, "error": "Xvfb failed"}

        if not self.start_luna():
            self.cleanup()
            return {"passed": False, "error": "Luna failed to start"}

        result = self.check_startup_success()
        self.cleanup()

        return result


if __name__ == "__main__":
    runner = HeadlessRunner()
    result = runner.run_test()

    print("\n" + "=" * 60)
    print("HEADLESS TEST RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))
