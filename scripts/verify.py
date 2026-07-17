#!/usr/bin/env python3
"""Offline end-to-end check of the IDT spatial GNN.

Fits the from-scratch GNN on a healthy factory, injects bearing faults on two
machines, and verifies they're flagged (with repair configs) while the rest of the
floor stays nominal — no torch-geometric, no services.

    python scripts/verify.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "intelligence-python"))

from idt_intelligence.detector import Detector  # noqa: E402
from idt_intelligence.synth import factory, inject_faults  # noqa: E402

_passed = 0
_failed = 0


def check(label: str, cond: bool) -> None:
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def main() -> int:
    print("=" * 70)
    print("industrial-digital-twin - offline end-to-end verification")
    print("=" * 70)

    det = Detector().fit(factory(seed=1))
    faulted = inject_faults(factory(seed=2), ["M05", "M10"])
    scores = det.score(faulted)
    flagged = {s.node for s in scores if s.anomaly}
    print(f"  agent={det.agent.name}  nodes={len(faulted.nodes)}  "
          f"threshold={det.threshold:.3f}  flagged={sorted(flagged)}")

    check("detects fault on M05", "M05" in flagged)
    check("detects fault on M10", "M10" in flagged)
    check("low collateral (<=5 flagged total)", len(flagged) <= 5)
    incidents = [s.incident for s in scores if s.anomaly and s.incident]
    check("anomalies carry a repair config", bool(incidents) and all("repair" in i for i in incidents))

    clean = det.score(factory(seed=3))
    check("healthy factory stays (mostly) nominal",
          sum(1 for s in clean if s.anomaly) <= 2)

    print("-" * 70)
    print(f"RESULT: {_passed} passed, {_failed} failed")
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
