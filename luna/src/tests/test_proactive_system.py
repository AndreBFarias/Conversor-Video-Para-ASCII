import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


class TestProactiveTrigger:
    def test_default_values(self):
        from src.data_memory.proactive_system import ProactiveTrigger

        trigger = ProactiveTrigger(trigger_type="test", message="Test message")

        assert trigger.trigger_type == "test"
        assert trigger.message == "Test message"
        assert trigger.priority == 1
        assert trigger.entity_id == "luna"
        assert trigger.metadata == {}

    def test_custom_values(self):
        from src.data_memory.proactive_system import ProactiveTrigger

        trigger = ProactiveTrigger(
            trigger_type="absence",
            message="Senti falta",
            priority=3,
            entity_id="eris",
            metadata={"days": 5},
        )

        assert trigger.priority == 3
        assert trigger.entity_id == "eris"
        assert trigger.metadata["days"] == 5


class TestProactiveSystemInit:
    def test_creates_storage_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            storage_dir = Path(tmpdir) / "subdir" / "proactive"
            system = ProactiveSystem("luna", storage_dir=storage_dir)

            assert storage_dir.exists()
            assert system.entity_id == "luna"

    def test_loads_empty_patterns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            assert system.patterns["interaction_times"] == []
            assert system.patterns["mentioned_dates"] == []
            assert system.patterns["last_sentiments"] == []
            assert system.patterns["last_interaction"] is None

    def test_loads_existing_patterns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            patterns_file = Path(tmpdir) / "luna_patterns.json"
            patterns_file.write_text(
                json.dumps(
                    {
                        "interaction_times": [8, 9, 10],
                        "mentioned_dates": [],
                        "last_sentiments": [],
                        "last_interaction": "2024-01-15T10:00:00",
                    }
                )
            )

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            assert system.patterns["interaction_times"] == [8, 9, 10]
            assert system.patterns["last_interaction"] == "2024-01-15T10:00:00"


class TestRecordInteraction:
    def test_records_hour(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            timestamp = datetime(2024, 1, 15, 14, 30, 0)

            system.record_interaction(timestamp=timestamp, sentiment=0.5)

            assert 14 in system.patterns["interaction_times"]

    def test_records_sentiment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.record_interaction(sentiment=-0.5)

            assert len(system.patterns["last_sentiments"]) == 1
            assert system.patterns["last_sentiments"][0]["sentiment"] == -0.5

    def test_limits_interaction_times(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            for i in range(150):
                system.record_interaction()

            assert len(system.patterns["interaction_times"]) == 100

    def test_limits_sentiments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            for i in range(30):
                system.record_interaction(sentiment=0.1 * i)

            assert len(system.patterns["last_sentiments"]) == 20

    def test_persists_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.record_interaction(sentiment=0.8)

            assert system.patterns_file.exists()
            data = json.loads(system.patterns_file.read_text())
            assert len(data["last_sentiments"]) == 1


class TestRecordDateMention:
    def test_records_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.record_date_mention("dia 28", "reuniao importante")

            assert len(system.patterns["mentioned_dates"]) == 1
            assert system.patterns["mentioned_dates"][0]["date"] == "dia 28"
            assert "reuniao" in system.patterns["mentioned_dates"][0]["context"]

    def test_limits_dates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            for i in range(60):
                system.record_date_mention(f"dia {i}", f"evento {i}")

            assert len(system.patterns["mentioned_dates"]) == 50


class TestExtractDatesFromText:
    def test_extracts_day_number(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            dates = system.extract_dates_from_text("tenho reuniao dia 15")

            assert len(dates) >= 1
            assert any("15" in d[0] for d in dates)

    def test_extracts_slash_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            dates = system.extract_dates_from_text("encontro marcado para 25/12")

            assert len(dates) >= 1

    def test_extracts_tomorrow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            dates = system.extract_dates_from_text("amanha tenho prova")

            assert len(dates) >= 1
            assert any("amanha" in d[0] for d in dates)

    def test_extracts_month_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            dates = system.extract_dates_from_text("viagem 15 de janeiro")

            assert len(dates) >= 1

    def test_no_dates_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            dates = system.extract_dates_from_text("ola como vai voce")

            assert dates == []


class TestCheckTimePatterns:
    def test_no_trigger_with_few_interactions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.patterns["interaction_times"] = [8, 8, 8]

            triggers = system._check_time_patterns()

            assert len(triggers) == 0

    def test_detects_common_hour_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            current_hour = datetime.now().hour
            expected_hour = current_hour - 1

            system.patterns["interaction_times"] = [expected_hour] * 10
            system.patterns["last_interaction"] = (datetime.now() - timedelta(days=1)).isoformat()

            triggers = system._check_time_patterns()

            assert len(triggers) == 1
            assert triggers[0].trigger_type == "time_pattern"


class TestCheckDateMentions:
    def test_triggers_for_today(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            today_day = datetime.now().day
            system.patterns["mentioned_dates"] = [
                {
                    "date": f"dia {today_day}",
                    "context": "reuniao muito importante",
                    "recorded_at": datetime.now().isoformat(),
                }
            ]

            triggers = system._check_date_mentions()

            assert len(triggers) == 1
            assert triggers[0].trigger_type == "date_mention"
            assert "reuniao" in triggers[0].message

    def test_no_trigger_for_other_day(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            other_day = (datetime.now().day % 28) + 1
            system.patterns["mentioned_dates"] = [
                {
                    "date": f"dia {other_day}",
                    "context": "evento futuro",
                    "recorded_at": datetime.now().isoformat(),
                }
            ]

            triggers = system._check_date_mentions()

            assert len(triggers) == 0

    def test_removes_processed_dates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            today_day = datetime.now().day
            system.patterns["mentioned_dates"] = [
                {
                    "date": f"dia {today_day}",
                    "context": "evento hoje",
                    "recorded_at": datetime.now().isoformat(),
                }
            ]

            system._check_date_mentions()

            assert len(system.patterns["mentioned_dates"]) == 0


class TestCheckEmotionalFollowup:
    def test_triggers_after_negative_sentiment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.patterns["last_sentiments"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=20)).isoformat(),
                    "sentiment": -0.5,
                }
            ]

            triggers = system._check_emotional_followup()

            assert len(triggers) == 1
            assert triggers[0].trigger_type == "emotional_followup"

    def test_no_trigger_if_too_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.patterns["last_sentiments"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "sentiment": -0.5,
                }
            ]

            triggers = system._check_emotional_followup()

            assert len(triggers) == 0

    def test_no_trigger_if_too_old(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.patterns["last_sentiments"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=60)).isoformat(),
                    "sentiment": -0.5,
                }
            ]

            triggers = system._check_emotional_followup()

            assert len(triggers) == 0

    def test_no_trigger_if_positive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            system.patterns["last_sentiments"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=20)).isoformat(),
                    "sentiment": 0.5,
                }
            ]

            triggers = system._check_emotional_followup()

            assert len(triggers) == 0


