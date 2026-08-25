"""
Acumen Agent Mass Research
=============================
Sends research tasks through Acumen's chat endpoint.
All results saved to knowledge base automatically.
"""

import os, time, requests, json
from dotenv import load_dotenv
load_dotenv(override=True)

API = "http://127.0.0.1:8000/api"

def research(topic):
    try:
        r = requests.post(f"{API}/chat",
            json={"message": topic},
            timeout=600)
        data = r.json()
        return data.get("response", "No response")
    except Exception as e:
        return f"ERROR: {str(e)[:100]}"

topics = [
    "Explain GGUF quantization levels Q4_K_M vs Q5_K_M vs Q8_0 and their speed-to-quality ratio on CPU-only hardware",
    "How to check and enable llama.cpp CPU flags AVX2 F16C FMA on Intel i3-1215U processor for faster inference",
    "Explain KV-cache optimization techniques for running local LLMs on 32GB RAM systems",
    "How does speculative decoding work using a small draft model with a larger verification model",
    "Compare Rust async tokio vs blocking threads for DAG task scheduling performance",
    "Compare gRPC vs Unix domain sockets vs shared memory for lowest latency IPC on localhost",
    "Compare ChromaDB HNSW vs IVF index performance for collections under 100K documents",
    "Compare embedding models all-MiniLM-L6-v2 vs nomic-embed-text vs BGE-small for speed and accuracy",
    "How to reduce CrewAI agent context passing overhead using shared memory techniques",
    "How to implement parallel branch execution in DAG pipelines when tasks share the same dependency",
    "Explain chain-of-thought prompting templates that force step-by-step reasoning in small 3B to 7B models",
    "Explain the ReAct reasoning plus acting pattern and how to implement it in AI agent definitions",
    "How to implement hybrid search combining vector search with BM25 keyword search",
    "Explain cross-encoder re-ranking for RAG results using lightweight CPU-friendly models",
    "Compare semantic chunking vs fixed-size chunking vs recursive character splitting for RAG quality",
    "How to implement contextual compression of retrieved documents before feeding to an LLM",
    "How to implement query expansion that auto-rewrites questions into multiple variations for better recall",
    "Explain the debate pattern where two AI agents argue opposing positions and a judge picks the best answer",
    "Explain the reflection pattern where AI generates then a critic reviews then it revises",
    "What are the latest CPU-friendly AI models in 2025-2026 and their benchmarks",
    "How does IPFS use Merkle DAG for content-addressable decentralized storage",
    "Explain IOTA Tangle DAG architecture and how it achieves parallel transaction processing",
    "How does Hedera Hashgraph consensus work and how does it compare to traditional blockchain",
    "Explain content-addressable storage and how content identifiers CIDs work",
    "Compare BLAKE3 vs SHA-256 vs SHA-3 hash function speed on consumer CPU hardware",
    "Compare RocksDB vs SQLite vs LevelDB as storage backends for blockchain nodes",
    "Explain DAG tip selection algorithms and how new transactions choose leaf nodes to reference",
    "How does the libp2p networking library handle peer discovery and NAT traversal",
    "Explain Kademlia DHT distributed hash table for content routing in decentralized networks",
    "How does file chunking and deduplication work in DAG storage systems like IPFS",
    "Compare proof of stake vs delegated proof of stake vs PBFT consensus for small networks",
    "Explain Avalanche consensus snowball snowflake sampling protocol and why it is CPU-friendly",
    "Explain proof of authority consensus for trusted small networks under 50 nodes",
    "Compare DAG-native consensus mechanisms IOTA vs Hedera vs Nano",
    "How to design custom consensus for CPU-only hardware with under 5 second finality",
    "Explain WebAssembly WASM as a smart contract runtime and why it is lightweight and sandboxed",
    "How to write Rust smart contracts that compile to WASM using ink! and CosmWasm",
    "How to design a fee model without cryptocurrency using compute-credits or reputation",
    "Compare best local code generation models for Rust and Go on CPU hardware",
    "How to implement test-driven development with AI agents using CrewAI",
    "How to build a spec-to-code pipeline from natural language to working code",
    "Explain iterative code refinement where AI generates then compiles then fixes then tests in a loop",
    "How to parse Rust compiler errors and extract actionable fix information programmatically",
    "Explain cargo-fuzz for fuzzing Rust code to find edge cases and crashes automatically",
    "How to set up local CI/CD pipeline on localhost without any cloud services",
    "Explain critical path analysis algorithm for finding bottlenecks in DAG pipelines",
    "How does incremental topological sort work for adding tasks to a running pipeline",
    "Explain Tarjan algorithm for detecting circular dependencies in directed graphs",
    "How to implement pipeline template learning from execution history",
    "How to implement predictive scheduling using historical execution times",
    "How to generate and verify Ed25519 key pairs in Rust using ed25519-dalek crate",
    "How to implement Merkle tree verification and Merkle proofs in Rust",
    "What are CPU-feasible zero-knowledge proof options for transaction privacy",
    "How to defend against prompt injection in autonomous AI agent systems",
    "Compare WASM sandboxing with Wasmtime vs Wasmer for running untrusted code",
    "How to design a complete DAG blockchain architecture with layers from UI to storage",
    "What is the optimal build sequence for an AI to autonomously construct a DAG blockchain",
    "How to implement chaos testing for distributed DAG systems simulating failures",
    "How to use property-based testing with quickcheck in Rust for blockchain invariants",
]

print("=" * 60)
print("  ACUMEN AGENT MASS RESEARCH")
print("=" * 60)
print(f"\nTopics: {len(topics)}")
print(f"Estimated time: 2-4 hours")
print()

try:
    r = requests.get(f"{API}/status", timeout=5)
    status = r.json()
    print(f"Acumen is running! KB: {status['knowledge_count']} docs")
except Exception:
    print("ERROR: Acumen is not running!")
    print("Start it first in another tab")
    exit(1)

print()
results = []
errors = 0
start_time = time.time()

for i, topic in enumerate(topics):
    print(f"[{i+1}/{len(topics)}] {topic[:70]}...", end=" ", flush=True)
    response = research(topic)
    if response.startswith("ERROR"):
        errors += 1
        print("FAIL")
    else:
        words = len(response.split())
        results.append({"topic": topic, "words": words})
        print(f"OK ({words} words)")
    time.sleep(2)

elapsed = (time.time() - start_time) / 60

try:
    r = requests.get(f"{API}/status", timeout=5)
    after = r.json()["knowledge_count"]
except Exception:
    after = "unknown"

print()
print("=" * 60)
print("  MASS RESEARCH COMPLETE!")
print("=" * 60)
print(f"  Topics researched: {len(results)}")
print(f"  Errors: {errors}")
print(f"  Time: {elapsed:.1f} minutes")
print(f"  Knowledge base: {after} docs")
print(f"  Total words: {sum(r['words'] for r in results)}")
print("=" * 60)