// Package engine simulates the factory sensor grid, scores it with the Python GNN,
// and streams per-node health to the 3D twin. (In production the readings would
// arrive over MQTT and point clouds would be cleaned by the Rust topology service.)
package engine

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"time"

	"github.com/avase33/industrial-digital-twin/hub/internal/config"
	"github.com/avase33/industrial-digital-twin/hub/internal/hub"
)

type nodeMeta struct {
	id  string
	pos [3]float64
}

type Engine struct {
	cfg   config.Config
	hub   *hub.Hub
	http  *http.Client
	rng   *rand.Rand
	nodes []nodeMeta
	edges [][2]string
}

func NewEngine(cfg config.Config, h *hub.Hub) *Engine {
	var nodes []nodeMeta
	var edges [][2]string
	for r := 0; r < cfg.Rows; r++ {
		for c := 0; c < cfg.Cols; c++ {
			id := fmt.Sprintf("M%02d", r*cfg.Cols+c)
			nodes = append(nodes, nodeMeta{id, [3]float64{float64(c), float64(r), 0}})
			if c+1 < cfg.Cols {
				edges = append(edges, [2]string{id, fmt.Sprintf("M%02d", r*cfg.Cols+c+1)})
			}
			if r+1 < cfg.Rows {
				edges = append(edges, [2]string{id, fmt.Sprintf("M%02d", (r+1)*cfg.Cols+c)})
			}
		}
	}
	return &Engine{cfg, h, &http.Client{Timeout: 3 * time.Second}, rand.New(rand.NewSource(7)), nodes, edges}
}

// GenGraph produces one sensor snapshot of the whole floor, occasionally with a
// faulted machine (temperature + vibration spike).
func (e *Engine) GenGraph() map[string]any {
	faultIdx := -1
	if e.rng.Float64() < 0.4 && len(e.nodes) > 0 {
		faultIdx = e.rng.Intn(len(e.nodes))
	}
	gnodes := make([]map[string]any, 0, len(e.nodes))
	for i, nm := range e.nodes {
		temp := 70 + e.rng.NormFloat64()*1.5
		vib := 0.8 + e.rng.NormFloat64()*0.1
		rot := 1500 + e.rng.NormFloat64()*25
		if i == faultIdx {
			temp += 35
			vib += 4
			rot -= 300
		}
		gnodes = append(gnodes, map[string]any{
			"node":     nm.id,
			"features": map[string]float64{"temp": temp, "vibration": vib, "rotation": rot},
			"pos":      nm.pos,
		})
	}
	edges := make([][]string, 0, len(e.edges))
	for _, ed := range e.edges {
		edges = append(edges, []string{ed[0], ed[1]})
	}
	return map[string]any{"nodes": gnodes, "edges": edges}
}

type scoreNode struct {
	Node       string         `json:"node"`
	Health     float64        `json:"health"`
	Anomaly    bool           `json:"anomaly"`
	Incident   map[string]any `json:"incident"`
}

func (e *Engine) Run() {
	ticker := time.NewTicker(time.Duration(e.cfg.TickMs) * time.Millisecond)
	defer ticker.Stop()
	for range ticker.C {
		e.step()
	}
}

func (e *Engine) step() {
	g := e.GenGraph()
	var resp struct {
		Nodes []scoreNode `json:"nodes"`
	}
	if err := e.post(e.cfg.IntelURL+"/score", map[string]any{"graph": g}, &resp); err != nil {
		return
	}
	pos := map[string][3]float64{}
	for _, nm := range e.nodes {
		pos[nm.id] = nm.pos
	}
	out := make([]map[string]any, 0, len(resp.Nodes))
	for _, sn := range resp.Nodes {
		out = append(out, map[string]any{
			"node": sn.Node, "health": sn.Health, "anomaly": sn.Anomaly,
			"incident": sn.Incident, "pos": pos[sn.Node],
		})
	}
	e.hub.Broadcast(map[string]any{"ts": float64(time.Now().Unix()), "nodes": out})
}

func (e *Engine) post(url string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	resp, err := e.http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return json.NewDecoder(resp.Body).Decode(out)
}
