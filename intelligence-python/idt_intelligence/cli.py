"""CLI: ``idt-intelligence demo|serve``."""

from __future__ import annotations

import argparse
import sys

from .detector import Detector
from .synth import factory, inject_faults


def _demo(faults: list[str]) -> int:
    det = Detector().fit(factory(seed=1))
    live = inject_faults(factory(seed=2), faults or ["M05", "M10"])
    scores = det.score(live)

    print("=" * 68)
    print(f"idt intelligence — agent={det.agent.name}  {len(live.nodes)} nodes  "
          f"threshold={det.threshold:.3f}")
    print("=" * 68)
    for s in scores:
        flag = "  ⚠ ANOMALY" if s.anomaly else ""
        print(f"  {s.node}  health={s.health:.3f}{flag}")
        if s.incident:
            print(f"      [{s.incident['severity']}] {s.incident['kind']}: {s.incident['repair']}")
    anomalies = [s.node for s in scores if s.anomaly]
    print("-" * 68)
    print(f"  anomalies: {anomalies}")
    return 0


def _serve(host: str, port: int) -> int:
    try:
        import uvicorn  # type: ignore
    except ImportError:
        print("Install server extras: pip install 'idt-intelligence[server]'", file=sys.stderr)
        return 1
    uvicorn.run("idt_intelligence.server:app", host=host, port=port, log_level="info")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="idt-intelligence")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="fit on a healthy factory, inject faults, detect them")
    d.add_argument("faults", nargs="*")
    s = sub.add_parser("serve", help="run the FastAPI service")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    if args.cmd == "demo":
        return _demo(args.faults)
    return _serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
