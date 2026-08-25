"""Acumen Working Memory - In-process session state."""

class WorkingMemory:
    def __init__(self): self._store = {}

    def set(self, key, value): self._store[key] = value

    def get(self, key, default=None): return self._store.get(key, default)

    def clear(self): self._store.clear()

    def keys(self): return list(self._store.keys())