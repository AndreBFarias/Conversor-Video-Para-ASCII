from datetime import datetime, timedelta

import numpy as np

import config
from src.core.file_lock import read_json_safe, write_json_safe
from src.core.logging_config import get_logger
from src.data_memory.embeddings import get_embedding
from src.data_memory.smart_memory import get_entity_smart_memory

logger = get_logger(__name__)


class MemoryConsolidator:
    def __init__(self, entity_id: str, similarity_threshold: float = 0.85):
        self.entity_id = entity_id
        self.similarity_threshold = similarity_threshold
        self.memory = get_entity_smart_memory(entity_id)
        self.sessions_dir = config.APP_DIR / "src" / "data_memory" / "sessions" / entity_id

    def find_similar_memories(self, memories: list[dict]) -> list[list[int]]:
        if len(memories) < 2:
            return []

        embeddings = []
        for mem in memories:
            emb = get_embedding(mem.get("content", ""))
            embeddings.append(emb)

        embeddings = np.array(embeddings)

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        embeddings_normalized = embeddings / norms

        clusters = []
        used = set()

        for i in range(len(embeddings_normalized)):
            if i in used:
                continue
            cluster = [i]
            for j in range(i + 1, len(embeddings_normalized)):
                if j in used:
                    continue
                similarity = np.dot(embeddings_normalized[i], embeddings_normalized[j])
                if similarity >= self.similarity_threshold:
                    cluster.append(j)
                    used.add(j)
            if len(cluster) > 1:
                clusters.append(cluster)
            used.add(i)

        return clusters

    def synthesize_memory(self, memories: list[dict]) -> dict:
        contents = [m.get("content", "") for m in memories]
        sources = list(set(m.get("source", "unknown") for m in memories))
        timestamps = [m.get("timestamp", "") for m in memories if m.get("timestamp")]

        latest_timestamp = max(timestamps) if timestamps else datetime.now().isoformat()

        combined_content = " | ".join(contents[:3])
        if len(contents) > 3:
            combined_content += f" (+{len(contents)-3} similares)"

        return {
            "content": combined_content,
            "source": "consolidated",
            "original_sources": sources,
            "timestamp": latest_timestamp,
            "consolidated_from": len(memories),
            "category": memories[0].get("category", "context"),
        }

    def consolidate(self, max_age_days: int = 7) -> dict:
        memories_path = self.sessions_dir / "smart_memories.json"

        if not memories_path.exists():
            return {"status": "no_memories", "consolidated": 0}

        data = read_json_safe(memories_path)
        if data is None:
            data = {"memories": []}

        memories = data.get("memories", [])

        if len(memories) < 10:
            return {"status": "too_few", "consolidated": 0}

        cutoff = datetime.now() - timedelta(days=max_age_days)
        old_memories = []
        recent_memories = []

        for mem in memories:
            ts = mem.get("timestamp", "")
            try:
                mem_date = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))
                if mem_date < cutoff:
                    old_memories.append(mem)
                else:
                    recent_memories.append(mem)
            except (ValueError, TypeError):
                recent_memories.append(mem)

        if len(old_memories) < 5:
            return {"status": "nothing_old", "consolidated": 0}

        clusters = self.find_similar_memories(old_memories)

        synthesized = []
        consolidated_indices = set()

        for cluster in clusters:
            cluster_memories = [old_memories[i] for i in cluster]
            synthetic = self.synthesize_memory(cluster_memories)
            synthesized.append(synthetic)
            consolidated_indices.update(cluster)

        remaining_old = [m for i, m in enumerate(old_memories) if i not in consolidated_indices]

        new_memories = recent_memories + remaining_old + synthesized

        data["memories"] = new_memories
        data["last_consolidation"] = datetime.now().isoformat()
        data["consolidation_stats"] = {
            "original_count": len(memories),
            "new_count": len(new_memories),
            "synthesized": len(synthesized),
        }

        write_json_safe(memories_path, data)

        logger.info(f"Consolidation complete: {len(memories)} -> {len(new_memories)} memories")

        return {
            "status": "success",
            "original": len(memories),
            "final": len(new_memories),
            "consolidated": len(synthesized),
        }


def consolidate_entity_memories(entity_id: str) -> dict:
    consolidator = MemoryConsolidator(entity_id)
    return consolidator.consolidate()


def consolidate_all_entities() -> dict:
    results = {}
    entities = ["luna", "eris", "juno", "lars", "mars", "somn"]
    for entity in entities:
        try:
            results[entity] = consolidate_entity_memories(entity)
        except Exception as e:
            logger.error(f"Consolidation failed for {entity}: {e}")
            results[entity] = {"status": "error", "error": str(e)}
    return results
