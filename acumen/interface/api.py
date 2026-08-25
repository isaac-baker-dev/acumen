"""Acumen Web API"""
import json, uuid, asyncio, os, threading
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from acumen.core.config import MODELS, is_cloud_available, API_PORT, CONVO_DIR, OUTPUT_DIR
from acumen.core.llm import get_llm
from acumen.memory import MemoryManager
from acumen.metagraph.engine import metagraph
from acumen.metagraph.bootstrap import bootstrap_metagraph
from acumen.dags.pipeline import submit_pipeline
from acumen.core.logger import get_logger
from acumen.interface.auth import verify_password, create_token, verify_token
from acumen.memory.user_profile import get_profile_context, extract_user_info
from acumen.memory.summarizer import summarize_conversation, should_summarize
from acumen.router.chat_router import route_message, should_use_dag, build_dag_tasks
from acumen.core.self_correct import needs_review, self_correct
from acumen.core.agentic import needs_agentic, agentic_response
from acumen.core.context_engine import is_followup, compress_history, detect_tone, get_tone_instruction
import requests as _requests

logger = get_logger("acumen.interface.api")
app = FastAPI(title="Acumen AI", docs_url="/api/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    bootstrap_metagraph()
    logger.info("Acumen API started")


# ── Models ──

class LoginRequest(BaseModel):
    password: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = ""

class PipelineRequest(BaseModel):
    pipeline_type: str
    input_text: str

class DagPipelineRequest(BaseModel):
    tasks: list[dict]
    mission_name: str = "Pipeline"
    source: str = "api"


# ── Auth ──

@app.post("/api/login")
async def login(req: LoginRequest):
    if verify_password(req.password):
        return {"token": create_token(), "status": "ok"}
    return {"status": "error", "message": "Wrong password"}


# ── Conversation Helpers ──

def load_conversation(convo_id):
    path = CONVO_DIR / f"{convo_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return []

def save_conversation(convo_id, messages):
    path = CONVO_DIR / f"{convo_id}.json"
    path.write_text(json.dumps(messages, indent=2))


# ── Context Builder ──

def build_context(memory, message):
    context = memory.get_task_context(message)
    sources = []
    kb_results = memory.search_knowledge(message, n=3)
    if kb_results:
        best = float(kb_results[0]["relevance"].replace("%", ""))
        if best >= 40:
            for r in kb_results[:2]:
                topic = r.get("metadata", {}).get("topic", "general")
                rel = r["relevance"]
                sources.append(f"Knowledge Base ({topic}, {rel} match)")
            kb_context = "\n".join(r["content"][:300] for r in kb_results[:2])
            context = f"Knowledge base results:\n{kb_context}\n\n{context}"
    if not kb_results or float(kb_results[0]["relevance"].replace("%", "")) < 40:
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                web_results = list(ddgs.text(message, max_results=3))
            if web_results:
                web_context = "\n".join(f"- {r['body']}" for r in web_results)
                context = f"Web search results:\n{web_context}\n\n{context}"
                for r in web_results[:2]:
                    sources.append(f"Web: {r.get('title', 'Unknown')[:50]}")
                logger.info("Auto web search triggered")
        except Exception:
            pass
    if sources:
        source_note = "\n\nSOURCES (mention these naturally in your response):\n" + "\n".join(f"- {s}" for s in sources)
        context = context + source_note
    return context


def is_complex_question(message):
    msg = message.lower().strip()
    complex_indicators = ["why", "how does", "explain", "compare", "analyze", "what are the pros",
        "design", "build", "create a", "write a", "help me understand", "what would happen",
        "difference between", "step by step", "best way to", "should i", "evaluate"]
    if len(msg) > 80:
        return True
    return any(w in msg for w in complex_indicators)


def build_prompt(context, history, user_context="", message="", tone="", followup=False):
    chain_of_thought = ""
    tone_instruction = get_tone_instruction(tone)
    followup_note = ""
    if followup:
        followup_note = "The user is following up. Reference the previous exchange directly. "
    if is_complex_question(message):
        chain_of_thought = (
            "THINKING PROCESS (internal - don't show to user):\n"
            "1. What is the user asking?\n2. What do I know from KB?\n"
            "3. Key points to cover?\n4. Best structure?\nNow respond.\n\n")
    return (
        "You are Acumen, a knowledgeable and friendly personal AI assistant. "
        "You run locally on the user's computer for privacy.\n\n"
        "RULES:\n"
        "- Be conversational, warm, and helpful\n"
        "- Give direct answers first, then explain if needed\n"
        "- If web search results are provided, USE them\n"
        "- If you have knowledge base info, reference it naturally\n"
        "- Match response length to complexity\n"
        "- If unsure, say so honestly\n"
        "- Use markdown for lists and code blocks\n"
        "- NEVER show thinking process to user\n\n"
        f"{chain_of_thought}{followup_note}{tone_instruction}\n\n"
        f"USER PROFILE:\n{user_context}\n\n"
        f"CONTEXT:\n{context}\n\nCONVERSATION:\n{history}\n\nRespond naturally as Acumen:")


# ── Command Handler ──

def handle_command(message, memory):
    msg = message.strip()

    if msg.startswith("/dag ") and msg != "/dag status":
        instruction = msg[5:].strip()
        if not instruction:
            return ("Usage: `/dag <task description>`\n\n"
                "Examples:\n"
                "- `/dag research blockchain consensus mechanisms`\n"
                "- `/dag full build a REST API for task management`\n"
                "- `/dag security audit the authentication module`\n"
                "- `/dag automate nightly knowledge base backup`")
        logger.info(f"DAG command: {instruction}")
        dag_tasks = build_dag_tasks(instruction)
        try:
            resp = _requests.post("http://127.0.0.1:8000/api/dag/submit",
                json={"tasks": dag_tasks, "mission_name": f"Chat: {instruction[:50]}", "source": "chat"},
                timeout=5)
            result = resp.json() if resp.ok else {}
        except:
            result = {}
        response = f"## DAG Pipeline Launched\n\n"
        response += f"**Mission:** {instruction[:80]}\n"
        response += f"**Pipeline ID:** {result.get('pipeline_id', 'running')}\n"
        response += f"**Tasks:** {len(dag_tasks)}\n\n"
        response += "| # | Task | Agent | Depends On |\n|---|---|---|---|\n"
        for t in dag_tasks:
            deps = ", ".join(t["depends_on"]) if t["depends_on"] else "—"
            response += f"| {t['id']} | {t['name']} | {t['agent']} | {deps} |\n"
        response += "\n*Track progress in the Command Center or type `/dag status`*"
        return response

    elif msg == "/dag status":
        try:
            resp = _requests.get("http://127.0.0.1:8000/api/dag/status", timeout=3)
            data = resp.json()
        except:
            return "Could not fetch DAG status."
        if not data.get("tasks"):
            return "No pipeline running. Start one with `/dag <task>`"
        running = data.get("running", False)
        states = data.get("states", {})
        completed = sum(1 for s in states.values() if s == "completed")
        failed = sum(1 for s in states.values() if s == "failed")
        total = len(states)
        status_icon = "🔄" if running else "✅" if failed == 0 else "⚠️"
        response = f"## {status_icon} DAG Pipeline Status\n\n"
        response += f"**Pipeline:** {data.get('pipeline_id', 'unknown')}\n"
        response += f"**Status:** {'Running' if running else 'Complete'}\n"
        response += f"**Progress:** {completed}/{total} tasks"
        if failed > 0:
            response += f" ({failed} failed)"
        response += "\n\n| Task | Status |\n|---|---|\n"
        for task in data.get("tasks", []):
            state = states.get(task["id"], "pending")
            icons = {"completed": "✅", "running": "🔄", "failed": "❌", "ready": "⏳", "pending": "⬜"}
            response += f"| {task['name']} | {icons.get(state, '⬜')} {state} |\n"
        return response

    elif msg.startswith("/research "):
        topic = msg[10:].strip()
        logger.info(f"Research command: {topic}")
        kb = memory.search_knowledge(topic, n=3)
        kb_text = "\n".join(r["content"][:300] for r in kb) if kb else "No knowledge found."
        web_text = ""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(topic, max_results=5))
            if results:
                web_text = "\n".join(f"- **{r['title']}**: {r['body']}" for r in results)
        except Exception:
            web_text = "Web search unavailable."
        llm = get_llm("reasoning")
        prompt = (f"You are a research agent. Compile a research report on: {topic}\n\n"
            f"Knowledge Base:\n{kb_text}\n\nWeb Results:\n{web_text}\n\n"
            "Write: ## Summary\n## Key Findings\n## Details\n## Sources\n")
        report = llm.invoke(prompt)
        memory.save_knowledge(f"Research on {topic}: {report[:1500]}", {"source": "research_agent", "topic": topic})
        return f"## Research Report: {topic}\n\n{report}"

    elif msg.startswith("/code "):
        description = msg[6:].strip()
        logger.info(f"Code command: {description}")
        kb = memory.search_knowledge(description, n=2)
        kb_text = "\n".join(r["content"][:300] for r in kb) if kb else ""
        llm = get_llm("code")
        prompt = (f"Write complete, production-ready code for:\n{description}\n\n"
            f"Reference:\n{kb_text}\n\nInclude imports, comments, error handling, usage example.\n")
        code = llm.invoke(prompt)
        review_llm = get_llm("fast")
        review = review_llm.invoke(f"Review this code briefly (3 bullets):\n\n{code[:2000]}")
        return f"## Code: {description}\n\n{code}\n\n---\n## Quick Review\n{review}"

    elif msg.startswith("/review "):
        filepath = msg[8:].strip()
        logger.info(f"Review command: {filepath}")
        from acumen.agents.code_reviewer import review_file
        return f"## Code Review: {filepath}\n\n{review_file(filepath)}"

    elif msg.startswith("/scrape "):
        url = msg[8:].strip()
        logger.info(f"Scrape command: {url}")
        from acumen.tools.web_scraper import WebScraperTool
        result = WebScraperTool()._run(url)
        memory.save_knowledge(f"Scraped from {url}: {result[:1500]}", {"source": "web_scrape", "topic": "scraped"})
        return f"## Scraped: {url}\n\n{result}"

    elif msg.startswith("/analyze "):
        filepath = msg[9:].strip()
        logger.info(f"Analyze image command: {filepath}")
        from acumen.tools.image_reader import analyze_image
        return f"## Image Analysis\n\n{analyze_image(filepath)}"

    elif msg.startswith("/correct "):
        correction = msg[9:].strip()
        logger.info(f"Correction: {correction}")
        memory.save_knowledge(f"User correction: {correction}", {"source": "user_correction", "topic": "corrections"})
        from acumen.memory.user_profile import add_fact
        add_fact(f"Correction: {correction}")
        return f"Got it! I've saved that correction and will remember it going forward."

    elif msg.startswith("/watch "):
        topic = msg[7:].strip()
        from acumen.tools.auto_research import add_topic
        topics = add_topic(topic)
        return f"Now watching **{topic}**.\n\nAll watched topics: " + ", ".join(topics)

    elif msg.startswith("/unwatch "):
        topic = msg[9:].strip()
        from acumen.tools.auto_research import remove_topic
        topics = remove_topic(topic)
        return f"Stopped watching **{topic}**.\n\nRemaining: " + (", ".join(topics) if topics else "None")

    elif msg == "/watchlist":
        from acumen.tools.auto_research import list_topics
        data = list_topics()
        if not data["topics"]:
            return "No watched topics. Use `/watch [topic]` to add one."
        lines = "## Watched Topics\n\n"
        for t in data["topics"]:
            lines += f"- {t}\n"
        if data["history"]:
            last = data["history"][-1]
            lines += f"\nLast research: {last['date'][:10]} ({last['topics_researched']} topics)"
        return lines

    elif msg == "/research-now":
        from acumen.tools.auto_research import run_all_research
        result = run_all_research()
        if result["researched"] == 0:
            return "No topics to research. Use `/watch [topic]` to add topics first."
        lines = f"## Auto-Research Complete\n\nResearched **{result['researched']}** topics:\n\n"
        for r in result.get("results", []):
            lines += f"### {r['topic']}\n{r['summary']}...\n\n"
        return lines

    elif msg.startswith("/speak "):
        text = msg[7:].strip()
        from acumen.tools.voice import speak_async
        speak_async(text)
        return f"Speaking: *{text[:100]}...*"

    elif msg == "/backup":
        from acumen.tools.backup import create_backup
        result = create_backup()
        if "error" in result:
            return f"Backup failed: {result['error']}"
        return (f"## Backup Created!\n\n- **Name:** {result['name']}\n"
            f"- **Files:** {result['files']}\n- **Size:** {result['size_mb']} MB")

    elif msg == "/backups":
        from acumen.tools.backup import list_backups
        backups = list_backups()
        if not backups:
            return "No backups found. Type `/backup` to create one."
        lines = "## Your Backups\n\n| Name | Date | Files | Size |\n|---|---|---|---|\n"
        for b in backups:
            lines += f"| {b['name']} | {b['created'][:10]} | {b['files']} | {b['size_mb']} MB |\n"
        return lines

    elif msg == "/help":
        return ("## Acumen Commands\n\n"
            "| Command | What it does |\n|---|---|\n"
            "| `/dag [task]` | Launch a multi-agent DAG pipeline |\n"
            "| `/dag status` | Check running pipeline status |\n"
            "| `/research [topic]` | Multi-source research report |\n"
            "| `/code [description]` | Write + review code |\n"
            "| `/review [filepath]` | Review a code file |\n"
            "| `/scrape [url]` | Extract content from a webpage |\n"
            "| `/analyze [filepath]` | Analyze a local image |\n"
            "| `/correct [fact]` | Correct Acumen's knowledge |\n"
            "| `/speak [text]` | Read text aloud |\n"
            "| `/watch [topic]` | Add auto-research topic |\n"
            "| `/unwatch [topic]` | Remove auto-research topic |\n"
            "| `/watchlist` | Show watched topics |\n"
            "| `/research-now` | Run auto-research immediately |\n"
            "| `/backup` | Create a full backup |\n"
            "| `/backups` | List all backups |\n"
            "| `/help` | Show this help |\n\n"
            "Or just chat normally! Complex requests are auto-routed through the DAG.")

    return None


