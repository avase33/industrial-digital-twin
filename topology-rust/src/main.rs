//! idt topology service (axum). POST /clean with raw point clouds, get cleaned
//! centroids + spread back. See proto/protocol.md.

use axum::{
    routing::{get, post},
    Json, Router,
};
use serde::Deserialize;

use idt_topology::cloud::{clean, Frame, PointCloud};

#[derive(Deserialize)]
struct CleanReq {
    points: Vec<PointCloud>,
    #[serde(default = "default_k")]
    k: f64,
}

fn default_k() -> f64 {
    2.0
}

async fn clean_h(Json(req): Json<CleanReq>) -> Json<serde_json::Value> {
    let frames: Vec<Frame> = req.points.iter().map(|pc| clean(pc, req.k)).collect();
    Json(serde_json::json!({ "frames": frames }))
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({ "status": "ok", "service": "topology" }))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/clean", post(clean_h))
        .route("/health", get(health));
    let addr = std::env::var("TOPOLOGY_ADDR").unwrap_or_else(|_| "0.0.0.0:8092".to_string());
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("bind");
    println!("idt topology listening on {addr}");
    axum::serve(listener, app).await.expect("serve");
}
