"""Acumen Semantic Memory - ChromaDB vector knowledge base."""

import chromadb
from datetime import datetime
from acumen.core.config import CHROMA_DIR, CHROMA_COLLECTION
from acumen.core.logger import get_logger

logger = get_logger("acumen.memory.semantic")

class SemanticMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=chromadb.Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION, metadata={"hnsw:space":"cosine"})
        logger.info(f"Semantic memory: {self.collection.count()} docs")

    def add(self, content, metadata=None, doc_id=None):
        doc_id = doc_id or f"doc_{datetime.now():%Y%m%d_%H%M%S_%f}"
        self.collection.add(documents=[content],
                            metadatas=[metadata or {}], ids=[doc_id])
        return doc_id

    def add_many(self, contents, metadatas=None, ids=None):
        ids = ids or [f"doc_{datetime.now():%Y%m%d_%H%M%S}_{i}" for i in range(len(contents))]
        metadatas = metadatas or [{}]*len(contents)
        self.collection.add(documents=contents, metadatas=metadatas, ids=ids)

    def search(self, query, n=5, where=None):
        kw = {"query_texts":[query], "n_results":n}
        if where: kw["where"] = where
        r = self.collection.query(**kw)
        if not r["documents"][0]: return []
        return [{"content":d,"metadata":m,"distance":dist,
                 "relevance":f"{(1-dist)*100:.0f}%"}
                for d,m,dist in zip(r["documents"][0],r["metadatas"][0],r["distances"][0])]

    def count(self): return self.collection.count()