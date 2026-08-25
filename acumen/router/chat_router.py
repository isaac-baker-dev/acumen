"""
Acumen Chat Router - Routes messages to the optimal path.

Two routing decisions:
1. Should this go through the DAG? (multi-step vs single-turn)
2. Which model should handle it? (fast vs reasoning vs code vs cloud)
"""

from acumen.core.config import MODELS, is_cloud_available
from acumen.core.logger import get_logger

logger = get_logger("acumen.router.chat")

# ── Model Routing ──

CODE_PHRASES = [
    "write code", "write a function", "write a class", "write a script",
    "debug this", "fix this code", "refactor this", "implement a", "code for",
    "build a function", "create a function", "create a class", "code example",
    "write a program", "build an api", "write an api", "write a python",
    "write a javascript", "write a rust", "fix my code", "review my code",
]
CODE_STARTS = ["write code", "code ", "debug ", "implement ", "fix this"]

COMPLEX_WORDS = [
    "compare", "analyze", "design a system", "architecture",
    "step by step guide", "comprehensive", "in depth", "explain in detail",
    "build a complete", "create a full", "business plan", "strategy",
    "pros and cons", "evaluate", "research",
]

SIMPLE_WORDS = [
    "what is", "who is", "when was", "define", "hello", "hi",
    "thanks", "yes", "no", "how are you", "what time", "what day",
]


def route_message(message):
    """Decide which model handles this message."""
    msg = message.lower().strip()

    if len(msg) < 20 and any(w in msg for w in SIMPLE_WORDS):
        logger.info("Routed to: fast (simple question)")
        return "fast"

    if any(msg.startswith(s) for s in CODE_STARTS) or any(p in msg for p in CODE_PHRASES):
        logger.info("Routed to: code (coding request)")
        return "code"

    if any(w in msg for w in COMPLEX_WORDS):
        if is_cloud_available():
            logger.info("Routed to: cloud (complex question)")
            return "cloud"
        else:
            logger.info("Routed to: reasoning (complex, no cloud)")
            return "reasoning"

    logger.info("Routed to: reasoning (default)")
    return "reasoning"


# ── DAG Routing ──

DAG_TRIGGERS = [
    "research and then", "research then", "compare and design",
    "build a complete", "create a full system", "design and implement",
    "research, design, and build", "step by step build",
    "analyze then create", "investigate and develop",
    "deep research on", "deep dive into", "full analysis of",
    "build me a", "create me a", "develop a complete",
    "research everything about", "comprehensive research",
    "full build", "security audit", "automate",
]

DAG_MULTI_STEP = [
    "then", "after that", "once done", "followed by",
    "step 1", "step 2", "first research", "first analyze",
    "and then build", "and then create", "and then write",
]


def should_use_dag(message):
    """Decide if this message should go through the DAG pipeline."""
    msg = message.lower().strip()

    # Explicit DAG command
    if msg.startswith("/dag "):
        return True

    # Explicit DAG triggers
    if any(t in msg for t in DAG_TRIGGERS):
        logger.info("DAG route: triggered by keyword match")
        return True

    # Multi-step indicators
    step_count = sum(1 for s in DAG_MULTI_STEP if s in msg)
    if step_count >= 2:
        logger.info(f"DAG route: {step_count} multi-step indicators found")
        return True

    # Very long complex requests (100+ chars with complex words)
    if len(msg) > 100 and any(w in msg for w in COMPLEX_WORDS):
        logger.info("DAG route: long complex request")
        return True

    return False