# ── Chat Endpoint ──

@app.post("/api/chat")
async def chat(req: ChatRequest):
    convo_id = req.conversation_id or str(uuid.uuid4())[:8]
    messages = load_conversation(convo_id)
    messages.append({"role": "user", "content": req.message, "timestamp": datetime.now().isoformat()})
    memory = MemoryManager()

    cmd_response = handle_command(req.message, memory)
    if cmd_response:
        messages.append({"role": "assistant", "content": cmd_response, "timestamp": datetime.now().isoformat()})
        save_conversation(convo_id, messages)
        return {"conversation_id": convo_id, "response": cmd_response, "messages": messages[-20:]}

    # Check if this should go through the DAG pipeline
    if should_use_dag(req.message):
        logger.info(f"Routing to DAG pipeline: {req.message[:60]}")
        dag_tasks = build_dag_tasks(req.message)
        dag_req = DagPipelineRequest(
            tasks=dag_tasks,
            mission_name=f"Chat: {req.message[:50]}",
            source="chat",
        )
        dag_result = await dag_submit(dag_req)
        dag_response = (
            f"I've started a multi-step DAG pipeline for this request.\n\n"
            f"**Pipeline:** {dag_result.get('pipeline_id', 'running')}\n"
            f"**Tasks:** {len(dag_tasks)}\n\n"
            f"Track progress in the Command Center or type `/dag status`.\n\n"
            f"Tasks created:\n"
        )
        for t in dag_tasks:
            deps = f" (after {', '.join(t['depends_on'])})" if t['depends_on'] else " (starts immediately)"
            dag_response += f"- **{t['name']}** [{t['agent']}]{deps}\n"
        messages.append({"role": "assistant", "content": dag_response, "timestamp": datetime.now().isoformat()})
        save_conversation(convo_id, messages)
        return {"conversation_id": convo_id, "response": dag_response, "messages": messages[-20:]}

    context = build_context(memory, req.message)
    history = compress_history(messages[-20:])
    user_ctx = get_profile_context()
    tone = detect_tone(messages)
    followup = is_followup(req.message)
    prompt = build_prompt(context, history, user_ctx, req.message, tone, followup)
    model_role = route_message(req.message)
    llm = get_llm(model_role)
    response = llm.invoke(prompt)

    if needs_review(req.message):
        fast_llm = get_llm("fast")
        response = self_correct(response, req.message, fast_llm)

    messages.append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
    save_conversation(convo_id, messages)
    memory.save_episode("chat", req.message[:500], {"conversation_id": convo_id})
    extract_user_info(req.message, response)
    if should_summarize(messages):
        summarize_conversation(messages, convo_id)
    return {"conversation_id": convo_id, "response": response, "messages": messages[-20:]}


