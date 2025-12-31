import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)


class TimeGroup(Enum):
    TODAY = "Hoje"
    YESTERDAY = "Ontem"
    THIS_WEEK = "Esta Semana"
    THIS_MONTH = "Este Mes"
    OLDER = "Anteriores"


@dataclass
class SessionSummary:
    session_id: str
    title: str
    date: datetime
    preview: str
    message_count: int
    entity_id: str | None
    time_group: TimeGroup

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "date": self.date.isoformat(),
            "preview": self.preview,
            "message_count": self.message_count,
            "entity_id": self.entity_id,
            "time_group": self.time_group.value,
        }


class SessionHistoryManager:
    def __init__(self, sessions_dir: Path = None, manifest_file: Path = None):
        self.sessions_dir = sessions_dir or config.SESSIONS_DIR
        self.manifest_file = manifest_file or config.MANIFEST_FILE
        self._cache: dict[str, SessionSummary] = {}
        self._cache_valid = False

    def _get_time_group(self, dt: datetime) -> TimeGroup:
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        if dt >= today:
            return TimeGroup.TODAY
        elif dt >= yesterday:
            return TimeGroup.YESTERDAY
        elif dt >= week_start:
            return TimeGroup.THIS_WEEK
        elif dt >= month_start:
            return TimeGroup.THIS_MONTH
        else:
            return TimeGroup.OLDER

    def _extract_preview(self, session_data: list[dict]) -> str:
        for turn in session_data[:3]:
            if turn.get("role") == "user":
                parts = turn.get("parts", [])
                if parts:
                    first_part = parts[0]
                    if isinstance(first_part, str):
                        text = first_part
                    elif isinstance(first_part, dict):
                        text = first_part.get("text", "")
                    else:
                        continue

                    text = text.split("--- CONTEUDO DO ARQUIVO ANEXADO ---")[0].strip()
                    if len(text) > 100:
                        text = text[:100] + "..."
                    return text
        return ""

    def _extract_entity_id(self, session_data: list[dict]) -> str | None:
        for turn in session_data:
            metadata = turn.get("metadata", {})
            if "entity_id" in metadata:
                return metadata["entity_id"]
        return None

    def _load_session_file(self, session_id: str) -> list[dict] | None:
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Erro ao ler sessao {session_id}: {e}")
            return None

    def _build_summary(self, session_id: str, manifest_entry: dict) -> SessionSummary | None:
        try:
            date = datetime.fromisoformat(manifest_entry["date"])
            title = manifest_entry.get("title", "Sem titulo")

            session_data = self._load_session_file(session_id)

            if session_data:
                preview = self._extract_preview(session_data)
                message_count = len(session_data)
                entity_id = self._extract_entity_id(session_data)
            else:
                preview = ""
                message_count = 0
                entity_id = None

            return SessionSummary(
                session_id=session_id,
                title=title,
                date=date,
                preview=preview,
                message_count=message_count,
                entity_id=entity_id,
                time_group=self._get_time_group(date),
            )
        except Exception as e:
            logger.error(f"Erro ao criar resumo para sessao {session_id}: {e}")
            return None

    def _load_manifest(self) -> dict:
        if not self.manifest_file.exists():
            return {}

        try:
            with open(self.manifest_file, encoding="utf-8") as f:
                manifest = json.load(f)
                return {k: v for k, v in manifest.items() if isinstance(v, dict) and "date" in v and "title" in v}
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Erro ao ler manifesto: {e}")
            return {}

    def refresh_cache(self) -> None:
        manifest = self._load_manifest()
        self._cache.clear()

        for session_id, entry in manifest.items():
            summary = self._build_summary(session_id, entry)
            if summary:
                self._cache[session_id] = summary

        self._cache_valid = True
        logger.info(f"Cache de historico atualizado: {len(self._cache)} sessoes")

    def get_all_sessions(self, force_refresh: bool = False) -> list[SessionSummary]:
        if not self._cache_valid or force_refresh:
            self.refresh_cache()

        sessions = list(self._cache.values())
        sessions.sort(key=lambda s: s.date, reverse=True)
        return sessions

    def get_sessions_grouped(self, force_refresh: bool = False) -> dict[TimeGroup, list[SessionSummary]]:
        sessions = self.get_all_sessions(force_refresh)

        grouped: dict[TimeGroup, list[SessionSummary]] = {
            TimeGroup.TODAY: [],
            TimeGroup.YESTERDAY: [],
            TimeGroup.THIS_WEEK: [],
            TimeGroup.THIS_MONTH: [],
            TimeGroup.OLDER: [],
        }

        for session in sessions:
            grouped[session.time_group].append(session)

        return grouped

    def search_sessions(self, query: str, limit: int = 20) -> list[SessionSummary]:
        if not self._cache_valid:
            self.refresh_cache()

        query_lower = query.lower().strip()
        if not query_lower:
            return self.get_all_sessions()[:limit]

        results = []
        for session in self._cache.values():
            score = 0

            if query_lower in session.title.lower():
                score += 10
            if query_lower in session.preview.lower():
                score += 5

            if score > 0:
                results.append((score, session))

        results.sort(key=lambda x: (-x[0], -x[1].date.timestamp()))
        return [s for _, s in results[:limit]]

    def get_session_by_id(self, session_id: str) -> SessionSummary | None:
        if not self._cache_valid:
            self.refresh_cache()
        return self._cache.get(session_id)

    def get_session_content(self, session_id: str) -> list[dict] | None:
        return self._load_session_file(session_id)

    def delete_session(self, session_id: str) -> bool:
        session_file = self.sessions_dir / f"{session_id}.json"

        try:
            if session_file.exists():
                session_file.unlink()

            manifest = self._load_manifest()
            if session_id in manifest:
                del manifest[session_id]
                with open(self.manifest_file, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)

            if session_id in self._cache:
                del self._cache[session_id]

            logger.info(f"Sessao {session_id} deletada")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar sessao {session_id}: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        if not self._cache_valid:
            self.refresh_cache()

        grouped = self.get_sessions_grouped()
        total_messages = sum(s.message_count for s in self._cache.values())

        return {
            "total_sessions": len(self._cache),
            "total_messages": total_messages,
            "today": len(grouped[TimeGroup.TODAY]),
            "this_week": len(grouped[TimeGroup.THIS_WEEK]),
            "this_month": len(grouped[TimeGroup.THIS_MONTH]),
            "older": len(grouped[TimeGroup.OLDER]),
        }


_history_manager: SessionHistoryManager | None = None


def get_session_history() -> SessionHistoryManager:
    global _history_manager
    if _history_manager is None:
        _history_manager = SessionHistoryManager()
    return _history_manager
