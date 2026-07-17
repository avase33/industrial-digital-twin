"""Synthetic factory floor: a grid of machine nodes with healthy sensor readings,
plus fault injection. Lets the GNN fit + detect end-to-end offline."""

from __future__ import annotations

import random

from .models import Graph, Node

NOMINAL = {"temp": 70.0, "vibration": 0.8, "rotation": 1500.0}


def factory(rows: int = 4, cols: int = 4, seed: int = 1) -> Graph:
    rng = random.Random(seed)
    nodes: list[Node] = []
    for r in range(rows):
        for c in range(cols):
            nid = f"M{r * cols + c:02d}"
            feats = {
                "temp": round(rng.gauss(NOMINAL["temp"], 1.5), 2),
                "vibration": round(rng.gauss(NOMINAL["vibration"], 0.1), 3),
                "rotation": round(rng.gauss(NOMINAL["rotation"], 25.0), 1),
            }
            nodes.append(Node(nid, feats, [float(c), float(r), 0.0]))
    edges: list[tuple[str, str]] = []
    for r in range(rows):
        for c in range(cols):
            nid = f"M{r * cols + c:02d}"
            if c + 1 < cols:
                edges.append((nid, f"M{r * cols + c + 1:02d}"))
            if r + 1 < rows:
                edges.append((nid, f"M{(r + 1) * cols + c:02d}"))
    return Graph(nodes, edges)


def inject_faults(graph: Graph, node_ids: list[str]) -> Graph:
    """Spike temperature + vibration on the given nodes (bearing failure signature)."""
    for nid in node_ids:
        nd = graph.node(nid)
        if nd:
            nd.features["temp"] += 35.0
            nd.features["vibration"] += 4.0
            nd.features["rotation"] -= 300.0
    return graph