# ── Streaming Chat ──

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    convo_id = req.conversation_id or str(uuid.uuid4())[:8]
    messages = load_conversation(convo_id)
    messages.append({"role": "user", "content": req.message, "timestamp": datetime.now().isoformat()})
    memory = MemoryManager()

    cmd_response = handle_command(req.message, memory)
    if cmd_response:
        messages.append({"role": "assistant", "content": cmd_response, "timestamp": datetime.now().isoformat()})
        save_conversation(convo_id, messages)
        async def cmd_stream():
            for i in range(0, len(cmd_response), 4):
                yield f"data: {json.dumps({'token': cmd_response[i:i+4], 'done': False, 'conversation_id': convo_id})}\n\n"
                await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'token': '', 'done': True, 'conversation_id': convo_id, 'messages': messages[-20:]})}\n\n"
        return StreamingResponse(cmd_stream(), media_type="text/event-stream")

    if needs_agentic(req.message):
        agentic_result = agentic_response(req.message)
        messages.append({"role": "assistant", "content": agentic_result, "timestamp": datetime.now().isoformat()})
        save_conversation(convo_id, messages)
        memory.save_episode("chat", req.message[:500], {"conversation_id": convo_id, "mode": "agentic"})
        async def agentic_stream():
            header = "*Researched from knowledge base + web*\n\n"
            yield f"data: {json.dumps({'token': header, 'done': False, 'conversation_id': convo_id})}\n\n"
            for i in range(0, len(agentic_result), 6):
                yield f"data: {json.dumps({'token': agentic_result[i:i+6], 'done': False, 'conversation_id': convo_id})}\n\n"
                await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'token': '', 'done': True, 'conversation_id': convo_id, 'messages': messages[-20:]})}\n\n"
        return StreamingResponse(agentic_stream(), media_type="text/event-stream")

    context = build_context(memory, req.message)
    history = compress_history(messages[-20:])
    user_ctx = get_profile_context()
    tone = detect_tone(messages)
    followup = is_followup(req.message)
    prompt = build_prompt(context, history, user_ctx, req.message, tone, followup)
    model_role = route_message(req.message)

    if model_role == "cloud":
        try:
            cloud_llm = get_llm("cloud")
            response = cloud_llm.invoke(prompt)
            messages.append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
            save_conversation(convo_id, messages)
            memory.save_episode("chat", req.message[:500], {"conversation_id": convo_id})
            extract_user_info(req.message, response)
            if should_summarize(messages):
                summarize_conversation(messages, convo_id)
            async def cloud_stream():
                for i in range(0, len(response), 4):
                    yield f"data: {json.dumps({'token': response[i:i+4], 'done': False, 'conversation_id': convo_id})}\n\n"
                    await asyncio.sleep(0.02)
                yield f"data: {json.dumps({'token': '', 'done': True, 'conversation_id': convo_id, 'messages': messages[-20:]})}\n\n"
            return StreamingResponse(cloud_stream(), media_type="text/event-stream")
        except Exception as e:
            logger.warning(f"Cloud failed, falling back to local: {e}")
            model_role = "reasoning"

    from acumen.core.config import OLLAMA_BASE_URL
    import httpx
    model_name = MODELS.get(model_role, MODELS["reasoning"])

    async def generate():
        full_response = ""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": model_name, "prompt": prompt, "stream": True}) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            full_response += token
                            if token:
                                yield f"data: {json.dumps({'token': token, 'done': False, 'conversation_id': convo_id})}\n\n"
                            if data.get("done", False):
                                break
        except Exception as e:
            full_response = f"Error: {str(e)}"
            yield f"data: {json.dumps({'token': full_response, 'done': False, 'conversation_id': convo_id})}\n\n"
        messages.append({"role": "assistant", "content": full_response, "timestamp": datetime.now().isoformat()})
        save_conversation(convo_id, messages)
        memory.save_episode("chat", req.message[:500], {"conversation_id": convo_id})
        extract_user_info(req.message, full_response)
        if should_summarize(messages):
            summarize_conversation(messages, convo_id)
        yield f"data: {json.dumps({'token': '', 'done': True, 'conversation_id': convo_id, 'messages': messages[-20:]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── File Endpoints ──

