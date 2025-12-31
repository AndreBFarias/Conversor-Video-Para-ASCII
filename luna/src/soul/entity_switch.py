import asyncio
import csv
import json
import logging
import random
from datetime import datetime

import config
from src.core.entity_loader import get_active_entity

logger = logging.getLogger(__name__)

USER_DIR = config.APP_DIR / "src" / "data_memory" / "user"
PROFILE_PATH = USER_DIR / "profile.json"
SWITCH_CSV_PATH = config.APP_DIR / "src" / "assets" / "others" / "Entity-Switch-Intro.csv"


class EntitySwitchDialogues:
    def __init__(self, entity_id: str):
        self.steps = {}
        self.entity_id = entity_id
        self._load_csv()

    def _load_csv(self):
        if not SWITCH_CSV_PATH.exists():
            logger.warning(f"Entity switch CSV nao encontrado: {SWITCH_CSV_PATH}")
            return

        try:
            with open(SWITCH_CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ordem = int(row.get("Ordem", 0))
                        entidade = row.get("Entidade", "").strip()
                        conteudo = row.get("Conteudo", "").strip()
                        programa = row.get("Programa", "").strip()

                        if entidade == "TODOS" or entidade.lower() == self.entity_id.lower():
                            variacoes = self._parse_variacoes(conteudo)

                            if ordem not in self.steps or entidade.lower() == self.entity_id.lower():
                                self.steps[ordem] = {
                                    "variacoes": variacoes,
                                    "programa": programa,
                                }

                    except (ValueError, KeyError) as e:
                        logger.debug(f"Linha ignorada no CSV: {e}")
                        continue

            logger.info(f"Entity switch CSV carregado: {len(self.steps)} passos")
        except Exception as e:
            logger.error(f"Erro ao carregar CSV de entity switch: {e}")

    def _parse_variacoes(self, texto: str) -> list:
        if not texto:
            return [""]

        texto = texto.strip().strip('"')
        partes = texto.split("|")
        return [p.strip() for p in partes if p.strip()]

    def get_frase(self, ordem: int, nome: str = "Viajante") -> str:
        step = self.steps.get(ordem)
        if not step or not step["variacoes"]:
            return ""

        frase = random.choice(step["variacoes"])
        frase = frase.replace("$N", nome)
        frase = frase.replace("$NOME_DELE", nome)

        entity_name = self.entity_id.capitalize()
        frase = frase.replace("$E", entity_name)
        frase = frase.replace("$ENTIDADE", entity_name)

        return frase


class EntitySwitchIntro:
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.user_name = self._get_user_name()

    def _get_user_name(self) -> str:
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("nome", "Viajante")
        except Exception as e:
            logger.debug(f"Erro ao ler nome do usuario: {e}")
        return "Viajante"

    def _get_last_entity(self) -> str:
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_entity", None)
        except Exception as e:
            logger.debug(f"Erro ao ler ultima entidade: {e}")
        return None

    def _get_known_entities(self) -> list:
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("known_entities", [])
        except Exception as e:
            logger.debug(f"Erro ao ler entidades conhecidas: {e}")
        return []

    def _get_pending_intro(self) -> str:
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("pending_entity_intro", None)
        except Exception as e:
            logger.debug(f"Erro ao ler intro pendente: {e}")
        return None

    def _clear_pending_intro(self):
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)

                if "pending_entity_intro" in data:
                    del data["pending_entity_intro"]
                    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    logger.debug("Pending entity intro limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar pending intro: {e}")

    def _save_known_entity(self, entity_id: str):
        try:
            current = {}
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    current = json.load(f)

            known = current.get("known_entities", [])
            if entity_id not in known:
                known.append(entity_id)

            current["known_entities"] = known
            current["active_entity"] = entity_id
            current["last_entity_switch"] = datetime.now().isoformat()

            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)

            logger.info(f"Entidade {entity_id} salva como conhecida")
        except Exception as e:
            logger.error(f"Erro ao salvar entidade conhecida: {e}")

    def _get_voice_preference(self) -> bool:
        try:
            if PROFILE_PATH.exists():
                with open(PROFILE_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("preferencias", {}).get("permite_voz", True)
        except Exception as e:
            logger.debug(f"Erro ao ler preferencia de voz: {e}")
        return True

    def _activate_voice_mode(self):
        if hasattr(self.app, "em_chamada"):
            self.app.em_chamada = True
            logger.debug("[ENTITY_SWITCH] em_chamada ativado")

    def needs_intro(self, new_entity_id: str) -> bool:
        pending = self._get_pending_intro()

        if pending and pending == new_entity_id:
            logger.debug(f"Intro pendente detectado para: {new_entity_id}")
            return True

        if self.is_first_meeting(new_entity_id):
            logger.debug(f"Primeiro encontro detectado com: {new_entity_id}")
            return True

        return False

    def is_first_meeting(self, entity_id: str) -> bool:
        known_entities = self._get_known_entities()
        return entity_id not in known_entities

    async def run_intro(self, new_entity_id: str):
        if self.is_running:
            logger.warning("Intro de entidade ja em execucao")
            return

        self.is_running = True
        logger.info(f"Iniciando introducao para entidade: {new_entity_id}")

        try:
            dialogues = EntitySwitchDialogues(new_entity_id)
            is_first = self.is_first_meeting(new_entity_id)

            if hasattr(self.app, "threading_manager") and self.app.threading_manager:
                self.app.threading_manager.listening_event.clear()
                logger.debug("[ENTITY_SWITCH] Escuta pausada")

            frase_saudacao = dialogues.get_frase(1, self.user_name)
            if frase_saudacao:
                await self._falar(frase_saudacao)

            if is_first:
                frase_persona = dialogues.get_frase(2, self.user_name)
                if frase_persona:
                    await asyncio.sleep(0.5)
                    await self._falar(frase_persona)

            frase_final = dialogues.get_frase(3, self.user_name)
            if frase_final:
                await asyncio.sleep(0.5)
                await self._falar(frase_final)

            self._save_known_entity(new_entity_id)
            self._clear_pending_intro()

            if hasattr(self.app, "threading_manager") and self.app.threading_manager:
                self.app.threading_manager.listening_event.set()
                logger.debug("[ENTITY_SWITCH] Escuta retomada")

            if self._get_voice_preference():
                self._activate_voice_mode()
                logger.info("[ENTITY_SWITCH] Modo de voz ativado")

            logger.info(f"Introducao de {new_entity_id} concluida")

        except Exception as e:
            logger.error(f"Erro na introducao de entidade: {e}", exc_info=True)
        finally:
            self.is_running = False

    async def _falar(self, texto: str):
        if not texto:
            return

        entity_id = get_active_entity()
        self.app.add_chat_entry(entity_id, texto)

        if hasattr(self.app, "boca") and self.app.boca:
            try:
                loop = asyncio.get_running_loop()

                if hasattr(self.app, "threading_manager") and self.app.threading_manager:
                    self.app.threading_manager.luna_speaking_event.set()

                try:
                    await loop.run_in_executor(None, self.app.boca.falar, texto)
                finally:
                    if hasattr(self.app, "threading_manager") and self.app.threading_manager:
                        self.app.threading_manager.luna_speaking_event.clear()

            except Exception as e:
                logger.error(f"Erro TTS entity switch: {e}")
                if hasattr(self.app, "threading_manager") and self.app.threading_manager:
                    self.app.threading_manager.luna_speaking_event.clear()


def get_entity_switch_intro(app) -> EntitySwitchIntro:
    return EntitySwitchIntro(app)
