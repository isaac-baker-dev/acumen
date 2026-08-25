"""Acumen Knowledge Base Health Check - Run anytime to check KB quality."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from acumen.memory import MemoryManager

def main():
    m = MemoryManager()
    collection = m.semantic.collection
    all_data = collection.get(include=["metadatas", "documents"])
    total = len(all_data["ids"])

    # Count by topic
    topics = {}
    junk = 0
    short = 0
    for i, meta in enumerate(all_data["metadatas"]):
        topic = meta.get("topic", "unknown")
        doc = all_data["documents"][i] or ""
        if topic == "learned" and "You are Acumen" in doc[:100]:
            junk += 1
            continue
        if len(doc) < 50:
            short += 1
        topics[topic] = topics.get(topic, 0) + 1

    print(f"\n{'='*50}")
    print(f"  ACUMEN KB HEALTH CHECK")
    print(f"{'='*50}")
    print(f"\n  Total documents: {total}")
    print(f"  Junk (system prompt copies): {junk}")
    print(f"  Short docs (<50 chars): {short}")
    print(f"  Healthy docs: {total - junk - short}")
    print(f"\n  Topics breakdown:")

    for topic, count in sorted(topics.items(), key=lambda x: -x[1])[:20]:
        bar = "█" * min(count // 5, 30)
        print(f"    {topic[:30]:30s} {count:4d} {bar}")

    print(f"\n  ... {len(topics)} total topics")

    if junk > 0:
        print(f"\n  ⚠ Found {junk} junk entries. Run:")
        print(f"    python -c \"from acumen.memory import MemoryManager; m=MemoryManager(); c=m.semantic.collection; d=c.get(include=['metadatas','documents']); ids=[d['ids'][i] for i,m in enumerate(d['metadatas']) if m.get('topic')=='learned' and 'You are Acumen' in (d['documents'][i] or '')[:100]]; c.delete(ids=ids); print(f'Deleted {{len(ids)}}')\"")
    else:
        print(f"\n  ✓ No junk found. KB is clean!")

    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()