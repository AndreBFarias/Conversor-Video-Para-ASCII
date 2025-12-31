from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.constants import MemoryConstants

from ..memory_decay import apply_decay_to_score, get_recency_boost
from .constants import MemoryCategory
from .models import ContextWindow, MemorySlice

if TYPE_CHECKING:
    from .core import SmartMemory

logger = logging.getLogger(__name__)


def retrieve(
    memory: "SmartMemory",
    query: str,
    max_chars: int | None = None,
    categories: list[MemoryCategory] | None = None,
    boost_recent: bool = True,
) -> str:
    memory._ensure_loaded()

    if not query or len(query.strip()) < 3:
        return ""

    max_chars = max_chars or memory._max_context_chars
    query_vector = memory._embedder.encode(query)
    query_category = memory._categorizer.detect_category(query)

    all_results = memory._store.search(query_vector, limit=20)

    query_words = len(query.split())
    if query_words <= 2:
        adaptive_threshold = MemoryConstants.ADAPTIVE_THRESHOLD_SHORT
    elif query_words <= 5:
        adaptive_threshold = MemoryConstants.ADAPTIVE_THRESHOLD_LONG
    else:
        adaptive_threshold = memory._similarity_threshold

    filtered = []
    for r in all_results:
        if r["similarity"] < adaptive_threshold:
            continue

        mem_category = r.get("metadata", {}).get("category", "context")
        category_match = 1.0

        if categories:
            if mem_category in [c.value for c in categories]:
                category_match = 1.2
            else:
                category_match = 0.7
        elif mem_category == query_category.value:
            category_match = 1.15

        mem_category_str = r.get("metadata", {}).get("category", "context")
        timestamp = r.get("timestamp", "")

        decayed_score = apply_decay_to_score(r["similarity"], timestamp, mem_category_str)
        recency_mult = get_recency_boost(timestamp)

        adjusted_score = decayed_score * category_match * recency_mult
        filtered.append((r, adjusted_score))

    filtered.sort(key=lambda x: x[1], reverse=True)

    window = ContextWindow(query=query, max_chars=max_chars)

    top_relevant = filtered[:3]
    for r, score in top_relevant:
        slice = create_slice(memory, r, score)
        window.add(slice)

    if boost_recent and len(filtered) > 3:
        remaining = [f for f in filtered[3:] if f not in top_relevant]
        remaining.sort(key=lambda x: x[0]["timestamp"], reverse=True)
        for r, score in remaining[:2]:
            slice = create_slice(memory, r, score)
            if not window.add(slice):
                break

    result = window.render()
    logger.debug(f"Retrieval: query='{query[:30]}...' -> {len(window.slices)} slices, {window.total_chars} chars")
    return result


def create_slice(memory: "SmartMemory", result: dict, score: float) -> MemorySlice:
    mem_id = result["id"]
    summary = memory._summary_cache.get(mem_id) or memory._categorizer.generate_summary(result["text"])
    category = result.get("metadata", {}).get("category", "context")
    frequency = result.get("metadata", {}).get("frequency", 1)

    return MemorySlice(
        id=mem_id,
        summary=summary,
        category=category,
        relevance=score,
        timestamp=result["timestamp"],
        frequency=frequency,
    )


def retrieve_by_category(memory: "SmartMemory", category: MemoryCategory, limit: int = 5) -> list[MemorySlice]:
    memory._ensure_loaded()

    mem_ids = memory._category_index.get(category.value, [])

    slices = []
    for mem_id in mem_ids[-limit:]:
        for mem in memory._store.memories:
            if mem["id"] == mem_id:
                slices.append(
                    MemorySlice(
                        id=mem_id,
                        summary=memory._summary_cache.get(mem_id, mem["text"][:80]),
                        category=category.value,
                        relevance=1.0,
                        timestamp=mem["timestamp"],
                        frequency=mem.get("metadata", {}).get("frequency", 1),
                    )
                )
                break

    return slices


def get_user_profile_context(memory: "SmartMemory") -> str:
    memory._ensure_loaded()

    slices = retrieve_by_category(memory, MemoryCategory.USER_INFO, limit=5)
    slices += retrieve_by_category(memory, MemoryCategory.PREFERENCE, limit=3)

    if not slices:
        return ""

    lines = ["[PERFIL]"]
    for s in slices[:6]:
        lines.append(s.to_compact())

    return "\n".join(lines)


def recall_emotional(memory: "SmartMemory", current_emotion: str, max_results: int = 3) -> list[dict]:
    memory._ensure_loaded()

    scored = []
    for mem in memory._store.memories:
        emotion_tags = mem.get("metadata", {}).get("emotion_tags", {})
        relevance = emotion_tags.get(current_emotion, 0)
        if relevance > 0.2:
            scored.append(
                {
                    "id": mem["id"],
                    "text": mem.get("text", ""),
                    "relevance": relevance,
                    "timestamp": mem.get("timestamp", ""),
                    "primary_emotion": mem.get("metadata", {}).get("primary_emotion", "neutral"),
                }
            )

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:max_results]