@app.post("/api/analyze-image")
async def analyze_image_endpoint(file: UploadFile = File(...), question: str = Form("Describe this image in detail.")):
    from acumen.tools.image_reader import analyze_image_bytes
    content = await file.read()
    return {"analysis": analyze_image_bytes(content, question), "filename": file.filename}

@app.post("/api/pipeline")
async def run_pipeline(req: PipelineRequest):
    pid = submit_pipeline(req.pipeline_type, [{"name": req.pipeline_type, "agent": req.pipeline_type,
        "payload": req.input_text, "depends_on": [], "priority": 1}])
    return {"pipeline_id": pid, "status": "submitted"}

@app.post("/api/search")
async def search(query: str = ""):
    return {"results": MemoryManager().search_knowledge(query, n=5)}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    save_path = OUTPUT_DIR / file.filename
    save_path.write_bytes(content)
    if file.filename.endswith(('.txt', '.md', '.py', '.json', '.csv', '.pdf', '.docx')):
        from acumen.vectordb.ingest import ingest_file
        chunks = ingest_file(str(save_path), topic="upload")
        return {"status": "uploaded_and_ingested", "chunks": chunks, "filename": file.filename}
    if file.filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        from acumen.tools.image_reader import analyze_image_bytes
        return {"status": "image_analyzed", "analysis": analyze_image_bytes(content), "filename": file.filename}
    return {"status": "uploaded", "path": str(save_path), "filename": file.filename}


