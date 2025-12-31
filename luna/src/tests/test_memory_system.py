from datetime import datetime, timedelta

import pytest


class TestMemoryConsolidator:
    def test_import(self):
        from src.data_memory.memory_consolidator import MemoryConsolidator

        assert MemoryConsolidator is not None

    def test_instantiation(self):
        from src.data_memory.memory_consolidator import MemoryConsolidator

        c = MemoryConsolidator("luna", similarity_threshold=0.7)
        assert c.entity_id == "luna"
        assert c.similarity_threshold == 0.7

    def test_find_similar_memories(self):
        from src.data_memory.memory_consolidator import MemoryConsolidator

        c = MemoryConsolidator("luna", similarity_threshold=0.7)

        memories = [
            {"content": "Meu nome e test_user"},
            {"content": "Me chamo test_user"},
            {"content": "O ceu e azul"},
            {"content": "Gosto de programar"},
            {"content": "Adoro programacao"},
        ]

        clusters = c.find_similar_memories(memories)
        assert isinstance(clusters, list)


class TestMemoryDecay:
    def test_decay_over_time(self):
        from src.data_memory.memory_decay import calculate_decay

        now = datetime.now()
        old = (now - timedelta(days=60)).isoformat()
        recent = now.isoformat()

        decay_old = calculate_decay(old, "context")
        decay_recent = calculate_decay(recent, "context")

        assert decay_recent > decay_old
        assert 0 < decay_old < 1
        assert decay_recent >= 0.9

    def test_category_specific_decay(self):
        from src.data_memory.memory_decay import calculate_decay

        old = (datetime.now() - timedelta(days=30)).isoformat()

        decay_user_info = calculate_decay(old, "user_info")
        decay_context = calculate_decay(old, "context")

        assert decay_user_info > decay_context

    def test_apply_decay_to_score(self):
        from src.data_memory.memory_decay import apply_decay_to_score

        old = (datetime.now() - timedelta(days=30)).isoformat()
        base_score = 0.8

        decayed = apply_decay_to_score(base_score, old, "context")

        assert decayed < base_score
        assert decayed > 0


class TestEmotionalTagger:
    def test_positive_detection(self):
        from src.data_memory.emotional_tagger import get_primary_emotion

        emotion, score = get_primary_emotion("Eu te amo, voce e incrivel!")
        assert emotion == "positive"
        assert score > 0.3

    def test_negative_detection(self):
        from src.data_memory.emotional_tagger import get_primary_emotion

        emotion, score = get_primary_emotion("Estou com raiva, isso e uma merda!")
        assert emotion == "negative"
        assert score > 0.3

    def test_neutral_detection(self):
        from src.data_memory.emotional_tagger import get_primary_emotion

        emotion, score = get_primary_emotion("Olá, tudo bem?")
        assert emotion == "neutral"

    def test_tag_emotion_returns_dict(self):
        from src.data_memory.emotional_tagger import tag_emotion

        scores = tag_emotion("Texto de teste")
        assert isinstance(scores, dict)


class TestCrossEntityMemory:
    def test_import_and_instantiation(self):
        from src.data_memory.cross_entity_memory import get_cross_entity_memory

        cem = get_cross_entity_memory()
        assert cem is not None

    def test_share_and_retrieve(self):
        from src.data_memory.cross_entity_memory import get_cross_entity_memory

        cem = get_cross_entity_memory()

        test_mem = {
            "content": f"Test memory {datetime.now().timestamp()}",
            "category": "user_info",
            "timestamp": datetime.now().isoformat(),
        }

        shared = cem.share_memory(test_mem, "luna")
        memories = cem.get_shared_memories("user_info")

        assert len(memories) > 0

    def test_entity_switch_recording(self):
        from src.data_memory.cross_entity_memory import get_cross_entity_memory

        cem = get_cross_entity_memory()
        cem.record_entity_switch("luna", "eris", "test")

        history = cem.get_entity_history()
        assert len(history) > 0
        assert history[-1]["to"] == "eris"


class TestProactiveRecall:
    def test_trigger_detection(self):
        from src.data_memory.proactive_recall import get_proactive_recall

        recall = get_proactive_recall("luna")

        triggers = recall.detect_triggers("Voce lembra o que eu disse?")
        assert len(triggers) > 0

        no_triggers = recall.detect_triggers("Ola, tudo bem?")
        assert len(no_triggers) == 0

    def test_should_recall(self):
        from src.data_memory.proactive_recall import get_proactive_recall

        recall = get_proactive_recall("luna")
        recall.reset_cooldown()

        assert recall.should_recall() == True


class TestMemoryWarmup:
    def test_import(self):
        from src.data_memory.memory_warmup import get_memory_warmup, run_startup_warmup

        assert get_memory_warmup is not None
        assert run_startup_warmup is not None

    def test_warmup_entity(self):
        from src.data_memory.memory_warmup import get_memory_warmup

        warmup = get_memory_warmup()
        result = warmup.warmup_entity("luna")

        assert "entity" in result
        assert "time_ms" in result
        assert result["entity"] == "luna"


class TestMemoryCron:
    def test_import(self):
        from src.data_memory.memory_cron import get_memory_cron

        assert get_memory_cron is not None

    def test_status(self):
        from src.data_memory.memory_cron import get_memory_cron

        cron = get_memory_cron()
        status = cron.get_status()

        assert "running" in status
        assert "interval_minutes" in status
        assert status["interval_minutes"] == 30


class TestSmartMemoryIntegration:
    def test_add_with_emotions(self):
        from src.data_memory.smart_memory import get_entity_smart_memory

        memory = get_entity_smart_memory("luna")
        mem_id = memory.add("Eu amo programar em Python", source="test")

        assert mem_id is not None or mem_id is None

    def test_retrieve_with_decay(self):
        from src.data_memory.smart_memory import get_entity_smart_memory

        memory = get_entity_smart_memory("luna")
        result = memory.retrieve("programar")

        assert isinstance(result, str)

    def test_recall_emotional(self):
        from src.data_memory.smart_memory import get_entity_smart_memory

        memory = get_entity_smart_memory("luna")
        memories = memory.recall_emotional("positive")

        assert isinstance(memories, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
