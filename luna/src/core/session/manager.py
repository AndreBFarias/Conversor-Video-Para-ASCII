import asyncio
import json
import logging
import os
import uuid
from datetime import datetime

import config
from src.core.entity_loader import get_active_entity, get_entity_name

from .summary import generate_title_for_session, generate_live_summary_background

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, app):
        self.app = app
        self.current_session_id = None
        self.conversation_history = []
        self._user_message_count = 0
        self._summary_interval = 2
        self._current_summary = None

    def on_message_added(self, role: str):
        if role == "user":
            self._user_message_count += 1
            if (
                self._user_message_count >= self._summary_interval
                and self._user_message_count % self._summary_interval == 0
            ):
                self._generate_live_summary()

    def _generate_live_summary(self):
        if len(self.conversation_history) < 2:
            return

        def on_summary_ready(summary: str):
            if summary:
                self._current_summary = summary
                self._update_manifest_title(summary)
                logger.info(f"Resumo atualizado: {summary}")

        generate_live_summary_background(self.conversation_history, on_summary_ready)

    def _update_manifest_title(self, title: str):
        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())

        manifest = {}
        if os.path.exists(config.MANIFEST_FILE):
            try:
                with open(config.MANIFEST_FILE, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, Exception):
                manifest = {}

        manifest[self.current_session_id] = {"title": title, "date": datetime.now().isoformat()}

        try:
            with open(config.MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao atualizar manifesto: {e}")

    def reset_message_count(self):
        self._user_message_count = 0
        self._current_summary = None

    def load_session(self, session_id: str):
        session_file = os.path.join(config.SESSIONS_DIR, f"{session_id}.json")
        chat_list = self.app.query_one("#chat-list")
        logger.info(f"Tentando carregar sessao de {session_file}")
        try:
            with open(session_file, encoding="utf-8") as f:
                history = json.load(f)
            self.current_session_id = session_id

            asyncio.create_task(chat_list.remove_children())

            self.conversation_history = history
            logger.info(f"Renderizando {len(history)} turnos da sessao carregada...")

            for i, turn in enumerate(history):
                try:
                    role = turn.get("role", "user")
                    parts_data = turn.get("parts", [])

                    if parts_data and isinstance(parts_data[0], str):
                        text_content = parts_data[0]
                        if role == "user":
                            text_content = text_content.split("--- CONTEUDO DO ARQUIVO ANEXADO ---")[0].strip()
                        parts = [("text", text_content, None)]
                    else:
                        parts = parts_data

                    self.app.add_chat_entry(role, parts=parts, restore=True)

                except Exception as e:
                    logger.error(f"Erro ao renderizar turno {i} da sessao {session_id}: {e}", exc_info=True)
                    self.app.add_chat_entry("kernel", f"--- Erro ao renderizar turno {i+1} ---")

            self.app.add_chat_entry("kernel", "--- Conversa restaurada. ---")
            self.app.query_one("#main_input").focus()
            logger.info(f"Sessao {session_id} carregada com sucesso.")

        except FileNotFoundError:
            logger.error(f"Arquivo da sessao nao encontrado: {session_file}")
            self.app.add_chat_entry("kernel", f"Erro: Arquivo da sessao '{session_id}' nao encontrado.")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Erro ao decodificar JSON da sessao '{session_id}': {e}", exc_info=True)
            self.app.add_chat_entry("kernel", f"Erro ao ler o arquivo da sessao '{session_id}'. Arquivo corrompido?")
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar sessao '{session_id}': {e}", exc_info=True)
            self.app.add_chat_entry("kernel", "Erro inesperado ao carregar a sessao.")

    async def save_current_session(self, gemini_error=None):
        history_to_save = self.conversation_history
        if not history_to_save:
            logger.info("Nenhum historico para salvar.")
            return
        logger.info("Preparando para salvar sessao...")
        history_for_saving = [
            turn
            for turn in history_to_save
            if not (
                turn.get("role") == "user"
                and isinstance(turn.get("parts"), list)
                and turn["parts"]
                and "--- CONTEUDO DO ARQUIVO ANEXADO ---" in str(turn["parts"][0])
            )
        ]
        if not history_for_saving:
            logger.info("Historico contem apenas prompts internos, nada a salvar.")
            return

        title = f"Dialogo de {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        user_messages = [t for t in history_for_saving if t.get("role") == "user"]

        if len(user_messages) >= 2:
            generated_title = await generate_title_for_session(history_for_saving, gemini_error)
            if generated_title:
                title = generated_title
        else:
            logger.debug("Menos de 2 mensagens do usuario, mantendo titulo padrao de data.")

        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())
            logger.info(f"Criando novo ID de sessao: {self.current_session_id}")

        session_filename = os.path.join(config.SESSIONS_DIR, f"{self.current_session_id}.json")
        logger.info(f"Salvando sessao em: {session_filename}")
        try:
            with open(session_filename, "w", encoding="utf-8") as f:
                json.dump(history_for_saving, f, indent=2, ensure_ascii=False)
            logger.info(f"Sessao salva com {len(history_for_saving)} turnos.")
        except Exception as e:
            logger.error(f"Falha ao salvar o arquivo da sessao '{session_filename}': {e}")
            return

        manifest = {}
        logger.debug(f"Atualizando manifesto: {config.MANIFEST_FILE}")
        if os.path.exists(config.MANIFEST_FILE):
            try:
                with open(config.MANIFEST_FILE, encoding="utf-8") as f:
                    manifest = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Manifesto corrompido em {config.MANIFEST_FILE}. Recriando.")
                manifest = {}
            except Exception as e:
                logger.error(f"Erro ao ler manifesto {config.MANIFEST_FILE}: {e}")
        manifest[self.current_session_id] = {"title": title, "date": datetime.now().isoformat()}
        try:
            with open(config.MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.debug("Manifesto atualizado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao salvar o arquivo de manifesto '{config.MANIFEST_FILE}': {e}")
