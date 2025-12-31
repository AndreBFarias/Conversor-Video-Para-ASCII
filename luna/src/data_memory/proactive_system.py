import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProactiveTrigger:
    trigger_type: str
    message: str
    priority: int = 1
    entity_id: str = "luna"
    metadata: dict[str, Any] = field(default_factory=dict)


class ProactiveSystem:
    def __init__(self, entity_id: str, storage_dir: Path | None = None):
        self.entity_id = entity_id

        if storage_dir is None:
            from config import APP_DIR

            storage_dir = APP_DIR / "src" / "data_memory" / "proactive"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.storage_dir / f"{entity_id}_patterns.json"
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> dict:
        if self.patterns_file.exists():
            try:
                return json.loads(self.patterns_file.read_text())
            except Exception as e:
                logger.warning(f"Erro ao carregar patterns: {e}")
        return {
            "interaction_times": [],
            "mentioned_dates": [],
            "last_sentiments": [],
            "last_interaction": None,
        }

    def _save_patterns(self) -> None:
        try:
            self.patterns_file.write_text(json.dumps(self.patterns, indent=2))
        except Exception as e:
            logger.error(f"Erro ao salvar patterns: {e}")

    def record_interaction(self, timestamp: datetime | None = None, sentiment: float = 0.0) -> None:
        if timestamp is None:
            timestamp = datetime.now()

        hour = timestamp.hour
        self.patterns["interaction_times"].append(hour)
        self.patterns["interaction_times"] = self.patterns["interaction_times"][-100:]

        self.patterns["last_sentiments"].append(
            {
                "timestamp": timestamp.isoformat(),
                "sentiment": sentiment,
            }
        )
        self.patterns["last_sentiments"] = self.patterns["last_sentiments"][-20:]

        self.patterns["last_interaction"] = timestamp.isoformat()

        self._save_patterns()
        logger.debug(f"Interacao registrada: hora={hour}, sentiment={sentiment:.2f}")

    def record_date_mention(self, date_str: str, context: str) -> None:
        self.patterns["mentioned_dates"].append(
            {
                "date": date_str,
                "context": context,
                "recorded_at": datetime.now().isoformat(),
            }
        )
        self.patterns["mentioned_dates"] = self.patterns["mentioned_dates"][-50:]
        self._save_patterns()
        logger.info(f"Data registrada: {date_str} - {context[:30]}...")

    def extract_dates_from_text(self, text: str) -> list[tuple[str, str]]:
        patterns = [
            (r"dia (\d{1,2})", "day"),
            (r"(\d{1,2})/(\d{1,2})", "date_slash"),
            (
                r"(\d{1,2}) de (janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)",
                "date_month",
            ),
            (r"\b(amanha)\b", "tomorrow"),
            (r"\b(depois de amanha)\b", "day_after"),
            (r"proxim[ao] (segunda|terca|quarta|quinta|sexta|sabado|domingo)", "next_weekday"),
        ]

        dates = []
        text_lower = text.lower()

        for pattern, date_type in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        dates.append((" ".join(match), date_type))
                    else:
                        dates.append((str(match), date_type))

        return dates

    def check_triggers(self) -> list[ProactiveTrigger]:
        triggers = []

        triggers.extend(self._check_time_patterns())
        triggers.extend(self._check_date_mentions())
        triggers.extend(self._check_emotional_followup())
        triggers.extend(self._check_absence())

        triggers.sort(key=lambda t: t.priority, reverse=True)

        return triggers

    def _check_time_patterns(self) -> list[ProactiveTrigger]:
        triggers = []

        interaction_times = self.patterns.get("interaction_times", [])
        if len(interaction_times) < 10:
            return triggers

        hour_counts = Counter(interaction_times)
        most_common_hour, count = hour_counts.most_common(1)[0]

        if count / len(interaction_times) > 0.3:
            current_hour = datetime.now().hour

            if current_hour == most_common_hour + 1:
                last = self.patterns.get("last_interaction")
                if last:
                    try:
                        last_dt = datetime.fromisoformat(last)
                        if last_dt.date() < datetime.now().date():
                            triggers.append(
                                ProactiveTrigger(
                                    trigger_type="time_pattern",
                                    message=f"Voce costuma falar comigo por volta das {most_common_hour}h. Tudo bem hoje?",
                                    priority=2,
                                    entity_id=self.entity_id,
                                    metadata={"expected_hour": most_common_hour},
                                )
                            )
                    except Exception as e:
                        logger.debug(f"Erro ao processar padrao de hora: {e}")

        return triggers

    def _check_date_mentions(self) -> list[ProactiveTrigger]:
        triggers = []
        today = datetime.now().date()

        mentioned_dates = self.patterns.get("mentioned_dates", [])
        processed_indices = []

        for i, mention in enumerate(mentioned_dates):
            try:
                date_str = mention.get("date", "")
                context = mention.get("context", "")

                match = re.search(r"(\d{1,2})", date_str)
                if match:
                    day = int(match.group(1))
                    if day == today.day:
                        triggers.append(
                            ProactiveTrigger(
                                trigger_type="date_mention",
                                message=f"Lembrei que voce mencionou algo para hoje: {context[:50]}...",
                                priority=3,
                                entity_id=self.entity_id,
                                metadata={"original_context": context},
                            )
                        )
                        processed_indices.append(i)
            except Exception as e:
                logger.debug(f"Erro ao processar data: {e}")

        for i in sorted(processed_indices, reverse=True):
            self.patterns["mentioned_dates"].pop(i)

        if processed_indices:
            self._save_patterns()

        return triggers

    def _check_emotional_followup(self) -> list[ProactiveTrigger]:
        triggers = []

        sentiments = self.patterns.get("last_sentiments", [])
        if len(sentiments) < 1:
            return triggers

        last = sentiments[-1]
        if last.get("sentiment", 0) < -0.3:
            try:
                last_dt = datetime.fromisoformat(last["timestamp"])
                hours_ago = (datetime.now() - last_dt).total_seconds() / 3600

                if 12 < hours_ago < 48:
                    triggers.append(
                        ProactiveTrigger(
                            trigger_type="emotional_followup",
                            message="Da ultima vez voce parecia um pouco pra baixo. Como esta se sentindo agora?",
                            priority=2,
                            entity_id=self.entity_id,
                            metadata={"last_sentiment": last.get("sentiment")},
                        )
                    )
            except Exception as e:
                logger.debug(f"Erro ao processar followup emocional: {e}")

        return triggers

    def _check_absence(self) -> list[ProactiveTrigger]:
        triggers = []

        last = self.patterns.get("last_interaction")
        if not last:
            return triggers

        try:
            last_dt = datetime.fromisoformat(last)
            days_ago = (datetime.now() - last_dt).days

            if days_ago >= 3:
                triggers.append(
                    ProactiveTrigger(
                        trigger_type="absence",
                        message=f"Faz {days_ago} dias que nao nos falamos. Senti sua falta.",
                        priority=1,
                        entity_id=self.entity_id,
                        metadata={"days_absent": days_ago},
                    )
                )
        except Exception as e:
            logger.debug(f"Erro ao verificar ausencia: {e}")

        return triggers

    def get_pattern_stats(self) -> dict:
        interaction_times = self.patterns.get("interaction_times", [])
        sentiments = self.patterns.get("last_sentiments", [])

        stats = {
            "total_interactions": len(interaction_times),
            "mentioned_dates_pending": len(self.patterns.get("mentioned_dates", [])),
            "last_interaction": self.patterns.get("last_interaction"),
        }

        if interaction_times:
            hour_counts = Counter(interaction_times)
            most_common = hour_counts.most_common(3)
            stats["common_hours"] = most_common

        if sentiments:
            avg_sentiment = sum(s.get("sentiment", 0) for s in sentiments) / len(sentiments)
            stats["avg_sentiment"] = round(avg_sentiment, 2)

        return stats


_systems: dict[str, ProactiveSystem] = {}


def get_proactive_system(entity_id: str) -> ProactiveSystem:
    if entity_id not in _systems:
        _systems[entity_id] = ProactiveSystem(entity_id)
    return _systems[entity_id]
