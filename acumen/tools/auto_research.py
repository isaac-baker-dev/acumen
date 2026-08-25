"""Acumen Auto-Research Daemon - Automatically researches topics on a schedule."""

import json, time, threading
from datetime import datetime
from pathlib import Path
from acumen.core.config import DATA_DIR
from acumen.core.llm import get_llm
from acumen.memory import MemoryManager
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.research_daemon")

TOPICS_FILE = DATA_DIR / "research_topics.json"

def load_topics():
    if TOPICS_FILE.exists():
        return json.loads(TOPICS_FILE.read_text())
    return {"topics": [], "history": [], "interval_hours": 24}

def save_topics(data):
    TOPICS_FILE.write_text(json.dumps(data, indent=2))

def add_topic(topic):
    data = load_topics()
    if topic not in data["topics"]:
        data["topics"].append(topic)
        save_topics(data)
        logger.info(f"Research topic added: {topic}")
    return data["topics"]

def remove_topic(topic):
    data = load_topics()
    if topic in data["topics"]:
        data["topics"].remove(topic)
        save_topics(data)
    return data["topics"]

def list_topics():
    return load_topics()

def research_topic(topic):
    memory = MemoryManager()
    web_text = ""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(f"{topic} latest news {datetime.now().year}", max_results=5))
        if results:
            web_text = "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception:
        web_text = "Web search unavailable."
    kb = memory.search_knowledge(topic, n=2)
    kb_text = "\n".join(r["content"][:300] for r in kb) if kb else ""
    llm = get_llm("fast")
    prompt = (
        f"Write a brief research update on: {topic}\n\n"
        f"Web findings:\n{web_text}\n\n"
        f"Existing knowledge:\n{kb_text}\n\n"
        "Summarize the latest developments in 2-3 paragraphs:"
    )
    try:
        report = llm.invoke(prompt)
        memory.save_knowledge(
            f"Auto-research on {topic} ({datetime.now().strftime('%Y-%m-%d')}): {report[:1500]}",
            {"source": "auto_research", "topic": topic, "date": datetime.now().isoformat()}
        )
        logger.info(f"Auto-research completed: {topic}")
        return report
    except Exception as e:
        logger.warning(f"Auto-research failed for {topic}: {e}")
        return None

def run_all_research():
    data = load_topics()
    if not data["topics"]:
        return {"status": "no topics", "researched": 0}
    results = []
    for topic in data["topics"]:
        report = research_topic(topic)
        if report:
            results.append({"topic": topic, "summary": report[:200]})
    data["history"].append({
        "date": datetime.now().isoformat(),
        "topics_researched": len(results),
    })
    data["history"] = data["history"][-30:]
    save_topics(data)
    return {"status": "complete", "researched": len(results), "results": results}

_daemon_thread = None
_daemon_running = False

def start_daemon(interval_hours=24):
    global _daemon_thread, _daemon_running
    if _daemon_running:
        return "Daemon already running"
    _daemon_running = True
    def daemon_loop():
        global _daemon_running
        while _daemon_running:
            try:
                run_all_research()
            except Exception as e:
                logger.warning(f"Daemon error: {e}")
            time.sleep(interval_hours * 3600)
    _daemon_thread = threading.Thread(target=daemon_loop, daemon=True)
    _daemon_thread.start()
    logger.info(f"Research daemon started (every {interval_hours}h)")
    return f"Daemon started (every {interval_hours}h)"

def stop_daemon():
    global _daemon_running
    _daemon_running = False
    logger.info("Research daemon stopped")
    return "Daemon stopped"