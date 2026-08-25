# File: acumen/tools/knowledge_query.py
"""Knowledge base search tool - tolerant of LLM argument quirks."""
from typing import Any
from crewai.tools import BaseTool
from acumen.memory import MemoryManager


class KnowledgeQueryTool(BaseTool):
    name: str = "knowledge_base_search"
    description: str = (
        "Search Acumen's internal knowledge base. Use this ONCE or TWICE "
        "with DIFFERENT keywords each time. After using this tool twice, "
        "switch to web_search for additional information. "
        "Input: a short search query (3-8 words work best)."
    )

    def _run(self, **kwargs: Any) -> str:
        # Extract query from whatever the LLM sent
        query = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str) and len(val.strip()) > 1:
                query = str(val).strip()
                break

        if not query:
            return "Please provide a search query."

        results = MemoryManager().search_knowledge(query, n=5)
        if not results:
            return (
                "No results found in knowledge base. "
                "Try web_search to find this information online."
            )
        output = "\n---\n".join(
            f"[{r['relevance']}] [{(r.get('metadata') or {}).get('topic','?')}] "
            f"{r['content'][:400]}" for r in results)
        output += (
            "\n\n[SYSTEM NOTE: Knowledge base search complete. "
            "Do NOT repeat this same query. Either search with DIFFERENT "
            "keywords, use web_search for more info, or write your final answer.]")
        return output