"""Acumen Conversation Summarizer - Extracts key points from conversations."""

from acumen.core.llm import get_llm
from acumen.memory import MemoryManager
from acumen.core.logger import get_logger

logger = get_logger("acumen.memory.summarizer")

def summarize_conversation(messages, convo_id=""):
    if len(messages) < 4:
        return None
    history = "\n".join(f"{m['role'].upper()}: {m['content'][:200]}" for m in messages[-20:])
    llm = get_llm("fast")
    prompt = (
        "Summarize this conversation in 2-3 sentences. "
        "Focus on: what was discussed, any decisions made, and any action items.\n\n"
        f"CONVERSATION:\n{history}\n\n"
        "SUMMARY:"
    )
    try:
        summary = llm.invoke(prompt)
        memory = MemoryManager()
        memory.save_episode("conversation_summary", summary[:500],
            {"conversation_id": convo_id, "message_count": len(messages)})
        memory.save_knowledge(
            f"Conversation summary: {summary[:500]}",
            {"source": "conversation", "topic": "chat_history", "conversation_id": convo_id}
        )
        logger.info(f"Conversation summarized: {summary[:80]}")
        return summary
    except Exception as e:
        logger.warning(f"Summarization failed: {e}")
        return None

def should_summarize(messages):
    return len(messages) >= 6 and len(messages) % 6 == 0