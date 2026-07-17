// Command idt-hub is the high-density sensor ingestion hub: it streams the factory
// floor through the Python GNN and broadcasts per-node health to 3D twin viewers.
package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gorilla/websocket"

	"github.com/avase33/industrial-digital-twin/hub/internal/config"
	"github.com/avase33/industrial-digital-twin/hub/internal/engine"
	"github.com/avase33/industrial-digital-twin/hub/internal/hub"
)

type App struct {
	cfg config.Config
	hub *hub.Hub
}

var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}

func (a *App) handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	client := a.hub.Add()
	defer func() {
		a.hub.Remove(client)
		conn.Close()
	}()
	go func() {
		for {
			if _, _, err := conn.ReadMessage(); err != nil {
				a.hub.Remove(client)
				return
			}
		}
	}()
	for msg := range client.Send {
		if err := conn.WriteMessage(websocket.TextMessage, msg); err != nil {
			return
		}
	}
}

func (a *App) handleIngest(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Readings []map[string]any `json:"readings"`
	}
	_ = json.NewDecoder(r.Body).Decode(&body)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]any{"accepted": len(body.Readings)})
}

func (a *App) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"status": "ok", "service": "hub", "clients": a.hub.Count(), "intel": a.cfg.IntelURL,
	})
}

func main() {
	cfg := config.Load()
	h := hub.New()
	app := &App{cfg: cfg, hub: h}

	go engine.NewEngine(cfg, h).Run()

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", app.handleHealth)
	mux.HandleFunc("POST /ingest", app.handleIngest)
	mux.HandleFunc("GET /ws/twin", app.handleWS)

	log.Printf("idt hub (http %s) → intel=%s grid=%dx%d", cfg.Addr, cfg.IntelURL, cfg.Rows, cfg.Cols)
	if err := http.ListenAndServe(cfg.Addr, mux); err != nil {
		log.Fatal(err)
	}
}