# ── System Endpoints ──

@app.get("/api/status")
async def status():
    memory = MemoryManager()
    return {"knowledge_count": memory.knowledge_count(), "cloud_available": is_cloud_available(),
        "models": MODELS, "metagraph": metagraph.stats()}

@app.get("/api/metagraph")
async def get_metagraph():
    nodes = [{"id": n.id, "name": n.name, "type": n.node_type.value, "status": n.status} for n in metagraph.nodes.values()]
    edges = [{"source": e.source_id, "target": e.target_id, "type": e.edge_type.value} for e in metagraph.edges]
    return {"nodes": nodes, "edges": edges}

@app.get("/api/conversations")
async def list_conversations():
    convos = []
    for f in CONVO_DIR.glob("*.json"):
        msgs = json.loads(f.read_text())
        if msgs:
            convos.append({"id": f.stem, "last_message": msgs[-1]["content"][:100],
                "count": len(msgs), "updated": msgs[-1].get("timestamp", "")})
    return sorted(convos, key=lambda c: c["updated"], reverse=True)

@app.get("/api/conversation/{convo_id}")
async def get_conversation(convo_id: str):
    return {"messages": load_conversation(convo_id)}

@app.websocket("/ws/logs")
async def log_stream(ws: WebSocket):
    await ws.accept()
    from acumen.core.config import LOG_DIR
    lf = LOG_DIR / "acumen.log"
    pos = 0
    if lf.exists():
        pos = lf.stat().st_size
    try:
        while True:
            if lf.exists():
                sz = lf.stat().st_size
                if sz > pos:
                    with open(lf) as f:
                        f.seek(pos)
                        lines = f.readlines()
                        pos = f.tell()
                    for line in lines:
                        await ws.send_text(line.strip())
            await asyncio.sleep(1)
    except Exception:
        pass

