"""Repair agent — classifies the fault behind an anomalous node and drafts a
structural repair configuration. Rule-based offline; LLM-written with a key."""

from __future__ import annotations

import os

from .models import Node

_STEPS = {
    "overheating": ["cut feed rate 20%", "inspect coolant flow", "schedule bearing thermal check"],
    "excess vibration": ["reduce spindle RPM", "inspect mounting bolts", "run balance calibration"],
    "rpm anomaly": ["verify drive controller", "check encoder wiring", "hold at safe RPM"],
    "sensor drift": ["recalibrate sensor", "compare to twin node", "flag for maintenance window"],
}


def classify_fault(node: Node) -> str:
    f = node.features
    if f.get("temp", 0.0) > 90.0:
        return "overheating"
    if f.get("vibration", 0.0) > 3.0:
        return "excess vibration"
    rpm = f.get("rotation", 1500.0)
    if rpm > 2500.0 or rpm < 300.0:
        return "rpm anomaly"
    return "sensor drift"


class RepairAgent:
    name = "mock"

    def repair(self, node: Node, divergence: float) -> dict:
        kind = classify_fault(node)
        severity = "critical" if divergence < 0.15 else "high" if divergence < 0.35 else "medium"
        return {
            "severity": severity,
            "kind": kind,
            "summary": f"{kind.title()} at {node.id} (health {divergence:.2f}); "
                       f"temp={node.features.get('temp'):.1f} vib={node.features.get('vibration'):.2f}",
            "repair": _STEPS.get(kind, _STEPS["sensor drift"]),
        }


class OpenAIAgent(RepairAgent):  # pragma: no cover - needs network + key
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def repair(self, node: Node, divergence: float) -> dict:
        base = super().repair(node, divergence)
        try:
            prompt = (
                "You are a reliability engineer. Given this anomalous machine node, write a one-line "
                f"summary and 3 concise repair steps.\nNode: {node.id} features={node.features}"
            )
            resp = self._client.chat.completions.create(
                model=self._model, messages=[{"role": "user", "content": prompt}], max_tokens=120
            )
            base["summary"] = resp.choices[0].message.content or base["summary"]
        except Exception:
            pass
        return base


def build_agent() -> RepairAgent:
    if os.environ.get("IDT_LLM", "mock").lower() == "openai" and os.environ.get("OPENAI_API_KEY"):
        return OpenAIAgent(os.environ["OPENAI_API_KEY"])
    return RepairAgent()
