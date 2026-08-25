"""Acumen Memory Manager - Unified interface for all 3 tiers."""

from acumen.memory.working import WorkingMemory
from acumen.memory.episodic import EpisodicMemory
from acumen.memory.semantic import SemanticMemory

class MemoryManager:
    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

    def set_context(self, k, v): self.working.set(k, v)

    def get_context(self, k, d=None): return self.working.get(k, d)

    def save_episode(self, event_type, content, metadata=None):
        self.episodic.save(event_type, content, metadata)

    def search_episodes(self, q, limit=5): return self.episodic.search(q, limit)

    def save_knowledge(self, content, metadata=None):
        return self.semantic.add(content, metadata)

    def save_knowledge_batch(self, contents, metadatas=None):
        self.semantic.add_many(contents, metadatas)

    def search_knowledge(self, q, n=5, where=None):
        return self.semantic.search(q, n, where)

    def knowledge_count(self): return self.semantic.count()

    def get_task_context(self, task_desc):
        parts = []
        ctx = self.working.get("active_context")
        if ctx: parts.append(f"Context: {ctx}")
        for ep in self.search_episodes(task_desc, 3):
            parts.append(f"[{ep['timestamp'][:10]}] {ep['content'][:200]}")
        for k in self.search_knowledge(task_desc, 3):
            parts.append(f"[{k['relevance']}] {k['content'][:200]}")
        return "\n".join(parts) or "No prior context."