import os
import unittest
from datetime import datetime

import config
from src.data_memory.memory_manager import MemoryManager


class TestMemorySystem(unittest.TestCase):
    def setUp(self):
        # Create a temporary db path
        self.test_db_path = str(config.APP_DIR / "src" / "data_memory" / "test_memories.json")
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.manager = MemoryManager(db_path=self.test_db_path)

    def tearDown(self):
        # Clean up
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_add_and_retrieve(self):
        text = "O usuario gosta de programar em Python."
        self.manager.add_memory(text, source="test")

        # Verify persistence
        stats = self.manager.get_stats()
        self.assertEqual(stats["count"], 1)

        # Verify retrieval
        context = self.manager.retrieve_context("Qual linguagem o usuario gosta?")
        self.assertIn("Python", context)

    def test_sanitization(self):
        self.manager.add_memory("ok")
        self.assertEqual(self.manager.get_stats()["count"], 0)

        self.manager.add_memory("obrigado")
        self.assertEqual(self.manager.get_stats()["count"], 0)

    def test_date_filter(self):
        self.manager.add_memory("Memoria antiga", source="test")

        now = datetime.now()

        results = self.manager.search_by_date(
            start_date=now.replace(year=2000).isoformat(), end_date=now.replace(year=2030).isoformat()
        )
        self.assertEqual(len(results), 1)

        # Future search
        results_future = self.manager.search_by_date(
            start_date=now.replace(year=2030).isoformat(), end_date=now.replace(year=2031).isoformat()
        )
        self.assertEqual(len(results_future), 0)


if __name__ == "__main__":
    unittest.main()
