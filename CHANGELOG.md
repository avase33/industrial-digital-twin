# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-07-17

Initial release — a four-language industrial digital-twin anomaly pipeline.

### Added
- **Python intelligence**: a from-scratch spatial GNN — feature standardisation,
  mean-aggregation message passing, and the spatial divergence kernel
  `D(x)=1/|N| Σ exp(−‖x−y‖²/2σ²)` — that fits on a healthy factory and flags nodes
  whose sensors drift, plus a repair agent (fault classification + steps). FastAPI
  `/score`, CLI, synthetic factory + fault injection, tests + offline verifier.
- **Rust topology**: LiDAR-style point-cloud cleaning — statistical outlier
  removal, centroid + spread geometric features. axum `/clean`. Unit tests.
- **Go hub**: factory sensor-grid simulator (MQTT-shaped ingest), scores the graph
  via the Python GNN each tick, and streams per-node health to the twin over
  WebSocket. Tests.
- **Next.js + Three.js interface**: a live WebGL factory floor — a mesh per
  machine, coloured by health and flashing red on anomaly, with an active-incident
  panel showing the drafted repair steps.
- Shared JSON protocol, docker-compose, per-language Dockerfiles, multi-language
  CI, Makefile, MIT license.