@app.post("/api/backup")
async def create_backup_endpoint():
    from acumen.tools.backup import create_backup
    return create_backup()

@app.get("/api/backups")
async def list_backups_endpoint():
    from acumen.tools.backup import list_backups
    return {"backups": list_backups()}

@app.post("/api/restore/{backup_name}")
async def restore_endpoint(backup_name: str):
    from acumen.tools.backup import restore_backup
    return restore_backup(backup_name)

@app.post("/api/voice/transcribe")
async def transcribe(file: UploadFile = File(...)):
    from acumen.tools.voice import transcribe_audio
    content = await file.read()
    text = transcribe_audio(content, file.filename)
    return {"text": text}

@app.post("/api/voice/speak")
async def speak_text(text: str = Form("")):
    from acumen.tools.voice import speak_async
    speak_async(text)
    return {"status": "speaking"}


# ══════════════════════════════════════════════════════════════
# UNIFIED DAG PIPELINE SYSTEM
# ══════════════════════════════════════════════════════════════

_dag_events = []
_dag_events_lock = threading.Lock()
_dag_current = {"pipeline_id": None, "tasks": [], "states": {}, "running": False}


def dag_log(msg, event_type="info", task_id=None):
    with _dag_events_lock:
        _dag_events.append({
            "ts": datetime.now().isoformat(), "msg": msg,
            "type": event_type, "task_id": task_id,
        })
        if len(_dag_events) > 500:
            _dag_events[:] = _dag_events[-400:]


