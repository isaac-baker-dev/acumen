"""
Acumen Metagraph Bootstrap
===========================
Registers all system components in the Metagraph on startup.
"""

from acumen.metagraph.engine import metagraph, MetaNode, MetaEdge, NodeType, EdgeType

def bootstrap_metagraph():
    """Register all agents, data sources, and base relationships."""

    # Register agents
    agents = [
        ("agent_strategist", "Strategist", ["planning","delegation","synthesis"], "reasoning"),
        ("agent_researcher", "Research Analyst", ["research","analysis","summarization"], "reasoning"),
        ("agent_engineer", "Software Engineer", ["coding","testing","documentation"], "code"),
        ("agent_debugger", "Debugger", ["debugging","review","security_audit"], "reasoning"),
        ("agent_automator", "Automation Engineer", ["pipelines","scheduling","monitoring"], "fast"),
        ("agent_security", "Security Analyst", ["security","monitoring","audit"], "fast"),
        ("agent_knowledge", "Knowledge Archivist", ["ingestion","curation","search"], "reasoning"),
    ]
    for aid, name, skills, model in agents:
        metagraph.register_agent(aid, name, skills, model)

    # Register data sources
    metagraph.register_data_source("ds_chromadb", "ChromaDB Knowledge Base", "vector_db")
    metagraph.register_data_source("ds_episodic", "Episodic Memory (SQLite)", "relational_db")
    metagraph.register_data_source("ds_working", "Working Memory", "in_memory")

    # Register delegation relationships
    delegations = [
        ("agent_strategist", "agent_researcher"),
        ("agent_strategist", "agent_engineer"),
        ("agent_strategist", "agent_debugger"),
        ("agent_strategist", "agent_automator"),
        ("agent_researcher", "agent_knowledge"),
    ]
    for src, tgt in delegations:
        metagraph.add_edge(MetaEdge(src, tgt, EdgeType.DELEGATES_TO))

    # Register data consumption
    for aid, _, _, _ in agents:
        metagraph.add_edge(MetaEdge(aid, "ds_chromadb", EdgeType.CONSUMES))

    metagraph.add_edge(MetaEdge("agent_security", "agent_strategist", EdgeType.MONITORS))

    stats = metagraph.stats()
    print(f"Metagraph bootstrapped: {stats['total_nodes']} nodes, {stats['total_edges']} edges")