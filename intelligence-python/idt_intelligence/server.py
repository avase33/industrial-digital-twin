"""FastAPI service for the GNN detector. Fits on a synthetic healthy factory at
startup; POST a graph to /score to get per-node health + anomalies."""

from __future__ import annotations

from typing import Any

from .detector import Detector
from .models import Graph
from .synth import factory

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError as e:  # pragma: no cover
    raise RuntimeError("Install server extras: pip install 'idt-intelligence[server]'") from e

app = FastAPI(title="idt-intelligence", version="0.1.0")
_detector = Detector().fit(factory())


class ScoreReq(BaseModel):
    graph: dict[str, Any]


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "intelligence", "agent": _detector.agent.name,
                         "fitted": _detector.fitted})


@app.post("/score")
def score(req: ScoreReq) -> dict[str, Any]:
    graph = Graph.from_dict(req.graph)
    return {"nodes": [n.to_dict() for n in _detector.score(graph)]}