def build_dag_tasks(message):
    """Auto-generate a DAG task list from a free-form message."""
    msg = message.lower().strip()

    # Strip /dag prefix if present
    if msg.startswith("/dag "):
        msg = msg[5:].strip()
        message = message[5:].strip()

    # Detect what kind of pipeline to build
    has_research = any(w in msg for w in [
        "research", "compare", "analyze", "investigate", "find", "explore"])
    has_code = any(w in msg for w in [
        "build", "create", "write", "implement", "code", "develop"])
    has_design = any(w in msg for w in [
        "design", "architect", "plan", "strategy"])
    has_security = any(w in msg for w in [
        "security", "audit", "vulnerability", "secure"])
    has_automation = any(w in msg for w in [
        "automate", "schedule", "pipeline", "workflow"])
    has_full_build = "full build" in msg or (has_research and has_code and has_design)

    tasks = []
    task_id = 0

    # Full build mode - all agents
    if has_full_build:
        return [
            {"id": "t1", "name": "Research", "agent": "research",
             "payload": message, "depends_on": [], "priority": 3},
            {"id": "t2", "name": "Strategy", "agent": "strategist",
             "payload": f"Create strategy for: {message[:200]}",
             "depends_on": ["t1"], "priority": 3},
            {"id": "t3", "name": "Write Code", "agent": "engineer",
             "payload": f"Implement: {message[:200]}",
             "depends_on": ["t2"], "priority": 3},
            {"id": "t4", "name": "Debug", "agent": "debugger",
             "payload": f"Debug code for: {message[:200]}",
             "depends_on": ["t3"], "priority": 2},
            {"id": "t5", "name": "Security Audit", "agent": "security",
             "payload": f"Security audit: {message[:200]}",
             "depends_on": ["t4"], "priority": 2},
            {"id": "t6", "name": "Archive", "agent": "knowledge",
             "payload": f"Archive: {message[:100]}",
             "depends_on": ["t5"], "priority": 1},
        ]

    # Wave 1: Research (always first if detected)
    if has_research:
        task_id += 1
        tasks.append({
            "id": f"t{task_id}", "name": "Research & Gather Info",
            "agent": "research", "payload": message,
            "depends_on": [], "priority": 3,
        })
        if len(msg) > 80:
            task_id += 1
            tasks.append({
                "id": f"t{task_id}", "name": "Search Web for Latest Info",
                "agent": "research",
                "payload": f"Web search for latest on: {message[:200]}",
                "depends_on": [], "priority": 2,
            })

    # Wave 2: Strategy/Design
    if has_design or (has_research and has_code):
        task_id += 1
        research_deps = [t["id"] for t in tasks]
        tasks.append({
            "id": f"t{task_id}", "name": "Strategize & Design",
            "agent": "strategist",
            "payload": f"Create strategy for: {message[:200]}",
            "depends_on": research_deps, "priority": 3,
        })

    # Wave 3: Code
    if has_code:
        task_id += 1
        code_deps = [tasks[-1]["id"]] if tasks else []
        tasks.append({
            "id": f"t{task_id}", "name": "Write Code",
            "agent": "engineer", "payload": f"Implement: {message[:200]}",
            "depends_on": code_deps, "priority": 3,
        })
        task_id += 1
        tasks.append({
            "id": f"t{task_id}", "name": "Review & Debug",
            "agent": "debugger",
            "payload": f"Debug code for: {message[:200]}",
            "depends_on": [f"t{task_id - 1}"], "priority": 2,
        })

    # Security audit
    if has_security or has_code:
        task_id += 1
        sec_deps = [tasks[-1]["id"]] if tasks else []
        tasks.append({
            "id": f"t{task_id}", "name": "Security Audit",
            "agent": "security",
            "payload": f"Security audit: {message[:200]}",
            "depends_on": sec_deps, "priority": 2,
        })

    # Automation
    if has_automation:
        task_id += 1
        auto_deps = [tasks[-1]["id"]] if tasks else []
        tasks.append({
            "id": f"t{task_id}", "name": "Design Automation",
            "agent": "automator",
            "payload": f"Automate: {message[:200]}",
            "depends_on": auto_deps, "priority": 2,
        })

    # Archive (always last)
    if tasks:
        task_id += 1
        tasks.append({
            "id": f"t{task_id}", "name": "Archive to Knowledge Base",
            "agent": "knowledge",
            "payload": f"Store findings: {message[:100]}",
            "depends_on": [tasks[-1]["id"]], "priority": 1,
        })

    # Fallback
    if not tasks:
        tasks = [
            {"id": "t1", "name": "Research", "agent": "research",
             "payload": message, "depends_on": [], "priority": 3},
            {"id": "t2", "name": "Synthesize", "agent": "strategist",
             "payload": f"Synthesize: {message[:200]}",
             "depends_on": ["t1"], "priority": 2},
        ]

    return tasks