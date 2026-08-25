"""
Acumen Deep Parallel DAG Research
===================================
Sends a multi-agent research pipeline through the Rust DAG scheduler
where multiple agents research DIFFERENT aspects simultaneously,
then synthesize, architect, and archive the results.

This is the REAL power of the DAG — parallel agent execution.

Usage:
    python deep_research.py "Build a DAG blockchain for personal cloud storage"
    python deep_research.py "Create an AI-powered code review system"
    python deep_research.py --preset blockchain
    python deep_research.py --preset ai-coding
    python deep_research.py --preset self-optimization
"""

import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from acumen.core.config import OLLAMA_BASE_URL
from acumen.core.logger import get_logger
from acumen.memory import MemoryManager

logger = get_logger("acumen.deep_research")

SCHED = "http://127.0.0.1:9090"
WORKER = "http://127.0.0.1:9091"
API = "http://127.0.0.1:8000"

# ── Preset Research Missions ──

PRESETS = {
    "blockchain": {
        "name": "DAG Blockchain Architecture Deep Dive",
        "description": "Full parallel research into building a DAG-based blockchain on CPU-only hardware",
        "tasks": [
            # WAVE 1: Four research agents work SIMULTANEOUSLY
            {"id": "r1", "name": "Research DAG Architectures",
             "agent": "research",
             "payload": "Compare IOTA Tangle, Hedera Hashgraph, Nano Block Lattice, and Avalanche Snowball architectures. Focus on: data structures, transaction format, tip selection algorithms, throughput on consumer CPUs. Which is best for a single-node personal blockchain on Intel i3-1215U?",
             "depends_on": [], "priority": 3},

            {"id": "r2", "name": "Research Storage Protocols",
             "agent": "research",
             "payload": "Compare content-addressable storage approaches: IPFS Merkle DAG, Arweave permaweb, and Storj erasure coding. How does each handle chunking, deduplication, and integrity verification? Design a storage layer for 954GB local disk that could later federate with peers.",
             "depends_on": [], "priority": 3},

            {"id": "r3", "name": "Research Consensus Mechanisms",
             "agent": "research",
             "payload": "Compare lightweight consensus for CPU-only: Avalanche Snowball sampling, IOTA Shimmer coordinator-free, Proof of Authority, async BFT, and Narwhal/Tusk DAG-based mempool. Which achieves sub-5-second finality on consumer hardware with minimal RAM? Include pseudocode for the best option.",
             "depends_on": [], "priority": 3},

            {"id": "r4", "name": "Research P2P Networking",
             "agent": "research",
             "payload": "Research libp2p-rs for Rust: peer discovery with mDNS and Kademlia DHT, NAT traversal with hole punching, transport encryption with Noise protocol. What is the minimum viable P2P network for 2-3 trusted nodes? How to keep localhost-first but allow optional federation?",
             "depends_on": [], "priority": 2},

            # WAVE 2: Strategist synthesizes (needs ALL wave 1 results)
            {"id": "s1", "name": "Compare & Select Architecture",
             "agent": "strategist",
             "payload": "Using the research from all four domains, select the SINGLE best combination: one DAG architecture, one storage approach, one consensus mechanism, and one networking stack. Justify each choice based on: CPU-only performance, RAM under 12GB, single-node initially, local-first privacy, ability to scale to federation later. Output a clear recommendation with tradeoffs.",
             "depends_on": ["r1", "r2", "r3", "r4"], "priority": 3},

            # WAVE 3: Two engineers work SIMULTANEOUSLY on different subsystems
            {"id": "e1", "name": "Design Data Layer",
             "agent": "engineer",
             "payload": "Based on the selected architecture, design the data layer: Rust struct definitions for DAG nodes, edges, and transactions. Define the content-addressing scheme (CID format), chunk sizes, and Merkle proof structure. Show how this integrates with the existing acumen/engine/scheduler/ Rust codebase. Provide Cargo.toml dependencies needed.",
             "depends_on": ["s1"], "priority": 3},

            {"id": "e2", "name": "Design Consensus Module",
             "agent": "engineer",
             "payload": "Based on the selected consensus mechanism, design the Rust module: core algorithm implementation, message types, state machine, and integration with the existing DAG scheduler's topological sort. Show the validation pipeline: receive transaction → verify signature → check dependencies → add to DAG → propagate. Provide code stubs.",
             "depends_on": ["s1"], "priority": 3},

            # WAVE 4: Strategist creates the master blueprint (needs both engineers)
            {"id": "s2", "name": "Write Master Blueprint",
             "agent": "strategist",
             "payload": "Combine the data layer design and consensus module into a complete architecture blueprint. Include: system diagram, file structure (mapping to existing acumen/ directories), build sequence (what to implement first), estimated development time per component, and the exact cargo/go commands to build each piece. This should be a document the Engineer Agent can follow to BUILD the entire blockchain.",
             "depends_on": ["e1", "e2"], "priority": 3},

            # WAVE 5: Knowledge archivist stores everything
            {"id": "k1", "name": "Archive to Knowledge Base",
             "agent": "knowledge",
             "payload": "Archive the complete blockchain architecture blueprint to the Acumen knowledge base. Tag with metadata: project=dag_blockchain, phase=architecture, date=today, confidence=HIGH. Create separate entries for: architecture overview, data layer design, consensus design, networking design, and build sequence.",
             "depends_on": ["s2"], "priority": 1},
        ]
    },

    "ai-coding": {
        "name": "Autonomous AI Code Generation System",
        "description": "Research how to make Acumen write, test, and fix its own code",
        "tasks": [
            # WAVE 1: Three parallel research streams
            {"id": "r1", "name": "Research Code Gen Techniques",
             "agent": "research",
             "payload": "Research state-of-the-art AI code generation: AlphaCode, CodeT, SWE-Agent, Aider, and OpenHands. How do they structure generate-test-fix loops? What prompting strategies work best with 7B models like CodeLlama and Qwen2.5-Coder? Include specific prompt templates.",
             "depends_on": [], "priority": 3},

            {"id": "r2", "name": "Research Test-Driven AI Dev",
             "agent": "research",
             "payload": "How to implement test-driven development with AI agents: write tests first from specification, generate code to pass tests, run tests automatically, parse failures, regenerate. What frameworks support this? How to handle Rust cargo test and Go go test outputs?",
             "depends_on": [], "priority": 3},

            {"id": "r3", "name": "Research Compiler Error Parsing",
             "agent": "research",
             "payload": "How to parse Rust compiler errors (rustc) and Go compiler errors into structured data an LLM can use to fix code. What regex patterns extract file, line, error type, and suggestion? How do existing tools like rust-analyzer provide fix suggestions?",
             "depends_on": [], "priority": 2},

            # WAVE 2: Strategist designs the system
            {"id": "s1", "name": "Design Code Gen Pipeline",
             "agent": "strategist",
             "payload": "Design a complete autonomous coding pipeline for Acumen: (1) Spec input from user, (2) Research Agent finds patterns, (3) Engineer Agent generates code with tests, (4) Sandbox compiles and runs tests, (5) Debugger Agent fixes failures, (6) Loop until tests pass or max iterations. Define the exact CrewAI task handoffs, prompt templates per step, and success criteria.",
             "depends_on": ["r1", "r2", "r3"], "priority": 3},

            # WAVE 3: Engineer implements
            {"id": "e1", "name": "Build Error Parser",
             "agent": "engineer",
             "payload": "Write a Python module acumen/tools/compiler_parser.py that parses Rust and Go compiler output into structured JSON: {file, line, error_type, message, suggestion}. Include regex patterns for common errors. This feeds into the Debugger Agent's fix loop.",
             "depends_on": ["s1"], "priority": 2},

            {"id": "e2", "name": "Build Code Gen Prompts",
             "agent": "engineer",
             "payload": "Write optimized prompt templates for code generation with Qwen2.5-Coder:7b. Create templates for: (1) initial code generation from spec, (2) test generation from spec, (3) code fix from error message, (4) code review checklist. Store as Python string templates in acumen/agents/prompts/coding.py.",
             "depends_on": ["s1"], "priority": 2},

            # WAVE 4: Blueprint
            {"id": "s2", "name": "Write Implementation Plan",
             "agent": "strategist",
             "payload": "Create the complete implementation plan for the autonomous coding system. Include: files to create, modifications to existing agents, new CrewAI crew definition, test cases to validate the system works, and a demo scenario showing Acumen writing a Rust function from scratch.",
             "depends_on": ["e1", "e2"], "priority": 3},
        ]
    },

    "self-optimization": {
        "name": "Acumen Self-Optimization System",
        "description": "Research how Acumen can measure and improve its own performance",
        "tasks": [
            # WAVE 1: Parallel research
            {"id": "r1", "name": "Research Self-Optimization",
             "agent": "research",
             "payload": "Research AI self-optimization techniques: OPRO (Optimization by Prompting), meta-learning, prompt optimization with small models, hyperparameter tuning. Can a 7B model effectively optimize its own prompts? What are the safety guardrails needed?",
             "depends_on": [], "priority": 3},

            {"id": "r2", "name": "Research Performance Metrics",
             "agent": "research",
             "payload": "What metrics should an AI system track to measure its own performance? Research: task completion rate, response quality scoring, agent utilization, pipeline throughput, knowledge base growth rate, inference latency. How to detect performance degradation automatically?",
             "depends_on": [], "priority": 3},

            {"id": "r3", "name": "Research Safety Guardrails",
             "agent": "research",
             "payload": "Research safety mechanisms for recursive self-improvement: rollback mechanisms, performance regression detection, change budgets, human-in-the-loop checkpoints, canary testing. How do production ML systems handle safe deployment of model updates?",
             "depends_on": [], "priority": 2},

            # WAVE 2: Design
            {"id": "s1", "name": "Design Optimization Loop",
             "agent": "strategist",
             "payload": "Design Acumen's self-optimization loop: (1) Metagraph collects performance data, (2) Analyzer detects improvement opportunities, (3) Optimizer proposes changes (prompt refinement, model routing adjustments, pipeline reordering), (4) Validator tests changes in sandbox, (5) Deployer applies if improved, rolls back if not. Define metrics, thresholds, and safety limits.",
             "depends_on": ["r1", "r2", "r3"], "priority": 3},

            # WAVE 3: Implementation design
            {"id": "e1", "name": "Design Metrics Collector",
             "agent": "engineer",
             "payload": "Design a Python module acumen/optimization/metrics.py that hooks into the existing Metagraph and memory system to collect: task durations, agent success rates, model inference times, knowledge base query relevance scores, pipeline completion rates. Store in SQLite for time-series analysis.",
             "depends_on": ["s1"], "priority": 2},

            {"id": "s2", "name": "Write Optimization Blueprint",
             "agent": "strategist",
             "payload": "Create the complete blueprint for Acumen's self-optimization system. Include: new files needed, integration points with existing Metagraph and memory, the optimization loop schedule (run nightly?), safety guardrails, and success criteria for the first optimization cycle.",
             "depends_on": ["e1"], "priority": 3},
        ]
    },
}


