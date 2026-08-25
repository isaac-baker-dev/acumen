# File: acumen/tools/web_search.py
"""Web search tool using DuckDuckGo. Tolerant of LLM argument quirks."""
from typing import Any
from crewai.tools import BaseTool
from pydantic import model_validator
from ddgs import DDGS
from acumen.security.audit import audit


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web using DuckDuckGo. Input: a SHORT search query "
        "(3-6 words work best). Do NOT paste long sentences. "
        "Example good queries: 'IOTA Tangle CPU performance', "
        "'Rust blockchain crates 2025', 'libp2p peer discovery'."
    )

    class ArgsSchema(BaseTool.args_schema.__class__ if hasattr(BaseTool, 'args_schema') else object):
        pass

    def _run(self, **kwargs: Any) -> str:
        # Extract query from whatever the LLM sent
        query = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str) and len(val.strip()) > 1:
                query = str(val).strip()
                break

        if not query:
            return "Please provide a search query."

        # Shorten overly long queries
        words = query.split()
        if len(words) > 8:
            filler = {"the", "a", "an", "is", "are", "was", "were", "be",
                      "been", "have", "has", "had", "do", "does", "did",
                      "will", "would", "could", "should", "to", "of", "in",
                      "for", "on", "with", "at", "by", "from", "as", "into",
                      "and", "but", "or", "not", "how", "what", "which",
                      "when", "where", "who", "this", "that", "it",
                      "explain", "describe", "compare", "analyze"}
            important = [w for w in words if w.lower() not in filler][:6]
            query = " ".join(important) if important else " ".join(words[:6])

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))

            audit.log_action("tool", "web_search", "DuckDuckGo", query,
                             f"{len(results)} results", "success")

            if not results:
                return f"No results for '{query}'. Try different keywords."

            output = "\n---\n".join(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
                for r in results)
            output += (
                "\n\n[SYSTEM NOTE: Web search complete. Use these results "
                "to write your final answer. Do NOT search again with the same topic.]")
            return output

        except Exception as e:
            if "Ratelimit" in str(e):
                return "Search rate limited. Write your answer using knowledge base results."
            return f"Search failed: {e}. Try a shorter query."