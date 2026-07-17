.PHONY: up down test test-rust test-python test-go build-web demo verify

up:
	docker compose up --build

down:
	docker compose down

test: test-rust test-python test-go

test-rust:
	cd topology-rust && cargo test

test-python:
	cd intelligence-python && pip install -e ".[dev]" && pytest -q

test-go:
	cd hub-go && go test ./...

build-web:
	cd interface-ts && npm install && npm run build

# Offline: fit the GNN, inject faults, detect them (no services needed).
demo:
	cd intelligence-python && python -m idt_intelligence.cli demo

verify:
	python scripts/verify.py
