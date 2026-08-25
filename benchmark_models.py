"""
Acumen Model Benchmark Tool
=============================
Tests all your Ollama models to find the optimal one for each role:
- Fast: Quick responses for simple questions
- Reasoning: Deep thinking for complex analysis
- Code: Code generation and review

Measures: response time, tokens/second, output quality

Usage:
    python benchmark_models.py              # Benchmark all models
    python benchmark_models.py --quick      # Quick test (1 prompt per model)
    python benchmark_models.py --model qwen2.5:3b  # Test specific model
"""

import sys
import time
import json
import argparse
import requests
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434"

# ── Test Prompts for Each Role ──
BENCHMARKS = {
    "fast": {
        "description": "Simple questions needing quick answers",
        "prompts": [
            "What is a DAG? Answer in one sentence.",
            "Name 3 benefits of local-first software.",
            "What does CPU stand for?",
        ],
    },
    "reasoning": {
        "description": "Complex analysis requiring deep thinking",
        "prompts": [
            "Compare IOTA Tangle and Hedera Hashgraph consensus mechanisms. List 3 pros and cons of each in a table.",
            "Explain why content-addressed storage is better than location-addressed storage for decentralized systems. Give a concrete example.",
            "Design a lightweight consensus mechanism for a single-node blockchain that can later scale to 5 nodes. Describe the algorithm in 3 steps.",
        ],
    },
    "code": {
        "description": "Code generation and analysis",
        "prompts": [
            "Write a Python function that computes the SHA-256 hash of a file. Include error handling.",
            "Write a Rust struct for a DAG node with id, data, and parent_ids fields. Include derive macros for Debug, Clone, Serialize.",
            "Write a Go function that starts an HTTP server on port 9091 with a /health endpoint returning JSON.",
        ],
    },
}


def get_installed_models():
    """Get all models installed in Ollama."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.ok:
            models = r.json().get("models", [])
            return [
                {
                    "name": m["name"],
                    "size_gb": round(m["size"] / 1e9, 1),
                    "family": m["details"].get("family", "?"),
                    "params": m["details"].get("parameter_size", "?"),
                    "quant": m["details"].get("quantization_level", "?"),
                }
                for m in models
            ]
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
    return []


def unload_all_models():
    """Unload all models to get clean benchmark."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/ps", timeout=3)
        if r.ok:
            for m in r.json().get("models", []):
                requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": m["name"], "keep_alive": 0},
                    timeout=5,
                )
    except:
        pass


def benchmark_model(model_name, prompt, timeout=120):
    """Run a single benchmark: send prompt, measure response."""
    # Unload other models first
    unload_all_models()
    time.sleep(1)

    start = time.time()
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        elapsed = time.time() - start

        if r.ok:
            data = r.json()
            response = data.get("response", "")
            eval_count = data.get("eval_count", 0)
            eval_duration = data.get("eval_duration", 1)  # nanoseconds
            load_duration = data.get("load_duration", 0)
            prompt_eval = data.get("prompt_eval_count", 0)

            tokens_per_sec = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
            load_time = load_duration / 1e9

            return {
                "status": "ok",
                "response": response,
                "total_time": round(elapsed, 1),
                "load_time": round(load_time, 1),
                "tokens_generated": eval_count,
                "tokens_per_sec": round(tokens_per_sec, 1),
                "prompt_tokens": prompt_eval,
                "word_count": len(response.split()),
            }
        else:
            return {"status": "error", "error": f"HTTP {r.status_code}"}
    except requests.Timeout:
        return {"status": "timeout", "total_time": timeout}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


