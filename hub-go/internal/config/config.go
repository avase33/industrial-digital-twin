// Package config loads hub settings from the environment.
package config

import (
	"os"
	"strconv"
)

type Config struct {
	Addr     string
	IntelURL string // Python GNN service
	TickMs   int
	Rows     int
	Cols     int
}

func Load() Config {
	return Config{
		Addr:     env("IDT_ADDR", ":8080"),
		IntelURL: env("IDT_INTEL_URL", "http://localhost:8000"),
		TickMs:   envInt("IDT_TICK_MS", 1000),
		Rows:     envInt("IDT_ROWS", 4),
		Cols:     envInt("IDT_COLS", 4),
	}
}

func env(k, def string) string {
	if v, ok := os.LookupEnv(k); ok && v != "" {
		return v
	}
	return def
}

func envInt(k string, def int) int {
	if v, ok := os.LookupEnv(k); ok {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
