"""A spatial Graph Neural Network for anomaly detection — from scratch.

Node sensor readings are standardised, then smoothed by a few rounds of
mean-aggregation message passing over the machine topology. The spatial
**divergence** of each node from its neighbourhood,

    D(x) = (1/|N(x)|) · Σ_{y∈N(x)} exp( −‖e_x − e_y‖² / (2σ²) ),

measures how well the node fits its local structure. Healthy nodes sit close to
their neighbours (high D); a node whose sensors have drifted becomes isolated in
embedding space (low D). No numpy / torch-geometric.
"""

from __future__ import annotations

import math

from .models import FEATURE_KEYS, Graph


def baseline_stats(graph: Graph) -> tuple[dict[str, float], dict[str, float]]:
    n = max(1, len(graph.nodes))
    mean: dict[str, float] = {}
    std: dict[str, float] = {}
    for k in FEATURE_KEYS:
        vals = [nd.features.get(k, 0.0) for nd in graph.nodes]
        m = sum(vals) / n
        var = sum((v - m) ** 2 for v in vals) / n
        mean[k] = m
        std[k] = math.sqrt(var) or 1.0
    return mean, std


def feature_vec(features: dict[str, float], mean: dict[str, float], std: dict[str, float]) -> list[float]:
    return [(features.get(k, 0.0) - mean[k]) / (std[k] or 1.0) for k in FEATURE_KEYS]


def embeddings(graph: Graph, mean, std, layers: int = 2, alpha: float = 0.5) -> dict[str, list[float]]:
    adj = graph.adjacency()
    h = {nd.id: feature_vec(nd.features, mean, std) for nd in graph.nodes}
    dim = len(FEATURE_KEYS)
    for _ in range(layers):
        new_h: dict[str, list[float]] = {}
        for nid, hv in h.items():
            nbrs = adj.get(nid, [])
            if nbrs:
                agg = [0.0] * dim
                for j in nbrs:
                    for i in range(dim):
                        agg[i] += h[j][i]
                agg = [x / len(nbrs) for x in agg]
                new_h[nid] = [alpha * hv[i] + (1 - alpha) * agg[i] for i in range(dim)]
            else:
                new_h[nid] = hv
        h = new_h
    return h


def dist2(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def divergence(graph: Graph, emb: dict[str, list[float]], sigma: float) -> dict[str, float]:
    adj = graph.adjacency()
    two_s2 = 2.0 * sigma * sigma or 1e-9
    out: dict[str, float] = {}
    for nid in emb:
        nbrs = adj.get(nid, [])
        if not nbrs:
            out[nid] = 1.0
            continue
        s = sum(math.exp(-dist2(emb[nid], emb[j]) / two_s2) for j in nbrs)
        out[nid] = s / len(nbrs)
    return out