def run_benchmarks(models=None, quick=False, specific_model=None):
    """Run full benchmark suite."""
    installed = get_installed_models()
    if not installed:
        print("No models found. Is Ollama running?")
        return

    # Filter to text models only (skip embedding, vision)
    skip_families = {"nomic-bert", "clip"}
    skip_names = {"nomic-embed-text", "moondream", "llava"}
    test_models = [
        m for m in installed
        if m["family"] not in skip_families
        and not any(s in m["name"] for s in skip_names)
    ]

    if specific_model:
        test_models = [m for m in test_models if specific_model in m["name"]]
        if not test_models:
            print(f"Model '{specific_model}' not found. Available:")
            for m in installed:
                print(f"  {m['name']} ({m['params']}, {m['size_gb']}GB)")
            return

    print(f"\n{'='*70}")
    print(f"  ACUMEN MODEL BENCHMARK")
    print(f"{'='*70}")
    print(f"\n  Models to test: {len(test_models)}")
    print(f"  Roles to benchmark: {len(BENCHMARKS)}")
    prompts_per = 1 if quick else 3
    print(f"  Prompts per role: {prompts_per}")
    print(f"  Estimated time: {len(test_models) * len(BENCHMARKS) * prompts_per * 30}s")
    print(f"\n  Models:")
    for m in test_models:
        print(f"    {m['name']:40s} {m['params']:8s} {m['size_gb']}GB  {m['quant']}")
    print(f"\n{'='*70}\n")

    results = {}

    for model in test_models:
        model_name = model["name"]
        results[model_name] = {"info": model, "roles": {}}
        print(f"\n  ┌─ {model_name} ({model['params']}, {model['size_gb']}GB)")

        for role, bench in BENCHMARKS.items():
            prompts = bench["prompts"][:prompts_per]
            role_results = []

            for i, prompt in enumerate(prompts):
                short_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
                print(f"  │  [{role}] {short_prompt}", end=" ", flush=True)

                result = benchmark_model(model_name, prompt)

                if result["status"] == "ok":
                    print(f"✓ {result['tokens_per_sec']} tok/s, {result['total_time']}s, {result['word_count']}w")
                    role_results.append(result)
                elif result["status"] == "timeout":
                    print(f"✗ TIMEOUT ({result['total_time']}s)")
                    role_results.append(result)
                else:
                    print(f"✗ {result.get('error', 'Unknown error')[:60]}")
                    role_results.append(result)

            # Calculate averages for this role
            ok_results = [r for r in role_results if r["status"] == "ok"]
            if ok_results:
                avg_tps = sum(r["tokens_per_sec"] for r in ok_results) / len(ok_results)
                avg_time = sum(r["total_time"] for r in ok_results) / len(ok_results)
                avg_words = sum(r["word_count"] for r in ok_results) / len(ok_results)
                results[model_name]["roles"][role] = {
                    "avg_tokens_per_sec": round(avg_tps, 1),
                    "avg_time": round(avg_time, 1),
                    "avg_words": round(avg_words),
                    "success_rate": len(ok_results) / len(role_results),
                    "details": role_results,
                }
                print(f"  │  └─ {role} avg: {avg_tps:.1f} tok/s, {avg_time:.1f}s")
            else:
                results[model_name]["roles"][role] = {
                    "avg_tokens_per_sec": 0,
                    "avg_time": 999,
                    "avg_words": 0,
                    "success_rate": 0,
                    "details": role_results,
                }
                print(f"  │  └─ {role}: ALL FAILED")

        print(f"  └─ Done\n")

    # ── Print Rankings ──
    print(f"\n{'='*70}")
    print(f"  BENCHMARK RESULTS - RANKINGS")
    print(f"{'='*70}\n")

    for role in BENCHMARKS:
        print(f"  ── {role.upper()} ({BENCHMARKS[role]['description']}) ──\n")

        ranked = []
        for model_name, data in results.items():
            if role in data["roles"]:
                rd = data["roles"][role]
                if rd["success_rate"] > 0:
                    ranked.append({
                        "model": model_name,
                        "tps": rd["avg_tokens_per_sec"],
                        "time": rd["avg_time"],
                        "words": rd["avg_words"],
                        "success": rd["success_rate"],
                        "params": data["info"]["params"],
                    })

        # Sort by tokens/second (speed)
        ranked.sort(key=lambda x: -x["tps"])

        if ranked:
            print(f"    {'Rank':<5} {'Model':<35} {'Tok/s':<8} {'Time':<8} {'Words':<7} {'Pass':<6}")
            print(f"    {'─'*4}  {'─'*34} {'─'*7} {'─'*7} {'─'*6} {'─'*5}")
            for i, r in enumerate(ranked):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "  "
                pct = f"{r['success']*100:.0f}%"
                print(f"    {medal} {i+1}  {r['model']:<35} {r['tps']:<8} {r['time']:<8} {r['words']:<7} {pct}")
            print()

            best = ranked[0]
            print(f"    → Recommended for {role}: {best['model']} ({best['tps']} tok/s)\n")
        else:
            print(f"    No models completed this benchmark.\n")

    # ── Print Config Recommendation ──
    print(f"\n{'='*70}")
    print(f"  RECOMMENDED CONFIG FOR acumen/core/config.py")
    print(f"{'='*70}\n")

    recommendations = {}
    for role in BENCHMARKS:
        ranked = []
        for model_name, data in results.items():
            if role in data["roles"] and data["roles"][role]["success_rate"] > 0:
                ranked.append((model_name, data["roles"][role]["avg_tokens_per_sec"]))
        ranked.sort(key=lambda x: -x[1])
        if ranked:
            recommendations[role] = ranked[0][0]

    print(f'  MODELS = {{')
    for role in ["fast", "reasoning", "code"]:
        if role in recommendations:
            print(f'      "{role}": "{recommendations[role]}",')
    print(f'      "embedding": "nomic-embed-text",')
    print(f'      "router": "tinyllama:1.1b",')
    print(f'  }}')
    print()

    # Save results
    output_dir = Path.home() / "acumen" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "benchmark_results.json"
    report_file.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": {k: {
            "info": v["info"],
            "roles": {rk: {kk: vv for kk, vv in rv.items() if kk != "details"}
                      for rk, rv in v["roles"].items()}
        } for k, v in results.items()},
        "recommendations": recommendations,
    }, indent=2))
    print(f"  Full results saved: {report_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Acumen Model Benchmark")
    parser.add_argument("--quick", action="store_true", help="Quick test (1 prompt per role)")
    parser.add_argument("--model", type=str, help="Test specific model only")
    args = parser.parse_args()

    run_benchmarks(quick=args.quick, specific_model=args.model)


if __name__ == "__main__":
    main()
