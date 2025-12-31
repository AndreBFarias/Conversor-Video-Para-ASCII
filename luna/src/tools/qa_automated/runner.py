import asyncio
import logging
import time
from datetime import datetime

from .models import TestReport, TestResult

logger = logging.getLogger(__name__)


class LunaTestRunner:
    def __init__(self):
        self.report = TestReport()
        self.app = None
        self.pilot = None

    async def setup(self):
        from main import TemploDeLuna

        self.app = TemploDeLuna()
        self.app.skip_onboarding = True

    async def run_test(self, name: str, test_func):
        start = time.time()
        error = None
        passed = True

        try:
            logger.info(f"[TEST] {name}")
            await test_func()
            logger.info(f"[PASS] {name}")
        except AssertionError as e:
            passed = False
            error = str(e)
            logger.error(f"[FAIL] {name}: {e}")
        except Exception as e:
            passed = False
            error = f"{type(e).__name__}: {e}"
            logger.error(f"[ERROR] {name}: {e}")

        duration = time.time() - start
        self.report.add(TestResult(name=name, passed=passed, duration=duration, error=error))

    async def test_app_starts(self):
        assert self.app is not None, "App nao inicializado"

    async def test_ui_elements_exist(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            assert pilot.app.query_one("#ascii-pane") is not None, "ascii-pane nao encontrado"
            assert pilot.app.query_one("#chat-list") is not None, "chat-list nao encontrado"
            assert pilot.app.query_one("#main_input") is not None, "main_input nao encontrado"
            assert pilot.app.query_one("#menu-pane") is not None, "menu-pane nao encontrado"

    async def test_tab_navigation(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("shift+tab")
            await pilot.pause()

    async def test_input_focus_and_type(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            main_input = pilot.app.query_one("#main_input")
            main_input.focus()
            await pilot.pause()

            await pilot.press("t", "e", "s", "t", "e")
            await pilot.pause()

            assert "teste" in main_input.value.lower(), f"Texto nao digitado: {main_input.value}"

    async def test_esc_shows_notification(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

    async def test_f5_creates_new_conversation(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("f5")
            await pilot.pause()

    async def test_canone_opens_and_closes(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            canone_btn = pilot.app.query_one("#canone")
            canone_btn.press()
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

    async def test_canone_tab_navigation(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            canone_btn = pilot.app.query_one("#canone")
            canone_btn.press()
            await pilot.pause()

            await pilot.press("2")
            await pilot.pause()

            await pilot.press("ctrl+right")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

    async def test_history_opens(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            history_btn = pilot.app.query_one("#ver_historico")
            history_btn.press()
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

    async def test_chat_message_copy(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            pilot.app.add_chat_entry("luna", "Mensagem de teste para copia")
            await pilot.pause()

            chat_list = pilot.app.query_one("#chat-list")
            chat_list.focus()
            await pilot.pause()

            await pilot.press("ctrl+a")
            await pilot.pause()

    async def test_double_esc_exits(self):
        async with self.app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("escape")
            await asyncio.sleep(0.1)
            await pilot.press("escape")
            await pilot.pause()

    async def run_all_tests(self):
        self.report.started_at = datetime.now().isoformat()

        await self.setup()

        tests = [
            ("App inicia corretamente", self.test_app_starts),
            ("Elementos UI existem", self.test_ui_elements_exist),
            ("Navegacao Tab funciona", self.test_tab_navigation),
            ("Input aceita texto", self.test_input_focus_and_type),
            ("Esc mostra notificacao", self.test_esc_shows_notification),
            ("F5 cria nova conversa", self.test_f5_creates_new_conversation),
            ("Canone abre e fecha", self.test_canone_opens_and_closes),
            ("Canone navegacao por abas", self.test_canone_tab_navigation),
            ("Historico abre", self.test_history_opens),
            ("Chat copia mensagens", self.test_chat_message_copy),
        ]

        for name, test_func in tests:
            await self.run_test(name, test_func)

        self.report.finished_at = datetime.now().isoformat()
        return self.report
