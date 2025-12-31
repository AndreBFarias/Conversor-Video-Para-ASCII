import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from src.tools.screenshot_tester import capture_luna_state, get_window_id

REPORT_DIR = Path("src/logs/qa_reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class VisualQA:
    def __init__(self):
        self.results = []
        self.luna_process = None
        self.start_time = None

    def start_luna(self, timeout: int = 15) -> bool:
        self.start_time = time.time()
        self.luna_process = subprocess.Popen(
            ["./venv/bin/python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        for _ in range(timeout):
            time.sleep(1)
            if get_window_id():
                startup_time = time.time() - self.start_time
                self.results.append({"test": "startup", "passed": True, "time": startup_time, "threshold": 10.0})
                return True

        self.results.append({"test": "startup", "passed": False, "error": "Timeout waiting for window"})
        return False

    def stop_luna(self):
        if self.luna_process:
            self.luna_process.terminate()
            self.luna_process.wait(timeout=5)

    def check_element_visible(self, screenshot_path: str, expected_text: str) -> bool:
        if not OCR_AVAILABLE:
            return True

        try:
            img = Image.open(screenshot_path)
            text = pytesseract.image_to_string(img)
            return expected_text.lower() in text.lower()
        except Exception:
            return False

    def test_startup_screen(self) -> dict:
        state = capture_luna_state("startup")
        if not state["success"]:
            return {"test": "startup_screen", "passed": False, "error": state["error"]}

        checks = {"window_captured": state["success"], "screenshot_exists": Path(state["filepath"]).exists()}

        if OCR_AVAILABLE:
            checks["has_luna_text"] = self.check_element_visible(state["filepath"], "Luna")

        passed = all(checks.values())
        return {"test": "startup_screen", "passed": passed, "checks": checks, "screenshot": state["filepath"]}

    def test_animation_running(self) -> dict:
        screenshots = []
        for i in range(3):
            state = capture_luna_state(f"animation_{i}")
            if state["success"]:
                screenshots.append(state["filepath"])
            time.sleep(0.5)

        unique_files = len(set(open(s, "rb").read() for s in screenshots if Path(s).exists()))

        animation_running = unique_files > 1
        return {
            "test": "animation_running",
            "passed": animation_running,
            "unique_frames": unique_files,
            "total_captures": len(screenshots),
        }

    def run_full_suite(self) -> dict:
        report = {"timestamp": datetime.now().isoformat(), "tests": []}

        if not self.start_luna():
            report["tests"] = self.results
            report["summary"] = {"passed": 0, "failed": 1, "total": 1}
            return report

        time.sleep(3)

        report["tests"].append(self.test_startup_screen())
        report["tests"].append(self.test_animation_running())

        self.stop_luna()

        passed = sum(1 for t in report["tests"] if t.get("passed"))
        report["summary"] = {"passed": passed, "failed": len(report["tests"]) - passed, "total": len(report["tests"])}

        report_path = REPORT_DIR / f"visual_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report


def run_visual_qa():
    qa = VisualQA()
    report = qa.run_full_suite()

    print("\n" + "=" * 60)
    print("VISUAL QA REPORT")
    print("=" * 60)

    for test in report["tests"]:
        status = "PASS" if test.get("passed") else "FAIL"
        print(f"[{status}] {test['test']}")
        if not test.get("passed") and test.get("error"):
            print(f"       Error: {test['error']}")

    print("-" * 60)
    s = report["summary"]
    print(f"Total: {s['passed']}/{s['total']} passed")

    return report


if __name__ == "__main__":
    run_visual_qa()