@app.post("/api/dag/submit")
async def dag_submit(req: DagPipelineRequest):
    _dag_current["running"] = True
    _dag_current["tasks"] = req.tasks
    _dag_current["states"] = {t["id"]: "pending" for t in req.tasks}
    _dag_current["pipeline_id"] = None

    dag_log(f"Pipeline submitted: {req.mission_name} ({len(req.tasks)} tasks)", "info")

    sched_data = None
    try:
        resp = _requests.post("http://127.0.0.1:9090/schedule",
            json={"tasks": req.tasks}, timeout=3)
        if resp.ok:
            sched_data = resp.json()
            _dag_current["pipeline_id"] = sched_data.get("pipeline_id")
            dag_log(f"Scheduler accepted: {sched_data['pipeline_id']}", "success")
            dag_log(f"Order: {' -> '.join(sched_data['execution_order'])}", "info")
            for t in sched_data.get("ready_tasks", []):
                _dag_current["states"][t["id"]] = "ready"
    except Exception as e:
        dag_log(f"Scheduler offline: {e}", "warning")

    thread = threading.Thread(target=_execute_dag_pipeline,
        args=(req.tasks, req.mission_name), daemon=True)
    thread.start()

    return {"status": "running", "pipeline_id": _dag_current["pipeline_id"],
        "scheduler": sched_data, "total_tasks": len(req.tasks)}


def _execute_dag_pipeline(tasks, mission_name):
    try:
        from acumen.agents.crews import research_crew, coding_crew, learning_crew, security_crew, automation_crew, full_build_crew
        from acumen.memory import MemoryManager
        memory = MemoryManager()
    except Exception as e:
        dag_log(f"Failed to load crews: {e}", "error")
        _dag_current["running"] = False
        return

    crew_map = {
        "research": research_crew, "strategist": research_crew,
        "engineer": coding_crew, "coding": coding_crew, "debugger": coding_crew,
        "knowledge": learning_crew, "learning": learning_crew,
        "security": security_crew, "automator": automation_crew,
        "automation": automation_crew, "full_build": full_build_crew,
    }

    completed = set()
    def get_ready():
        return [t for t in tasks if t["id"] not in completed
                and all(d in completed for d in t["depends_on"])]

    while len(completed) < len(tasks):
        ready = get_ready()
        if not ready:
            break

        dag_log(f"Wave: {', '.join(t['id'] for t in ready)} ({len(ready)} tasks)", "info")

        for task in ready:
            tid = task["id"]
            agent = task["agent"]
            _dag_current["states"][tid] = "running"
            dag_log(f">> {task['name']} [{agent}]", "running", tid)

            try:
                _requests.post("http://127.0.0.1:9091/execute", json={
                    "id": tid, "name": task["name"], "agent": agent,
                    "payload": task["payload"], "timeout_seconds": 300}, timeout=2)
            except:
                pass

            try:
                crew_fn = crew_map.get(agent, research_crew)
                result = crew_fn(task["payload"]).kickoff()
                result_text = str(result)
                words = len(result_text.split())

                memory.save_episode("dag_pipeline", result_text[:2000],
                    {"mission": mission_name, "task": task["name"], "agent": agent})
                try:
                    memory.add_knowledge(result_text[:3000],
                        {"topic": task["name"], "source": "dag_pipeline",
                         "date": datetime.now().strftime("%Y-%m-%d")})
                except:
                    pass

                _dag_current["states"][tid] = "completed"
                completed.add(tid)
                dag_log(f"OK {task['name']} ({words} words)", "success", tid)

                try:
                    r = _requests.post("http://127.0.0.1:9090/mark",
                        json={"task_id": tid, "status": "completed"}, timeout=2)
                    md = r.json()
                    unlocked = md.get("next_ready", [])
                    for uid in unlocked:
                        _dag_current["states"][uid] = "ready"
                    if unlocked:
                        dag_log(f"  Unlocked: {', '.join(unlocked)}", "info")
                except:
                    pass

            except Exception as e:
                _dag_current["states"][tid] = "failed"
                completed.add(tid)
                dag_log(f"FAIL {task['name']}: {str(e)[:100]}", "error", tid)
                try:
                    _requests.post("http://127.0.0.1:9090/mark",
                        json={"task_id": tid, "status": "failed"}, timeout=2)
                except:
                    pass

    ok = sum(1 for s in _dag_current["states"].values() if s == "completed")
    dag_log(f"Pipeline complete: {ok}/{len(tasks)} tasks", "success")
    _dag_current["running"] = False


