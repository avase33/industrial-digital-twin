# industrial-digital-twin 🏭

**A distributed digital twin for factory-floor anomaly detection.** Go ingests
thousands of sensors, Rust cleans LiDAR point clouds, a from-scratch Python
**spatial GNN** flags machines whose behaviour has drifted before they fail, and a
Three.js twin shows the whole floor lighting up red in real time.

Four languages, each on the layer it's built for, over one JSON protocol:

```
sensors (MQTT) ──▶ Go hub ──▶ Rust topology ──▶ Python GNN ──▶ anomalies
                     │  (ingest+timestamp)  (point-cloud clean)  (divergence)
                     └──WebSocket──▶ TypeScript 3D twin ◀── node health ──┘
```

| Layer | Language | Owns |
| --- | --- | --- |
| **Hub** | Go | High-density MQTT sensor ingest, timestamps, twin broadcast |
| **Topology** | Rust | LiDAR point-cloud outlier removal + geometric features |
| **Intelligence** | Python | Spatial GNN anomaly detection + repair agent |
| **Interface** | TypeScript / Three.js | WebGL 3D factory floor, health-coloured nodes |

Runs **offline** — a from-scratch GNN (no torch-geometric), a built-in factory
simulator with fault injection, and a self-contained point-cloud cleaner.

## Quickstart — the GNN, offline

```bash
cd intelligence-python && pip install -e .
python -m idt_intelligence.cli demo
```

```
idt intelligence — agent=mock  16 nodes  threshold=0.3xx
  M00  health=0.7x
  ...
  M05  health=0.0x  ⚠ ANOMALY
      [critical] overheating: ['cut feed rate 20%', 'inspect coolant flow', ...]
  M10  health=0.0x  ⚠ ANOMALY
  ...
  anomalies: ['M05', 'M10']
```

Offline end-to-end check:

```bash
python scripts/verify.py     # RESULT: N passed, 0 failed
```

## Quickstart — the whole twin

```bash
docker compose up --build
# Twin:         http://localhost:3000   (watch machines flash red on fault)
# Hub:          http://localhost:8080/health
# Topology:     http://localhost:8092/health
# Intelligence: http://localhost:8000/health
```

Or run layers standalone:

```bash
cd topology-rust      && cargo run                                            # :8092
cd intelligence-python && pip install -e ".[server]" && idt-intelligence serve # :8000
cd hub-go             && IDT_INTEL_URL=http://localhost:8000 go run .          # :8080
cd interface-ts       && npm install && npm run dev                           # :3000
```

## The interesting engineering

- **Spatial GNN (Python)** — feature standardisation, mean-aggregation message
  passing, and the divergence kernel `D(x)=1/|N| Σ exp(−‖x−y‖²/2σ²)`, all from
  scratch. `intelligence-python/idt_intelligence/gnn.py`
- **Point-cloud cleaning (Rust)** — statistical outlier removal + centroid/spread
  over 3D coordinate arrays, the hot loop that would crawl in Python.
  `topology-rust/src/cloud.rs`
- **Go hub** — assembles the factory graph each tick, scores it via the GNN, and
  streams per-node health to every connected twin. `hub-go/`
- **Repair agent** — classifies the fault and drafts repair steps for each
  anomalous node. `intelligence-python/idt_intelligence/agent.py`
- **Three.js twin (TS)** — a WebGL mesh per machine, recoloured by health and
  flashing on anomaly. `interface-ts/app/page.tsx`

## Testing

```bash
make test                        # rust + python + go
cd intelligence-python && pytest -q
cd topology-rust       && cargo test
cd hub-go              && go test ./...
cd interface-ts        && npm run build
```

## Layout

```
proto/               shared JSON wire protocol
interface-ts/        Next.js + Three.js 3D digital twin
hub-go/              Go sensor ingestion hub (grid sim, GNN scoring, WS)
topology-rust/       Rust point-cloud cleaner (outlier removal, geometry)
intelligence-python/ spatial GNN anomaly detector + repair agent + FastAPI
scripts/verify.py    offline end-to-end check
docs/ARCHITECTURE.md
```

## License

MIT © 2026 Akhil Vase
