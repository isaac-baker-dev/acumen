"""
Acumen Overnight Knowledge Expansion
======================================
A massive research mission to make Acumen deeply knowledgeable in:
1. DAG Blockchain & Cloud Storage Engineering
2. Prompt Engineering & AI Understanding
3. Cloud Storage Business Strategy & Operations
4. Accounting, Finance & Business Intelligence

Run before bed. Wake up to a smarter Acumen.

Usage:
    python overnight_expand.py              # Run everything (~4-6 hours)
    python overnight_expand.py --domain 1   # Just blockchain
    python overnight_expand.py --domain 2   # Just prompt engineering
    python overnight_expand.py --domain 3   # Just business strategy
    python overnight_expand.py --domain 4   # Just accounting/finance
"""

import sys
import time
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from acumen.core.config import OLLAMA_BASE_URL
from acumen.core.logger import get_logger
from acumen.memory import MemoryManager

logger = get_logger("acumen.overnight_expand")

TOPICS = {

    # ══════════════════════════════════════════════════════════
    # DOMAIN 1: DAG BLOCKCHAIN & CLOUD DATA STORAGE
    # ══════════════════════════════════════════════════════════

    "Domain 1A - DAG Blockchain Architecture": [
        "Explain DAG directed acyclic graph data structures for blockchain including node types edge types transaction format and tip selection algorithms with code examples in Rust",
        "How does IOTA Tangle 2.0 Shimmer achieve coordinator-free consensus and what is the exact algorithm for transaction validation on CPU-only hardware",
        "Explain Hedera Hashgraph gossip-about-gossip protocol and virtual voting consensus in detail with pseudocode for the algorithm",
        "How does Nano Block Lattice architecture work where each account has its own blockchain and how does Open Representative Voting achieve consensus",
        "Explain Avalanche consensus family Snowball Snowflake Snowman sampling protocol with mathematical proof of safety and liveness guarantees",
        "Compare DAG blockchain transaction throughput benchmarks IOTA vs Hedera vs Nano vs Avalanche on consumer hardware with specific TPS numbers",
        "How to implement a DAG blockchain from scratch in Rust including data structures transaction validation and tip selection with complete code",
        "Explain Merkle DAG structure used in IPFS and Git including content addressing CID format and recursive linking for file storage",
    ],

    "Domain 1B - Cloud Data Storage Systems": [
        "How do enterprise cloud storage systems like AWS S3 Azure Blob and Google Cloud Storage architect their backend for 99.999999999 percent durability",
        "Explain erasure coding Reed-Solomon codes for distributed storage including how data is split into shards with parity for fault tolerance",
        "How does content-addressable storage CAS work including content hashing deduplication and garbage collection for efficient storage",
        "Explain distributed hash tables DHT Kademlia Chord Pastry for routing and data lookup in decentralized storage networks",
        "How to implement file chunking with variable-size content-defined chunking using Rabin fingerprinting for efficient deduplication",
        "Explain the CAP theorem and how distributed storage systems choose between consistency availability and partition tolerance with real examples",
        "How do decentralized storage networks IPFS Filecoin Arweave Storj Sia incentivize storage providers and verify data integrity",
        "Design a complete personal cloud storage system architecture with encryption at rest data deduplication versioning and multi-device sync",
    ],

    "Domain 1C - Integrating DAG with Cloud Storage": [
        "How to use a DAG blockchain as the metadata and integrity layer for a decentralized cloud storage system with content-addressed chunks",
        "Explain how Filecoin uses proof of replication and proof of spacetime to verify storage providers are actually storing data",
        "How to implement end-to-end encrypted file storage where the DAG blockchain tracks encrypted chunk locations and access permissions",
        "Design a hybrid system where local storage is primary and DAG blockchain enables optional peer-to-peer file sharing with trusted nodes",
        "How to implement file versioning using a DAG where each version points to its parent creating a version history tree",
        "Explain how to handle large file ingestion splitting into chunks hashing each chunk building Merkle tree and registering on DAG",
        "How to implement access control lists ACL on a DAG blockchain so file owners can grant and revoke read write permissions cryptographically",
        "Design the complete data flow for upload download and sync in a DAG-based personal cloud storage system with offline support",
    ],

    # ══════════════════════════════════════════════════════════
    # DOMAIN 2: PROMPT ENGINEERING & AI UNDERSTANDING
    # ══════════════════════════════════════════════════════════

    "Domain 2A - Prompt Engineering Mastery": [
        "Explain all major prompting techniques zero-shot few-shot chain-of-thought tree-of-thought self-consistency ReAct with examples for each",
        "How to write system prompts that reliably control AI behavior including role assignment output format constraints and boundary setting",
        "Explain prompt injection attacks and defenses including direct injection indirect injection jailbreaking and how to build resistant systems",
        "How to optimize prompts for small language models 3B to 7B parameters including token efficiency structured output and constraint handling",
        "Explain retrieval augmented generation RAG prompt design including context window management source attribution and hallucination reduction",
        "How to design multi-turn conversation prompts that maintain context track topics handle follow-ups and manage long conversation history",
        "Explain agent prompting patterns including tool use formatting ReAct loops plan-and-execute and self-reflection with working examples",
        "How to evaluate prompt quality including A/B testing automated scoring rubric design and iterative prompt refinement methodology",
    ],

    "Domain 2B - Complex Prompt Understanding": [
        "How to decompose complex multi-part user requests into atomic subtasks that can be routed to different AI agents or models",
        "Explain intent classification for routing user messages to the right handler including ambiguity resolution and multi-intent detection",
        "How to handle vague or underspecified prompts including clarification strategies assumption making and graceful degradation",
        "Explain meta-prompting where an AI generates or improves its own prompts including OPRO and automatic prompt optimization",
        "How to design prompts that produce structured output JSON XML markdown tables reliably from small language models",
        "Explain constitutional AI and RLHF techniques for aligning AI responses with human values and reducing harmful outputs",
        "How to build prompt templates that adapt to user expertise level beginner intermediate expert based on conversation history",
        "Explain how context window limitations affect prompt design and strategies for summarization compression and selective retrieval",
    ],

    # ══════════════════════════════════════════════════════════
    # DOMAIN 3: CLOUD STORAGE BUSINESS STRATEGY
    # ══════════════════════════════════════════════════════════

    "Domain 3A - Cloud Storage Industry Analysis": [
        "Analyze the cloud storage market landscape 2024-2026 including market size growth rate key players market share and emerging trends",
        "Compare business models of Dropbox Google Drive iCloud OneDrive Box and how each differentiates on pricing features and target market",
        "Explain the economics of running a cloud storage company including infrastructure costs per TB revenue per user and unit economics",
        "How do enterprise cloud storage companies like Box Egnyte and Citrix ShareFile sell to large organizations including sales cycles and pricing",
        "Analyze emerging decentralized storage competitors Filecoin Storj Arweave and their business models versus traditional cloud storage",
        "What are the key regulatory requirements for cloud storage companies including GDPR SOC2 HIPAA FedRAMP and data sovereignty laws",
        "Explain customer acquisition strategies for cloud storage startups including freemium PLG enterprise sales and partnership channels",
        "How to analyze competitive advantages and moats in cloud storage including switching costs network effects and data gravity",
    ],

    "Domain 3B - Building a Cloud Storage Company": [
        "Create a complete business plan outline for a DAG-based decentralized cloud storage startup including mission vision and value proposition",
        "Design the organizational structure for a cloud storage startup including key roles engineering sales marketing legal and operations",
        "Explain go-to-market strategy for a new cloud storage product including target segments positioning messaging and launch timeline",
        "How to build a financial model for a SaaS cloud storage company including MRR ARR churn LTV CAC and unit economics projections",
        "Design a pricing strategy for a cloud storage product including free tier pro tier enterprise tier and usage-based components",
        "Explain fundraising strategy for a cloud storage startup including seed Series A pitch deck structure and investor targeting",
        "How to build strategic partnerships for a cloud storage company including technology partners channel partners and integration ecosystem",
        "Create a product roadmap for a DAG-based cloud storage product covering MVP to enterprise-ready including feature prioritization",
    ],

    "Domain 3C - Executive Strategy & Board Advisory": [
        "How does a board of directors operate for a technology startup including board composition meetings fiduciary duties and governance",
        "Explain strategic planning frameworks OKRs SWOT Porters Five Forces Blue Ocean for a cloud storage company with specific examples",
        "How to conduct a quarterly business review QBR for a SaaS company including KPI dashboards financial review and strategic decisions",
        "Explain mergers and acquisitions strategy for cloud storage including buy vs build analysis due diligence and integration planning",
        "How to manage a technology company through hypergrowth including hiring scaling culture preservation and operational excellence",
        "Explain crisis management and business continuity planning for a cloud storage company including data breach response and disaster recovery",
        "How to build an advisory board for a tech startup including selecting advisors compensation structures and maximizing advisor value",
        "Explain exit strategy options for a cloud storage startup including IPO acquisition SPAC and private equity with valuation methods",
    ],

    # ══════════════════════════════════════════════════════════
    # DOMAIN 4: ACCOUNTING & FINANCE
    # ══════════════════════════════════════════════════════════

    "Domain 4A - Accounting Fundamentals & Practice": [
        "Explain double-entry bookkeeping system completely including debits credits journal entries ledgers trial balance and closing entries with examples",
        "How to read and analyze the three core financial statements income statement balance sheet and cash flow statement with real examples",
        "Explain Generally Accepted Accounting Principles GAAP including revenue recognition matching principle materiality and conservatism",
        "How to set up a chart of accounts for a technology startup including asset liability equity revenue and expense categories",
        "Explain accrual vs cash basis accounting including when to use each how to convert between them and implications for tax reporting",
        "How to handle accounts receivable and accounts payable including aging reports collections strategy and vendor payment terms",
        "Explain depreciation methods straight-line declining balance MACRS for business assets including software development capitalization",
        "How to prepare and file business taxes for a startup including estimated taxes quarterly filings deductions and R&D tax credits",
    ],

    "Domain 4B - Financial Analysis & Intelligence": [
        "Explain financial ratio analysis including liquidity profitability efficiency leverage and valuation ratios with formulas and interpretation",
        "How to build a complete financial model for a SaaS company in a spreadsheet including assumptions revenue model costs and projections",
        "Explain discounted cash flow DCF valuation including free cash flow calculation discount rate WACC terminal value and sensitivity analysis",
        "How to perform break-even analysis for a startup including fixed costs variable costs contribution margin and break-even revenue",
        "Explain unit economics for subscription businesses including LTV CAC LTV/CAC ratio payback period and cohort analysis",
        "How to create a cash flow forecast for a startup including runway calculation burn rate scenarios and fundraising timing",
        "Explain financial due diligence for investors or acquirers including quality of earnings revenue quality and working capital analysis",
        "How to set up management reporting and KPI dashboards for a SaaS company including MRR churn NRR and operating metrics",
    ],

    "Domain 4C - Advanced Finance & Tax Strategy": [
        "Explain corporate tax planning strategies for technology companies including R&D credits Section 179 deductions and qualified small business stock",
        "How to structure a company for tax efficiency including LLC vs S-Corp vs C-Corp selection state tax considerations and holding companies",
        "Explain stock option accounting including ISO vs NSO 409A valuations expense recognition and tax implications for founders and employees",
        "How to manage international tax considerations for a global SaaS company including transfer pricing VAT and permanent establishment",
        "Explain revenue recognition ASC 606 for SaaS companies including performance obligations transaction price allocation and contract modifications",
        "How to structure a cap table for a startup including founders shares option pool SAFE notes convertible notes and dilution modeling",
        "Explain financial controls and audit preparation for a growing company including SOX compliance internal controls and audit readiness",
        "How to analyze and optimize SaaS metrics including gross margin operating margin rule of 40 magic number and efficiency score",
    ],
}