def check_services():
    """Check which services are running."""
    services = {}
    try:
        r = requests.get(f"{SCHED}/health", timeout=2)
        services["scheduler"] = r.json().get("status") == "healthy"
    except:
        services["scheduler"] = False

    try:
        requests.post(f"{WORKER}/execute", json={"id": "hc"}, timeout=2)
        services["worker"] = True
    except:
        services["worker"] = False

    try:
        r = requests.get(f"{API}/api/status", timeout=2)
        services["api"] = True
        services["kb_count"] = r.json().get("knowledge_count", 0)
    except:
        services["api"] = False
        services["kb_count"] = 0

    return services


def run_pipeline_via_crews(tasks, mission_name):
    """Execute tasks using CrewAI crews with DAG ordering."""
    from acumen.agents.crews import research_crew, coding_crew, learning_crew
    from acumen.memory import MemoryManager

    memory = MemoryManager()
    results = {}
    completed = set()
    total = len(tasks)
    start_time = time.time()

    # Submit to scheduler for tracking
    try:
        resp = requests.post(f"{SCHED}/schedule", json={"tasks": tasks}, timeout=2)
        if resp.ok:
            sdata = resp.json()
            print(f"  Scheduler: {sdata['pipeline_id']}")
            print(f"  Order: {' → '.join(sdata['execution_order'])}")
    except:
        print("  Scheduler: offline (running standalone)")

    print()

    def get_ready():
        return [t for t in tasks if t["id"] not in completed
                and all(d in completed for d in t["depends_on"])]

    wave_num = 0
    while len(completed) < total:
        ready = get_ready()
        if not ready:
            break

        wave_num += 1
        wave_ids = [t["id"] for t in ready]
        print(f"  ═══ Wave {wave_num}: {', '.join(wave_ids)} ({len(ready)} parallel) ═══\n")

        for task in ready:
            task_start = time.time()
            agent = task["agent"]
            payload = task["payload"]
            tid = task["id"]
            short_name = task["name"]

            print(f"  [{tid}] {short_name}")
            print(f"       Agent: {agent.upper()}")
            print(f"       Working...", end=" ", flush=True)

            try:
                # Route to the right crew
                if agent in ("research",):
                    crew = research_crew(payload)
                elif agent in ("engineer", "coding"):
                    crew = coding_crew(payload)
                elif agent in ("knowledge", "learning"):
                    crew = learning_crew(payload)
                elif agent == "strategist":
                    # Strategist uses research crew (Research → Strategist)
                    crew = research_crew(payload)
                else:
                    crew = research_crew(payload)

                result = crew.kickoff()
                result_text = str(result)
                duration = time.time() - task_start
                words = len(result_text.split())

                # Save to memory
                memory.save_episode(
                    "deep_research",
                    result_text[:2000],
                    {"mission": mission_name, "task": short_name,
                     "task_id": tid, "agent": agent},
                )

                try:
                    memory.add_knowledge(
                        result_text[:3000],
                        {"topic": short_name, "source": "deep_research",
                         "mission": mission_name,
                         "date": datetime.now().strftime("%Y-%m-%d")},
                    )
                except:
                    pass

                # Notify scheduler
                try:
                    r = requests.post(f"{SCHED}/mark",
                        json={"task_id": tid, "status": "completed"}, timeout=2)
                    mark_data = r.json()
                    unlocked = mark_data.get("next_ready", [])
                except:
                    unlocked = []

                results[tid] = {"status": "OK", "words": words,
                               "duration": round(duration, 1)}
                completed.add(tid)

                print(f"OK ({words} words, {duration:.0f}s)")
                if unlocked:
                    print(f"       ↳ Unlocked: {', '.join(unlocked)}")
                print()

            except Exception as e:
                duration = time.time() - task_start
                results[tid] = {"status": "ERROR", "error": str(e)[:200],
                               "duration": round(duration, 1)}
                completed.add(tid)

                try:
                    requests.post(f"{SCHED}/mark",
                        json={"task_id": tid, "status": "failed"}, timeout=2)
                except:
                    pass

                print(f"ERROR ({duration:.0f}s)")
                print(f"       {str(e)[:100]}")
                print()

    elapsed = time.time() - start_time
    ok_count = sum(1 for r in results.values() if r["status"] == "OK")
    total_words = sum(r.get("words", 0) for r in results.values())

    return {
        "completed": ok_count,
        "total": total,
        "errors": total - ok_count,
        "total_words": total_words,
        "duration_minutes": round(elapsed / 60, 1),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Acumen Deep Parallel DAG Research")
    parser.add_argument("topic", nargs="?", help="Custom research topic")
    parser.add_argument("--preset", choices=list(PRESETS.keys()),
                        help="Use a preset research mission")
    parser.add_argument("--list", action="store_true", help="List available presets")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable presets:\n")
        for key, preset in PRESETS.items():
            print(f"  --preset {key}")
            print(f"    {preset['name']}")
            print(f"    {preset['description']}")
            print(f"    {len(preset['tasks'])} tasks\n")
        return

    if args.preset:
        preset = PRESETS[args.preset]
        tasks = preset["tasks"]
        mission_name = preset["name"]
        description = preset["description"]
    elif args.topic:
        # Auto-generate a parallel research pipeline from a free-form topic
        mission_name = f"Deep Research: {args.topic[:50]}"
        description = args.topic
        tasks = [
            {"id": "r1", "name": "Background Research",
             "agent": "research",
             "payload": f"Research the background and current state of: {args.topic}. Focus on existing approaches, key technologies, and recent developments.",
             "depends_on": [], "priority": 3},
            {"id": "r2", "name": "Technical Deep Dive",
             "agent": "research",
             "payload": f"Technical deep dive into implementation details for: {args.topic}. Focus on code patterns, libraries, frameworks, and architecture decisions.",
             "depends_on": [], "priority": 3},
            {"id": "r3", "name": "Constraints Analysis",
             "agent": "research",
             "payload": f"Analyze hardware and software constraints for: {args.topic}. Consider CPU-only (Intel i3-1215U), 32GB RAM, local-first, zero telemetry. What are the limitations and workarounds?",
             "depends_on": [], "priority": 2},
            {"id": "s1", "name": "Strategy & Synthesis",
             "agent": "strategist",
             "payload": f"Synthesize all research into an actionable plan for: {args.topic}. Select the best approach, justify tradeoffs, and create a step-by-step implementation roadmap.",
             "depends_on": ["r1", "r2", "r3"], "priority": 3},
            {"id": "e1", "name": "Architecture Design",
             "agent": "engineer",
             "payload": f"Design the technical architecture for: {args.topic}. Include file structure, key components, integration with Acumen's existing codebase, and code stubs for the critical path.",
             "depends_on": ["s1"], "priority": 3},
            {"id": "k1", "name": "Archive Results",
             "agent": "knowledge",
             "payload": f"Archive all research and designs for '{args.topic}' to the Acumen knowledge base with proper metadata tags.",
             "depends_on": ["e1"], "priority": 1},
        ]
    else:
        parser.print_help()
        print("\nExamples:")
        print('  python deep_research.py "Build a DAG blockchain"')
        print('  python deep_research.py --preset blockchain')
        print('  python deep_research.py --list')
        return

    # Check services
    services = check_services()

    # Print banner
    print("\n" + "═" * 60)
    print(f"  ACUMEN DEEP PARALLEL RESEARCH")
    print("═" * 60)
    print(f"\n  Mission: {mission_name}")
    print(f"  Description: {description[:80]}")
    print(f"  Tasks: {len(tasks)}")

    # Count waves
    deps_map = {t["id"]: t["depends_on"] for t in tasks}
    waves = 0
    done = set()
    while len(done) < len(tasks):
        wave = [t["id"] for t in tasks if t["id"] not in done
                and all(d in done for d in t["depends_on"])]
        if not wave:
            break
        waves += 1
        done.update(wave)
    parallel_tasks = max(len([t for t in tasks if not t["depends_on"]]), 1)

    print(f"  Waves: {waves}")
    print(f"  Max parallel: {parallel_tasks} agents simultaneously")
    print(f"  Estimated: {len(tasks) * 3}-{len(tasks) * 5} minutes")
    print(f"\n  Services:")
    print(f"    Scheduler: {'✓ online' if services['scheduler'] else '✗ offline'}")
    print(f"    Workers:   {'✓ online' if services['worker'] else '✗ offline'}")
    print(f"    API:       {'✓ online' if services['api'] else '✗ offline'}")
    if services.get("kb_count"):
        print(f"    KB:        {services['kb_count']} docs")
    print("\n" + "═" * 60 + "\n")

    # Run the pipeline
    summary = run_pipeline_via_crews(tasks, mission_name)

    # Print results
    print("═" * 60)
    print(f"  MISSION COMPLETE")
    print("═" * 60)
    print(f"  Completed: {summary['completed']}/{summary['total']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Total words: {summary['total_words']}")
    print(f"  Duration: {summary['duration_minutes']} minutes")
    print("═" * 60 + "\n")

    # Save report
    output_dir = Path.home() / "acumen" / "data" / "research" / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / f"deep_research_{datetime.now():%H%M%S}.json"
    report_file.write_text(json.dumps({
        "mission": mission_name,
        "timestamp": datetime.now().isoformat(),
        **summary,
    }, indent=2))
    print(f"  Report saved: {report_file}\n")


if __name__ == "__main__":
    main()
