from idt_intelligence.agent import classify_fault
from idt_intelligence.detector import Detector
from idt_intelligence.gnn import baseline_stats
from idt_intelligence.models import Node
from idt_intelligence.synth import factory, inject_faults


def test_grid_adjacency():
    g = factory(2, 2, seed=1)  # M00 M01 / M02 M03
    adj = g.adjacency()
    assert set(adj["M00"]) == {"M01", "M02"}
    assert set(adj["M03"]) == {"M01", "M02"}


def test_baseline_stats():
    mean, std = baseline_stats(factory(4, 4, seed=1))
    assert 60 < mean["temp"] < 80
    assert std["temp"] > 0


def test_detects_injected_faults():
    det = Detector().fit(factory(seed=1))
    live = inject_faults(factory(seed=2), ["M05", "M10"])
    scores = det.score(live)
    flagged = {s.node for s in scores if s.anomaly}
    assert "M05" in flagged
    assert "M10" in flagged
    assert len(flagged) <= 5  # low collateral / false positives
    for s in scores:
        if s.anomaly:
            assert s.incident is not None and "repair" in s.incident


def test_healthy_factory_has_few_anomalies():
    det = Detector().fit(factory(seed=1))
    scores = det.score(factory(seed=3))  # clean, unseen
    assert sum(1 for s in scores if s.anomaly) <= 2


def test_classify_fault_kinds():
    assert classify_fault(Node("x", {"temp": 110, "vibration": 0.8, "rotation": 1500})) == "overheating"
    assert classify_fault(Node("x", {"temp": 70, "vibration": 5.0, "rotation": 1500})) == "excess vibration"
    assert classify_fault(Node("x", {"temp": 70, "vibration": 0.8, "rotation": 100})) == "rpm anomaly"
