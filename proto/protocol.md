# industrial-digital-twin wire protocol

A distributed digital-twin network for factory-floor anomaly detection. Each
language owns its domain; one JSON contract connects them.

```
sensors (MQTT) ──▶ Go hub ──▶ Rust topology ──▶ Python GNN ──▶ anomalies
                     │  (ingest+timestamp)  (point-cloud clean)   (divergence)
                     └──WebSocket──▶ TypeScript 3D twin ◀── node health ──┘
```

## 1. Sensors ⇄ Hub (Go)

```jsonc
POST /ingest { "readings": [
  { "node": "M07", "temp": 71.2, "vibration": 0.8, "rotation": 1490,
    "pos": [3.0, 1.0, 0.0] } ] }
GET  /health
WS   /ws/twin   -> streamed { "nodes": [ { node, health, anomaly, ... } ] }
```

## 2. Hub ⇄ Topology (Rust)

```jsonc
POST /clean { "points": [ { "node": "M07", "coords": [[x,y,z], ...] } ] }
->
{ "frames": [ { "node": "M07", "centroid": [x,y,z], "kept": 118, "dropped": 10,
               "spread": 0.42 } ] }   // statistical outlier removal + transform
GET /health
```

## 3. Hub ⇄ Intelligence (Python)

```jsonc
POST /score { "graph": { "nodes": [ { node, features: {temp, vibration, rotation},
                                      pos: [x,y,z] } ],
                         "edges": [ ["M07","M08"], ... ] } }
->
{ "nodes": [ { "node": "M07", "divergence": 0.31, "health": 0.31, "anomaly": true,
               "incident": { "severity": "high", "summary": "...",
                             "repair": ["inspect bearing", "reduce RPM"] } } ] }
GET /health
```

## The math

The GNN scores each node by its **spatial divergence** from its neighbours:

    D(x) = (1/|N(x)|) · Σ_{y∈N(x)} exp( −‖x − y‖² / (2σ²) )

computed on message-passed node embeddings. A healthy node sits close to its
neighbourhood (high D); a node whose sensors have drifted is isolated (low D →
anomaly). `‖x − y‖` uses the Euclidean distances the Rust layer computes; `σ` is
the baseline operating variance. Offline everything is from-scratch; set
`IDT_LLM=openai` for richer repair write-ups.
