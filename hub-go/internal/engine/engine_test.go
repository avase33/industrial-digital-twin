package engine

import (
	"testing"

	"github.com/avase33/industrial-digital-twin/hub/internal/config"
	"github.com/avase33/industrial-digital-twin/hub/internal/hub"
)

func TestGenGraphShape(t *testing.T) {
	cfg := config.Config{Rows: 4, Cols: 4}
	e := NewEngine(cfg, hub.New())
	g := e.GenGraph()
	nodes, _ := g["nodes"].([]map[string]any)
	edges, _ := g["edges"].([][]string)
	if len(nodes) != 16 {
		t.Fatalf("want 16 nodes, got %d", len(nodes))
	}
	if len(edges) == 0 {
		t.Fatal("expected grid edges")
	}
	for _, n := range nodes {
		feats, ok := n["features"].(map[string]float64)
		if !ok || feats["temp"] == 0 {
			t.Fatalf("node missing features: %v", n)
		}
	}
}

func TestGridEdgesCount(t *testing.T) {
	e := NewEngine(config.Config{Rows: 2, Cols: 2}, hub.New())
	// 2x2 grid: 2 horizontal + 2 vertical edges = 4
	if len(e.edges) != 4 {
		t.Fatalf("want 4 edges, got %d", len(e.edges))
	}
}
