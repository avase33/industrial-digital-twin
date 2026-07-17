"""idt intelligence — from-scratch spatial GNN anomaly detection + repair agent."""

from .agent import RepairAgent, build_agent, classify_fault
from .detector import Detector
from .gnn import divergence, embeddings
from .models import Graph, Node, NodeScore
from .synth import factory, inject_faults

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "RepairAgent",
    "build_agent",
    "classify_fault",
    "Detector",
    "divergence",
    "embeddings",
    "Graph",
    "Node",
    "NodeScore",
    "factory",
    "inject_faults",
]
