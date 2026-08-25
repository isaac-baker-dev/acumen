"""
Acumen Overnight Mass Research
===============================
Runs multiple research topics through agent crews overnight.
Each topic goes through the full pipeline: Research Agent → Strategist → Knowledge Base.

Usage:
    python overnight_research.py                    # Run default topics
    python overnight_research.py --file topics.txt  # Run topics from file (one per line)
    python overnight_research.py --topics "topic1" "topic2" "topic3"

Green Computing:
    - Runs topics sequentially (one model loaded at a time)
    - Unloads Ollama models between batches to free RAM
    - Estimated: 3-5 minutes per topic on i3-1215U CPU
"""

import sys
import os
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from acumen.core.config import OLLAMA_BASE_URL
from acumen.core.logger import get_logger
from acumen.memory import MemoryManager

logger = get_logger("acumen.overnight")

# ── Default Research Topics ──
# These are organized into waves. Within a wave, topics are independent.
# Between waves, later topics build on earlier findings.

DEFAULT_TOPICS = {
    "Wave 1 - Foundations": [
        "Explain DAG-based blockchain architectures comparing IOTA Tangle, Hedera Hashgraph, and Nano Block Lattice for CPU-only hardware",
        "Compare content-addressable storage systems IPFS Merkle DAG vs Arweave vs Storj for personal cloud storage on consumer hardware",
        "Explain lightweight consensus mechanisms for single-node systems that can later scale to federated networks",
        "Compare BLAKE3 vs SHA-256 vs SHA-3 hash function performance on Intel Alder Lake i3-1215U CPU",
    ],
    "Wave 2 - Implementation": [
        "Best Rust crates for blockchain development including ed25519-dalek, blake3, serde, tokio, and libp2p",
        "How to extend a Rust DAG scheduler to validate blockchain transactions with topological sorting",
        "Go worker pool patterns for blockchain task execution with gRPC streaming and graceful shutdown",
        "Compare RocksDB vs SQLite vs sled as embedded storage backends for a local-first blockchain node",
    ],
    "Wave 3 - AI Autonomous Coding": [
        "State of the art techniques for LLM-driven code generation that compiles and passes tests on first attempt",
        "How to implement test-driven development with AI agents where tests are written before code generation",
        "Best prompting strategies for code generation with 7B parameter models using chain-of-thought and few-shot examples",
        "How to parse Rust compiler errors and automatically generate fix suggestions for AI code refinement loops",
    ],
    "Wave 4 - Networking & Security": [
        "How libp2p handles peer discovery with mDNS and Kademlia DHT for decentralized networking in Rust",
        "Ed25519 key pair generation and Merkle tree verification implementation in Rust for blockchain integrity",
        "CPU-feasible zero-knowledge proof options for transaction privacy on consumer hardware without GPU",
        "How to defend against prompt injection attacks in autonomous AI agent systems",
    ],
    "Wave 5 - Optimization": [
        "Latest GGUF quantization techniques Q4_K_M vs Q5_K_M vs IQ formats for best speed quality tradeoff on Intel CPUs",
        "How speculative decoding works with draft models to speed up LLM inference on CPU-only hardware",
        "Optimal llama.cpp thread configuration for Intel i3-1215U with 2 Performance cores and 4 Efficiency cores",
        "How to implement predictive DAG scheduling using historical execution times to estimate pipeline completion",
    ],
}


