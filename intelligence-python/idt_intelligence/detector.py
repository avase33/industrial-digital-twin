"""Fit the GNN on a healthy baseline, then flag nodes whose spatial divergence
drops below the learned threshold."""

from __future__ import annotations

import math
from typing import Optional

from .agent import RepairAgent, build_agent
from .gnn import baseline_stats, dist2, divergence, embeddings
from .models import Graph, NodeScore


class Detector:
    def __init__(self, agent: Optional[RepairAgent] = None, layers: int = 1, alpha: float = 0.9) -> None:
        self.agent = agent or build_agent()
        self.layers = layers          # light message passing keeps outliers isolated
        self.alpha = alpha            # self-retention weight per GNN layer
        self.mean: dict[str, float] = {}
        self.std: dict[str, float] = {}
        self.sigma = 1.0
        self.threshold = 0.0
        self.fitted = False

    def fit(self, baseline: Graph) -> "Detector":
        self.mean, self.std = baseline_stats(baseline)
        emb = embeddings(baseline, self.mean, self.std, self.layers, self.alpha)
        adj = baseline.adjacency()

        # sigma = median neighbour distance in embedding space
        dists = [
            math.sqrt(dist2(emb[nid], emb[j]))
            for nid, nbrs in adj.items()
            for j in nbrs
        ]
        dists.sort()
        self.sigma = (dists[len(dists) // 2] if dists else 1.0) or 1.0

        d = divergence(baseline, emb, self.sigma)
        vals = list(d.values())
        mean_d = sum(vals) / max(1, len(vals))
        # anomalies fall well below the healthy neighbourhood density
        self.threshold = 0.5 * mean_d
        self.fitted = True
        return self

    def score(self, graph: Graph) -> list[NodeScore]:
        if not self.fitted:
            raise RuntimeError("detector not fitted — call fit() on a healthy baseline first")
        emb = embeddings(graph, self.mean, self.std, self.layers, self.alpha)
        d = divergence(graph, emb, self.sigma)
        out: list[NodeScore] = []
        for nd in graph.nodes:
            div = d[nd.id]
            anomaly = div < self.threshold
            incident = self.agent.repair(nd, div) if anomaly else None
            out.append(NodeScore(nd.id, div, health=div, anomaly=anomaly, incident=incident))
        return out
