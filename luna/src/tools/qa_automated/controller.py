import asyncio
import logging

logger = logging.getLogger(__name__)


class LunaInteractiveController:
    def __init__(self):
        self.app = None
        self.pilot = None
        self._running = False

    async def start(self):
        from main import TemploDeLuna

        self.app = TemploDeLuna()
        self.app.skip_onboarding = True
        self._running = True

    async def send_keys(self, *keys: str):
        if self.pilot:
            for key in keys:
                await self.pilot.press(key)
                await self.pilot.pause()

    async def type_text(self, text: str):
        if self.pilot:
            for char in text:
                await self.pilot.press(char)
            await self.pilot.pause()

    async def click_button(self, button_id: str):
        if self.pilot:
            try:
                btn = self.pilot.app.query_one(f"#{button_id}")
                btn.press()
                await self.pilot.pause()
                return True
            except Exception:
                return False

    async def get_chat_messages(self) -> list[str]:
        if not self.pilot:
            return []
        try:
            from src.ui.widgets import ChatMessage

            chat_list = self.pilot.app.query_one("#chat-list")
            messages = chat_list.query(ChatMessage)
            return [msg.get_text_content() for msg in messages]
        except Exception:
            return []

    async def get_input_value(self) -> str:
        if not self.pilot:
            return ""
        try:
            return self.pilot.app.query_one("#main_input").value
        except Exception:
            return ""

    async def get_app_state(self) -> str:
        if not self.pilot:
            return "UNKNOWN"
        try:
            return self.pilot.app.app_state
        except Exception:
            return "UNKNOWN"

    async def run_interactive(self):
        async with self.app.run_test() as pilot:
            self.pilot = pilot
            await pilot.pause()

            print("\n=== Luna Interactive Controller ===")
            print("Comandos: tab, esc, f5, enter, quit")
            print("Ou digite texto para enviar ao input")
            print("=====================================\n")

            while self._running:
                try:
                    cmd = await asyncio.get_event_loop().run_in_executor(None, lambda: input("luna> ").strip())

                    if not cmd:
                        continue

                    if cmd == "quit" or cmd == "exit":
                        self._running = False
                        break

                    if cmd == "state":
                        print(f"App state: {await self.get_app_state()}")
                        continue

                    if cmd == "messages":
                        msgs = await self.get_chat_messages()
                        for i, m in enumerate(msgs):
                            print(f"[{i}] {m[:100]}...")
                        continue

                    if cmd == "input":
                        print(f"Input value: {await self.get_input_value()}")
                        continue

                    if cmd.startswith("click "):
                        btn_id = cmd.split(" ", 1)[1]
                        success = await self.click_button(btn_id)
                        print(f"Click {btn_id}: {'OK' if success else 'FALHOU'}")
                        continue

                    if cmd.startswith("type "):
                        text = cmd.split(" ", 1)[1]
                        await self.type_text(text)
                        print(f"Digitado: {text}")
                        continue

                    if cmd in ["tab", "esc", "escape", "enter", "space", "f5", "up", "down", "left", "right"]:
                        key = "escape" if cmd == "esc" else cmd
                        await self.send_keys(key)
                        print(f"Tecla enviada: {key}")
                        continue

                    if cmd.startswith("key "):
                        key = cmd.split(" ", 1)[1]
                        await self.send_keys(key)
                        print(f"Tecla enviada: {key}")
                        continue

                    await self.type_text(cmd)
                    await self.send_keys("enter")
                    print(f"Enviado: {cmd}")

                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Erro: {e}")

            self.pilot = None
