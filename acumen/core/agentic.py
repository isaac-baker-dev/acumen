"""Acumen Agentic Mode - Auto research + plan + answer for complex questions."""

from acumen.core.llm import get_llm
from acumen.memory import MemoryManager
from acumen.core.logger import get_logger

logger = get_logger("acumen.core.agentic")

AGENTIC_TRIGGERS = ["how do i build", "design a system", "create a complete",
    "write a full", "help me plan", "step by step guide", "comprehensive",
    "build a complete", "architecture for", "strategy for", "roadmap for",
    "compare and recommend", "analyze in depth", "what is the best approach"]

def needs_agentic(message):
    msg = message.lower().strip()
    if len(msg) < 40:
        return False
    return any(t in msg for t in AGENTIC_TRIGGERS)

def agentic_response(message):
    logger.info(f"Agentic mode activated: {message[:50]}")
    memory = MemoryManager()

    # Step 1: Search knowledge base
    kb_results = memory.search_knowledge(message, n=5)
    kb_text = ""
    if kb_results:
        kb_text = "\n".join(f"[{r['relevance']}] {r['content'][:300]}" for r in kb_results[:3])

    # Step 2: Search the web
    web_text = ""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(message[:100], max_results=5))
        if results:
            web_text = "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception:
        pass

    # Step 3: Plan the response
    planner = get_llm("fast")
    plan_prompt = (
        f"You are a planning agent. The user asked: {message[:300]}\n\n"
        f"Available research:\nKB: {kb_text[:500]}\nWeb: {web_text[:500]}\n\n"
        "Create a brief outline (5-7 bullet points) of what a comprehensive answer should cover:"
    )
    plan = planner.invoke(plan_prompt)

    # Step 4: Generate comprehensive answer
    writer = get_llm("reasoning")
    write_prompt = (
        f"You are Acumen, an expert AI assistant. Give a comprehensive, well-structured answer.\n\n"
        f"User question: {message}\n\n"
        f"Your research plan:\n{plan}\n\n"
        f"Knowledge base findings:\n{kb_text[:1000]}\n\n"
        f"Web research:\n{web_text[:1000]}\n\n"
        f"RULES:\n"
        f"- Follow your plan structure\n"
        f"- Use markdown headers, bullet points, and code blocks\n"
        f"- Cite sources naturally (from knowledge base, from web research)\n"
        f"- Be thorough but organized\n"
        f"- Include practical examples and actionable advice\n\n"
        f"Write your comprehensive response:"
    )
    response = writer.invoke(write_prompt)

    # Step 5: Save to knowledge base
    try:
        memory.save_knowledge(
            f"Agentic research on '{message[:100]}': {response[:1500]}",
            {"source": "agentic_mode", "topic": "research"}
        )
    except Exception:
        pass

    logger.info("Agentic mode complete")
    return response