def unload_ollama_models():
    """Unload all Ollama models to free RAM between research waves."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=5)
        if resp.ok:
            running = resp.json().get("models", [])
            for model in running:
                name = model.get("name", "")
                if name:
                    requests.post(
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json={"model": name, "keep_alive": 0},
                        timeout=10,
                    )
                    logger.info(f"Unloaded model: {name}")
    except Exception as e:
        logger.warning(f"Could not unload models: {e}")


def notify_scheduler(task_id, status):
    """Notify the Rust scheduler of task completion."""
    try:
        requests.post(
            "http://127.0.0.1:9090/mark",
            json={"task_id": task_id, "status": status},
            timeout=2,
        )
    except Exception:
        pass


def submit_to_scheduler(tasks):
    """Submit task list to Rust scheduler for tracking."""
    try:
        resp = requests.post(
            "http://127.0.0.1:9090/schedule",
            json={"tasks": tasks},
            timeout=2,
        )
        if resp.ok:
            data = resp.json()
            logger.info(f"Scheduler tracking: {data.get('pipeline_id')}")
            return data
    except Exception:
        logger.info("Scheduler not available - running standalone")
    return None


def research_topic(topic, topic_id, memory, use_crew=True):
    """Research a single topic using the Research Crew."""
    start = time.time()
    result_text = ""

    try:
        if use_crew:
            from acumen.agents.crews import research_crew
            crew = research_crew(topic)
            result = crew.kickoff()
            result_text = str(result)
        else:
            # Fallback: use LLM directly without CrewAI
            from acumen.core.llm import get_llm
            llm = get_llm("reasoning")
            result_text = llm.invoke(
                f"Research the following topic thoroughly. Include key findings, "
                f"technical details, and practical applications:\n\n{topic}"
            )

        duration = time.time() - start
        word_count = len(result_text.split())

        # Save to knowledge base
        memory.save_episode(
            "overnight_research",
            result_text[:2000],
            {
                "topic": topic[:100],
                "topic_id": topic_id,
                "duration_seconds": round(duration, 1),
                "word_count": word_count,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Also save to semantic memory for vector search
        try:
            memory.add_knowledge(
                result_text[:3000],
                {
                    "topic": topic[:100],
                    "source": "overnight_research",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "confidence": "HIGH",
                },
            )
        except Exception:
            pass

        notify_scheduler(topic_id, "completed")
        return {
            "status": "OK",
            "words": word_count,
            "duration": round(duration, 1),
            "preview": result_text[:200],
        }

    except Exception as e:
        duration = time.time() - start
        notify_scheduler(topic_id, "failed")
        return {
            "status": "ERROR",
            "error": str(e)[:200],
            "duration": round(duration, 1),
        }


def run_overnight_research(topics_by_wave, output_dir=None, use_crew=True):
    """Run all research topics organized by wave."""

    # Setup output directory
    if output_dir is None:
        output_dir = Path.home() / "acumen" / "data" / "research" / datetime.now().strftime("%Y-%m-%d")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    memory = MemoryManager()

    # Count totals
    all_topics = []
    for wave_name, topics in topics_by_wave.items():
        for i, topic in enumerate(topics):
            all_topics.append((wave_name, topic))
    total = len(all_topics)

    # Build scheduler task list
    scheduler_tasks = []
    for idx, (wave, topic) in enumerate(all_topics):
        task_id = f"research_{idx+1:03d}"
        scheduler_tasks.append({
            "id": task_id,
            "name": topic[:60],
            "agent": "research",
            "payload": topic,
            "depends_on": [],
            "priority": 1,
        })

    # Submit to scheduler for tracking
    submit_to_scheduler(scheduler_tasks)

    # Print banner
    print("\n" + "=" * 60)
    print("  ACUMEN OVERNIGHT MASS RESEARCH")
    print("=" * 60)
    print(f"\n  Topics: {total}")
    print(f"  Estimated time: {total * 3}-{total * 5} minutes")
    print(f"  Output: {output_dir}")

    # Check knowledge base
    try:
        kb_count = memory.knowledge_count()
        print(f"  Knowledge base: {kb_count} docs")
    except Exception:
        print("  Knowledge base: available")

    print(f"\n  {'Crew mode' if use_crew else 'Direct LLM mode'}")
    print("=" * 60 + "\n")

    # Research loop
    results = []
    errors = 0
    total_words = 0
    start_time = time.time()

    topic_num = 0
    for wave_name, topics in topics_by_wave.items():
        print(f"\n{'─' * 60}")
        print(f"  {wave_name} ({len(topics)} topics)")
        print(f"{'─' * 60}\n")

        for topic in topics:
            topic_num += 1
            task_id = f"research_{topic_num:03d}"
            short = topic[:75] + "..." if len(topic) > 75 else topic

            print(f"[{topic_num}/{total}] {short}", end=" ", flush=True)

            result = research_topic(topic, task_id, memory, use_crew)

            if result["status"] == "OK":
                print(f"OK ({result['words']} words, {result['duration']}s)")
                total_words += result["words"]

                # Save individual result
                result_file = output_dir / f"topic_{topic_num:03d}.md"
                result_file.write_text(
                    f"# {topic}\n\n"
                    f"**Researched:** {datetime.now().isoformat()}\n"
                    f"**Words:** {result['words']}\n"
                    f"**Duration:** {result['duration']}s\n\n"
                    f"---\n\n"
                    f"{result.get('preview', 'No preview available')}\n",
                    encoding="utf-8",
                )
            else:
                print(f"ERROR: {result.get('error', 'Unknown')[:80]}")
                errors += 1

            results.append({
                "topic_num": topic_num,
                "topic": topic,
                "task_id": task_id,
                "wave": wave_name,
                **result,
            })

        # Unload models between waves to free RAM
        print(f"\n  [RAM cleanup] Unloading models between waves...")
        unload_ollama_models()
        time.sleep(3)

    # Final summary
    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    print("\n" + "=" * 60)
    print("  MASS RESEARCH COMPLETE!")
    print("=" * 60)
    print(f"  Topics researched: {total}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed_min:.1f} minutes")
    print(f"  Total words: {total_words}")

    try:
        kb_count = memory.knowledge_count()
        print(f"  Knowledge base: {kb_count} docs")
    except Exception:
        pass

    print(f"  Results saved: {output_dir}")
    print("=" * 60 + "\n")

    # Save summary report
    summary = {
        "completed": datetime.now().isoformat(),
        "total_topics": total,
        "errors": errors,
        "total_words": total_words,
        "duration_minutes": round(elapsed_min, 1),
        "results": results,
    }

    summary_file = output_dir / "SUMMARY.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Save human-readable report
    report_file = output_dir / "REPORT.md"
    report_lines = [
        f"# Acumen Overnight Research Report",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Topics:** {total}",
        f"**Errors:** {errors}",
        f"**Duration:** {elapsed_min:.1f} minutes",
        f"**Total Words:** {total_words}",
        f"",
        f"---",
        f"",
    ]
    for r in results:
        status_icon = "✓" if r["status"] == "OK" else "✗"
        report_lines.append(f"## {status_icon} Topic {r['topic_num']}: {r['topic'][:80]}")
        report_lines.append(f"")
        report_lines.append(f"- **Wave:** {r['wave']}")
        report_lines.append(f"- **Status:** {r['status']}")
        if r["status"] == "OK":
            report_lines.append(f"- **Words:** {r['words']}")
            report_lines.append(f"- **Duration:** {r['duration']}s")
        else:
            report_lines.append(f"- **Error:** {r.get('error', 'Unknown')}")
        report_lines.append(f"")

    report_file.write_text("\n".join(report_lines), encoding="utf-8")

    return summary


def load_topics_from_file(filepath):
    """Load topics from a text file (one per line)."""
    topics = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                topics.append(line)
    return {"Custom Research": topics}


def main():
    parser = argparse.ArgumentParser(description="Acumen Overnight Mass Research")
    parser.add_argument("--file", type=str, help="Text file with topics (one per line)")
    parser.add_argument("--topics", nargs="+", help="Topics as command line arguments")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--no-crew", action="store_true",
                        help="Use direct LLM instead of CrewAI crews (faster but less thorough)")
    parser.add_argument("--wave", type=str, help="Run only a specific wave (e.g. 'Wave 1 - Foundations')")
    args = parser.parse_args()

    if args.file:
        topics = load_topics_from_file(args.file)
    elif args.topics:
        topics = {"Command Line Topics": args.topics}
    else:
        topics = DEFAULT_TOPICS

    if args.wave:
        filtered = {k: v for k, v in topics.items() if args.wave.lower() in k.lower()}
        if filtered:
            topics = filtered
        else:
            print(f"Wave not found: {args.wave}")
            print(f"Available waves: {list(topics.keys())}")
            return

    use_crew = not args.no_crew
    run_overnight_research(topics, args.output, use_crew)


if __name__ == "__main__":
    main()
