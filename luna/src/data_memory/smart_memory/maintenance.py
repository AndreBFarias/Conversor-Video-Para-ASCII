from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import SmartMemory

logger = logging.getLogger(__name__)


def migrate_legacy_memories(memory: "SmartMemory") -> int:
    memory._ensure_loaded()

    migrated = 0
    for mem in memory._store.memories:
        if "category" not in mem.get("metadata", {}):
            cat = memory._categorizer.detect_category(mem.get("text", ""))
            if "metadata" not in mem:
                mem["metadata"] = {}
            mem["metadata"]["category"] = cat.value

            memory._category_index[cat.value].append(mem["id"])
            memory._summary_cache[mem["id"]] = memory._categorizer.generate_summary(mem.get("text", ""))
            migrated += 1

    if migrated > 0:
        memory._store.flush()
        logger.info(f"Migradas {migrated} memorias legadas")

    return migrated


def compact_old_memories(memory: "SmartMemory", days_threshold: int = 30, min_frequency: int = 1) -> int:
    memory._ensure_loaded()

    cutoff = datetime.now() - timedelta(days=days_threshold)
    to_remove = []
    to_merge: dict[str, list] = {}

    for mem in memory._store.memories:
        try:
            mem_date = datetime.fromisoformat(mem["timestamp"][:19])
            freq = mem.get("metadata", {}).get("frequency", 1)
            cat = mem.get("metadata", {}).get("category", "context")

            if mem_date < cutoff and freq <= min_frequency:
                if cat not in to_merge:
                    to_merge[cat] = []
                to_merge[cat].append(mem)
                to_remove.append(mem["id"])
        except Exception:
            continue

    compacted = 0
    for cat, mems in to_merge.items():
        if len(mems) < 3:
            continue

        texts = [m.get("text", "")[:50] for m in mems[:10]]
        merged_text = f"[Compactado {len(mems)} memorias de {cat}]: " + " | ".join(texts)

        memory.add(
            text=merged_text,
            source="compaction",
            metadata={"category": cat, "frequency": len(mems), "compacted_from": len(mems)},
        )
        compacted += 1

    for mem_id in to_remove:
        memory._store.delete(mem_id)
        if mem_id in memory._summary_cache:
            del memory._summary_cache[mem_id]
        for cat_ids in memory._category_index.values():
            if mem_id in cat_ids:
                cat_ids.remove(mem_id)

    if to_remove:
        memory._store.flush()
        logger.info(f"Compactacao: {len(to_remove)} memorias antigas -> {compacted} memorias compactadas")

    return len(to_remove)


def clear_old_memories(memory: "SmartMemory", days: int = 90) -> int:
    memory._ensure_loaded()

    cutoff = datetime.now() - timedelta(days=days)
    deleted = memory._store.clear_old(cutoff)
    logger.info(f"Limpadas {deleted} memorias antigas (>{days} dias)")
    return deleted