class TestCheckAbsence:
    def test_triggers_after_3_days(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.patterns["last_interaction"] = (datetime.now() - timedelta(days=5)).isoformat()

            triggers = system._check_absence()

            assert len(triggers) == 1
            assert triggers[0].trigger_type == "absence"
            assert "5 dias" in triggers[0].message

    def test_no_trigger_if_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.patterns["last_interaction"] = (datetime.now() - timedelta(days=1)).isoformat()

            triggers = system._check_absence()

            assert len(triggers) == 0

    def test_no_trigger_without_last_interaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            triggers = system._check_absence()

            assert len(triggers) == 0


class TestCheckTriggers:
    def test_returns_sorted_by_priority(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            today_day = datetime.now().day
            system.patterns["mentioned_dates"] = [
                {
                    "date": f"dia {today_day}",
                    "context": "evento importante",
                    "recorded_at": datetime.now().isoformat(),
                }
            ]
            system.patterns["last_interaction"] = (datetime.now() - timedelta(days=5)).isoformat()

            triggers = system.check_triggers()

            assert len(triggers) >= 2
            assert triggers[0].priority >= triggers[-1].priority

    def test_empty_if_no_triggers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.patterns["last_interaction"] = datetime.now().isoformat()

            triggers = system.check_triggers()

            assert triggers == []


class TestGetPatternStats:
    def test_returns_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))

            for _ in range(5):
                system.record_interaction(sentiment=0.5)

            stats = system.get_pattern_stats()

            assert stats["total_interactions"] == 5
            assert "avg_sentiment" in stats
            assert stats["avg_sentiment"] == 0.5

    def test_common_hours(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem

            system = ProactiveSystem("luna", storage_dir=Path(tmpdir))
            system.patterns["interaction_times"] = [8, 8, 8, 9, 9, 10]

            stats = system.get_pattern_stats()

            assert "common_hours" in stats
            assert stats["common_hours"][0][0] == 8


class TestGetProactiveSystem:
    def test_returns_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.data_memory.proactive_system import ProactiveSystem, _systems

            _systems.clear()

            system = ProactiveSystem("test_entity", storage_dir=Path(tmpdir))

            assert isinstance(system, ProactiveSystem)
            assert system.entity_id == "test_entity"

    def test_singleton_per_entity(self):
        from src.data_memory.proactive_system import _systems, get_proactive_system

        _systems.clear()

        s1 = get_proactive_system("luna")
        s2 = get_proactive_system("luna")
        s3 = get_proactive_system("eris")

        assert s1 is s2
        assert s1 is not s3
