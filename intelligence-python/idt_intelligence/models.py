"""Shared types (see proto/protocol.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

FEATURE_KEYS = ["temp", "vibration", "rotation"]


@dataclass
class Node:
    id: str
    features: dict[str, float]
    pos: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])


@dataclass
class Graph:
    nodes: list[Node]
    edges: list[tuple[str, str]]

    def node(self, nid: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.id == nid), None)

    def adjacency(self) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {n.id: [] for n in self.nodes}
        for a, b in self.edges:
            if a in adj and b in adj:
                adj[a].append(b)
                adj[b].append(a)
        return adj

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Graph":
        nodes = [
            Node(n["node"], {k: float(n["features"].get(k, 0.0)) for k in FEATURE_KEYS},
                 list(n.get("pos", [0.0, 0.0, 0.0])))
            for n in d.get("nodes", [])
        ]
        edges = [(e[0], e[1]) for e in d.get("edges", [])]
        return Graph(nodes=nodes, edges=edges)


@dataclass
class NodeScore:
    node: str
    divergence: float
    health: float
    anomaly: bool
    incident: Optional[dict] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "node": self.node,
            "divergence": round(self.divergence, 4),
            "health": round(self.health, 4),
            "anomaly": self.anomaly,
        }
        if self.incident is not None:
            d["incident"] = self.incident
        return d
