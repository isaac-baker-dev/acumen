"""
Acumen Metagraph Data Model
=============================
Defines the node and edge types that compose the system graph.
The Metagraph is an in-memory directed graph where nodes can be
tasks, pipelines, agents, crews, or data sources, and edges
represent relationships like depends_on, delegates_to, produces.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class NodeType(Enum):
    TASK = "task"
    PIPELINE = "pipeline"
    AGENT = "agent"
    CREW = "crew"
    DATA = "data"
    WORKFLOW = "workflow"

class EdgeType(Enum):
    DEPENDS_ON = "depends_on"
    DELEGATES_TO = "delegates_to"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    MONITORS = "monitors"
    COMPOSES = "composes"

@dataclass
class MetaNode:
    """A node in the Metagraph. Can represent any system entity."""
    id: str
    name: str
    node_type: NodeType
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"

@dataclass
class MetaEdge:
    """A directed edge between two MetaNodes."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: dict = field(default_factory=dict)
    weight: float = 1.0