def unload_models():
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=5)
        if resp.ok:
            for m in resp.json().get("models", []):
                requests.post(f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": m["name"], "keep_alive": 0}, timeout=10)
    except:
        pass


def research_topic(topic, topic_id, memory, use_cloud=False):
    start = time.time()
    try:
        if use_cloud:
            from acumen.core.llm import get_llm
            llm = get_llm("cloud")
        else:
            from acumen.core.llm import get_llm
            llm = get_llm("reasoning")

        prompt = (
            f"You are an expert researcher and educator. Research this topic thoroughly "
            f"and write a comprehensive, detailed guide. Include specific examples, "
            f"formulas, code snippets, and practical applications where relevant.\n\n"
            f"Topic: {topic}\n\n"
            f"Write at least 500 words. Be specific and technical, not vague."
        )

        result = llm.invoke(prompt)
        duration = time.time() - start
        words = len(result.split())

        # Save to knowledge base
        topic_short = topic[:100].replace(" ", "_").lower()
        topic_category = topic_id.split("_")[0] if "_" in topic_id else "general"

        memory.save_knowledge(
            result[:3000],
            {
                "topic": topic_short,
                "source": "overnight_expansion",
                "category": topic_category,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "words": str(words),
            },
        )

        # Also save as episode for context
        memory.save_episode(
            "knowledge_expansion",
            result[:1500],
            {"topic": topic[:100], "domain": topic_category},
        )

        return {"status": "OK", "words": words, "duration": round(duration, 1)}

    except Exception as e:
        duration = time.time() - start
        return {"status": "ERROR", "error": str(e)[:200], "duration": round(duration, 1)}


def run_expansion(domains=None, use_cloud=False):
    memory = MemoryManager()

    # Filter domains if specified
    if domains:
        filtered = {}
        for key, topics in TOPICS.items():
            domain_num = key.split(" ")[1][0]  # Extract "1", "2", "3", "4"
            if domain_num in [str(d) for d in domains]:
                filtered[key] = topics
        topics_to_run = filtered
    else:
        topics_to_run = TOPICS

    # Count totals
    total = sum(len(t) for t in topics_to_run.values())

    print("\n" + "=" * 60)
    print("  ACUMEN OVERNIGHT KNOWLEDGE EXPANSION")
    print("=" * 60)
    print(f"\n  Domains: {len(topics_to_run)}")
    print(f"  Topics: {total}")
    print(f"  Estimated time: {total * 2}-{total * 4} minutes")
    print(f"  Mode: {'Cloud (Claude)' if use_cloud else 'Local (qwen2.5:3b)'}")

    try:
        kb_count = memory.knowledge_count()
        print(f"  Knowledge base: {kb_count} docs")
    except:
        pass

    print(f"\n  Domains to research:")
    for key in topics_to_run:
        print(f"    • {key} ({len(topics_to_run[key])} topics)")

    print("\n" + "=" * 60 + "\n")

    # Research loop
    results = []
    errors = 0
    total_words = 0
    start_time = time.time()
    topic_num = 0

    for domain_name, domain_topics in topics_to_run.items():
        print(f"\n{'─' * 60}")
        print(f"  {domain_name} ({len(domain_topics)} topics)")
        print(f"{'─' * 60}\n")

        for topic in domain_topics:
            topic_num += 1
            topic_id = f"d{domain_name.split(' ')[1][0]}_{topic_num:03d}"
            short = topic[:75] + "..." if len(topic) > 75 else topic

            print(f"  [{topic_num}/{total}] {short}", end=" ", flush=True)

            result = research_topic(topic, topic_id, memory, use_cloud)

            if result["status"] == "OK":
                print(f"OK ({result['words']}w, {result['duration']}s)")
                total_words += result["words"]
            else:
                print(f"ERROR: {result.get('error', '?')[:60]}")
                errors += 1

            results.append({
                "num": topic_num, "topic": topic,
                "domain": domain_name, **result,
            })

        # Unload models between domains
        print(f"\n  [Cleanup] Unloading models...")
        unload_models()
        time.sleep(3)

    # Summary
    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("  KNOWLEDGE EXPANSION COMPLETE!")
    print("=" * 60)
    print(f"  Topics researched: {total}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed / 60:.1f} minutes")
    print(f"  Total words: {total_words}")

    try:
        kb_count = memory.knowledge_count()
        print(f"  Knowledge base: {kb_count} docs")
    except:
        pass

    print("=" * 60 + "\n")

    # Save report
    output_dir = Path.home() / "acumen" / "data" / "research" / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / f"expansion_{datetime.now():%H%M%S}.json"
    report_file.write_text(json.dumps({
        "completed": datetime.now().isoformat(),
        "total": total, "errors": errors,
        "total_words": total_words,
        "duration_minutes": round(elapsed / 60, 1),
        "mode": "cloud" if use_cloud else "local",
        "results": results,
    }, indent=2))
    print(f"  Report: {report_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Acumen Overnight Knowledge Expansion")
    parser.add_argument("--domain", type=int, nargs="+",
        help="Run specific domains: 1=blockchain, 2=prompts, 3=business, 4=finance")
    parser.add_argument("--cloud", action="store_true",
        help="Use Claude for deeper, more detailed responses (costs API credits)")
    args = parser.parse_args()

    run_expansion(domains=args.domain, use_cloud=args.cloud)


if __name__ == "__main__":
    main()
