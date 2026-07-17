# industrial-digital-twin architecture

A distributed digital-twin network for factory-floor anomaly detection. Each
language owns its domain; one JSON contract (`proto/protocol.md`) connects them.

```
   sensors (MQTT) + LiDAR
        │
        ▼
┌──────────────────────────┐   HTTP /clean    ┌──────────────────────────┐
│ Hub · Go                 │ ───────────────▶ │ Topology · Rust          │
│ high-density ingest ·    │ ◀── frames       │ point-cloud outlier      │
│ timestamps · route       │   (centroid,     │ removal + geometry       │
│ twin broadcast (WS)      │    spread)       │                          │
└───────┬──────────────────┘                  └──────────────────────────┘
        │ HTTP /score  (graph of machine nodes)
        ▼
┌──────────────────────────┐
│ Intelligence · Python    │  spatial GNN: message passing + divergence D(x)
│ anomaly + repair agent   │
└───────┬──────────────────┘
        │ WebSocket /ws/twin  (per-node health)
        ▼
┌──────────────────────────┐
│ Interface · TypeScript   │  Three.js factory floor, nodes coloured by health
└──────────────────────────┘
```

## Why each language

| Layer | Language | Reason |
| --- | --- | --- |
| Hub | **Go** | Thousands of sensor streams over MQTT with minimal memory overhead. |
| Topology | **Rust** | Volumetric coordinate/matrix work at hardware speed, no GC pauses. |
| Intelligence | **Python** | Graph learning ecosystem; here a from-scratch spatial GNN. |
| Interface | **TypeScript** | WebGL / Three.js 3D twin with live state. |

## Flow

1. The Go hub ingests sensor readings (temperature, vibration, rotation) for every
   machine node and, for LiDAR frames, ships point clouds to the Rust topology
   service which strips noise and returns clean centroids + spread.
2. Each tick the hub assembles the factory **graph** (nodes + machine-topology
   edges) and sends it to the Python GNN.
3. The GNN standardises features, runs light message passing, and scores each node
   by its spatial **divergence** from its neighbourhood. Low divergence = the node
   has drifted away from its healthy neighbours = anomaly.
4. For each anomaly the repair agent classifies the fault (overheating, excess
   vibration, RPM anomaly, sensor drift) and drafts repair steps.
5. The hub broadcasts per-node health to the Three.js twin, which recolours the
   corresponding machine mesh (green → red) and lists the incident + repair.

## The math

    D(x) = (1/|N(x)|) · Σ_{y∈N(x)} exp( −‖e_x − e_y‖² / (2σ²) )

computed on message-passed node embeddings `e`. `‖·‖` is the Euclidean distance
the Rust layer specialises in; `σ` is the baseline operating variance learned at
fit time. See `intelligence-python/idt_intelligence/gnn.py`.

## Offline-first

- **Intelligence**: from-scratch GNN + rule-based repair agent → no
  torch-geometric, no keys. `IDT_LLM=openai` writes richer repair configs.
- **Go**: a built-in factory simulator (with fault injection) drives the twin with
  no MQTT broker.
- **Rust**: the point-cloud cleaner is self-contained.

`docker compose up` gives a live 3D twin you can watch faults appear on;
`make demo` runs the detector with no services at all.
