"""
Acumen Metagraph Engine
========================
In-memory graph database for meta-orchestration.
Tracks all system entities and their relationships.
Supports queries, path finding, and dynamic graph modification.
"""

from collections import defaultdict
from acumen.metagraph.model import MetaNode, MetaEdge, NodeType, EdgeType
from acumen.core.logger import get_logger

logger = get_logger("acumen.metagraph")

class MetagraphEngine:
    """The meta-orchestration brain of Acumen."""

    def __init__(self):
        self.nodes: dict[str, MetaNode] = {}
        self.edges: list[MetaEdge] = []
        self._adj: dict[str, list[MetaEdge]] = defaultdict(list)
        self._rev: dict[str, list[MetaEdge]] = defaultdict(list)
        logger.info("Metagraph Engine initialized")

    # -- Node Operations --
    def add_node(self, node: MetaNode) -> None:
        self.nodes[node.id] = node
        logger.debug(f"Node added: {node.id} ({node.node_type.value})")

    def get_node(self, node_id: str) -> MetaNode | None:
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[MetaNode]:
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def get_nodes_by_status(self, status: str) -> list[MetaNode]:
        return [n for n in self.nodes.values() if n.status == status]

    def update_status(self, node_id: str, status: str) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].status = status

    # -- Edge Operations --
    def add_edge(self, edge: MetaEdge) -> None:
        self.edges.append(edge)
        self._adj[edge.source_id].append(edge)
        self._rev[edge.target_id].append(edge)
        logger.debug(f"Edge: {edge.source_id} -{edge.edge_type.value}-> {edge.target_id}")

    def get_outgoing(self, node_id: str, edge_type: EdgeType = None) -> list[MetaEdge]:
        edges = self._adj.get(node_id, [])
        if edge_type:
            return [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_incoming(self, node_id: str, edge_type: EdgeType = None) -> list[MetaEdge]:
        edges = self._rev.get(node_id, [])
        if edge_type:
            return [e for e in edges if e.edge_type == edge_type]
        return edges

    # -- Queries --
    def get_dependencies(self, node_id: str) -> list[MetaNode]:
        """What does this node depend on?"""
        deps = self.get_outgoing(node_id, EdgeType.DEPENDS_ON)
        return [self.nodes[e.target_id] for e in deps if e.target_id in self.nodes]

    def get_dependents(self, node_id: str) -> list[MetaNode]:
        """What depends on this node?"""
        deps = self.get_incoming(node_id, EdgeType.DEPENDS_ON)
        return [self.nodes[e.source_id] for e in deps if e.source_id in self.nodes]

    def get_idle_agents(self) -> list[MetaNode]:
        """Find agents available for task assignment."""
        return [n for n in self.get_nodes_by_type(NodeType.AGENT)
                if n.status in ("active", "idle")]

    def get_agent_for_task(self, task_type: str) -> MetaNode | None:
        """Find the best available agent for a task type."""
        for agent in self.get_idle_agents():
            skills = agent.metadata.get("skills", [])
            if task_type in skills:
                return agent
        return None

    # -- Pipeline Composition --
    def compose_pipeline(self, name: str, task_ids: list[str]) -> MetaNode:
        """Create a pipeline node that composes existing task nodes."""
        pipeline = MetaNode(
            id=f"pipe_{name}",
            name=name,
            node_type=NodeType.PIPELINE,
            metadata={"task_count": len(task_ids)},
        )
        self.add_node(pipeline)
        for task_id in task_ids:
            self.add_edge(MetaEdge(
                source_id=pipeline.id,
                target_id=task_id,
                edge_type=EdgeType.COMPOSES,
            ))
        logger.info(f"Pipeline composed: {name} ({len(task_ids)} tasks)")
        return pipeline

    # -- System Registration --
    def register_agent(self, agent_id: str, name: str,
                       skills: list[str], model: str) -> MetaNode:
        """Register an agent in the Metagraph."""
        node = MetaNode(
            id=agent_id, name=name,
            node_type=NodeType.AGENT,
            metadata={"skills": skills, "model": model,
                      "tasks_completed": 0, "avg_duration": 0},
        )
        self.add_node(node)
        return node

    def register_data_source(self, source_id: str,
                             name: str, source_type: str) -> MetaNode:
        """Register a data source (ChromaDB, SQLite, etc.)."""
        node = MetaNode(
            id=source_id, name=name,
            node_type=NodeType.DATA,
            metadata={"type": source_type},
        )
        self.add_node(node)
        return node

    # -- Statistics --
    def stats(self) -> dict:
        type_counts = {}
        for n in self.nodes.values():
            type_counts[n.node_type.value] = type_counts.get(n.node_type.value, 0) + 1
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "by_type": type_counts,
        }

# Singleton instance
metagraph = MetagraphEngine()