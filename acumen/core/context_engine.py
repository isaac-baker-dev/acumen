"""Acumen Context Engine - Handles follow-ups, context compression, and tone matching."""

from acumen.core.logger import get_logger

logger = get_logger("acumen.core.context")

FOLLOWUP_WORDS = ["that", "this", "it", "those", "them", "the same", "again",
    "more", "less", "shorter", "longer", "simpler", "elaborate", "expand",
    "what about", "how about", "and for", "but with", "instead", "also",
    "can you", "do it", "make it", "change it", "try again", "redo"]

def is_followup(message):
    msg = message.lower().strip()
    if len(msg) < 50 and any(w in msg for w in FOLLOWUP_WORDS):
        return True
    return False

def compress_history(messages, max_messages=10):
    if len(messages) <= max_messages:
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    old = messages[:-max_messages]
    recent = messages[-max_messages:]
    old_summary = "Earlier in this conversation: " + "; ".join(
        m['content'][:80] for m in old if m['role'] == 'user'
    )[:500]
    recent_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
    return f"{old_summary}\n\n{recent_text}"

def detect_tone(messages):
    if not messages:
        return "neutral"
    recent_user = [m['content'] for m in messages[-6:] if m['role'] == 'user']
    text = " ".join(recent_user).lower()
    casual_words = ["lol", "haha", "cool", "awesome", "nice", "yo", "hey",
        "gonna", "wanna", "kinda", "sorta", "nah", "yeah", "dude", "bro"]
    formal_words = ["please provide", "could you elaborate", "i would appreciate",
        "regarding", "furthermore", "in addition", "specifically", "pursuant"]
    technical_words = ["function", "class", "api", "database", "algorithm",
        "implement", "deploy", "configure", "architecture", "framework"]
    casual_count = sum(1 for w in casual_words if w in text)
    formal_count = sum(1 for w in formal_words if w in text)
    technical_count = sum(1 for w in technical_words if w in text)
    if technical_count >= 2:
        return "technical"
    if casual_count >= 2:
        return "casual"
    if formal_count >= 2:
        return "formal"
    return "neutral"

def get_tone_instruction(tone):
    if tone == "casual":
        return "The user is being casual - match their relaxed, friendly energy. Keep it light."
    elif tone == "formal":
        return "The user is being formal - be professional and thorough. Avoid slang."
    elif tone == "technical":
        return "The user is technical - use precise terminology, include code when relevant, skip basic explanations."
    return ""