@app.get("/api/dag/status")
async def dag_status():
    return {"running": _dag_current["running"], "pipeline_id": _dag_current["pipeline_id"],
        "tasks": _dag_current["tasks"], "states": _dag_current["states"],
        "completed": sum(1 for s in _dag_current["states"].values() if s == "completed"),
        "failed": sum(1 for s in _dag_current["states"].values() if s == "failed"),
        "total": len(_dag_current["tasks"])}

@app.get("/api/dag/events")
async def dag_events(since: int = 0):
    with _dag_events_lock:
        new_events = _dag_events[since:]
    return {"events": new_events, "total": len(_dag_events), "next_index": len(_dag_events)}

@app.post("/api/dag/research")
async def dag_research(topic: str = "", crew: str = "research"):
    if not topic:
        return {"error": "Provide a topic parameter"}
    tasks = [
        {"id": "r1", "name": f"Research: {topic[:40]}", "agent": "research",
         "payload": topic, "depends_on": [], "priority": 3},
        {"id": "s1", "name": "Synthesize findings", "agent": "strategist",
         "payload": f"Synthesize research on: {topic}", "depends_on": ["r1"], "priority": 2},
    ]
    req = DagPipelineRequest(tasks=tasks, mission_name=f"Research: {topic[:50]}", source="api")
    return await dag_submit(req)

@app.get("/api/dashboard")
async def dashboard():
    memory = MemoryManager()
    sched_ok = False
    try:
        r = _requests.get("http://127.0.0.1:9090/health", timeout=1)
        sched_ok = r.ok
    except:
        pass
    worker_ok = False
    try:
        _requests.post("http://127.0.0.1:9091/execute", json={"id": "hc"}, timeout=1)
        worker_ok = True
    except:
        pass
    ollama_models = []
    try:
        r = _requests.get("http://127.0.0.1:11434/api/ps", timeout=1)
        if r.ok:
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except:
        pass
    return {
        "services": {"scheduler": sched_ok, "workers": worker_ok, "api": True, "ollama": True},
        "models_loaded": ollama_models, "models_configured": MODELS,
        "knowledge_base": memory.knowledge_count(), "metagraph": metagraph.stats(),
        "dag": {"running": _dag_current["running"], "pipeline_id": _dag_current["pipeline_id"],
            "tasks": len(_dag_current["tasks"]),
            "completed": sum(1 for s in _dag_current["states"].values() if s == "completed")},
    }


# ── Static Files + Startup ──

wd = os.path.join(os.path.dirname(__file__), "../../web/dist")
if os.path.exists(wd):
    app.mount("/", StaticFiles(directory=wd, html=True))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)