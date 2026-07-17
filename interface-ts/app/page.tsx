"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { TwinNode, TwinUpdate } from "@/lib/types";

const GATEWAY = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080";
const WS_URL = GATEWAY.replace(/^http/, "ws") + "/ws/twin";

export default function Page() {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [connected, setConnected] = useState(false);
  const [anomalies, setAnomalies] = useState<TwinNode[]>([]);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e17);

    const camera = new THREE.PerspectiveCamera(55, el.clientWidth / el.clientHeight, 0.1, 200);
    camera.position.set(6, 7, 10);
    camera.lookAt(1.5, 0, 1.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(el.clientWidth, el.clientHeight);
    el.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dl = new THREE.DirectionalLight(0xffffff, 0.7);
    dl.position.set(6, 12, 8);
    scene.add(dl);

    const grid = new THREE.GridHelper(14, 14, 0x1d2a3d, 0x131c2b);
    grid.position.set(1.5, -0.4, 1.5);
    scene.add(grid);

    const meshes: Record<string, THREE.Mesh> = {};
    const alarmed = new Set<string>();

    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      alarmed.forEach((id) => {
        const m = meshes[id];
        if (m) m.rotation.y += 0.02;
      });
      renderer.render(scene, camera);
    };
    animate();

    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      let up: TwinUpdate;
      try {
        up = JSON.parse(e.data);
      } catch {
        return;
      }
      up.nodes.forEach((n) => {
        let m = meshes[n.node];
        if (!m) {
          const geo = new THREE.BoxGeometry(0.6, 0.6, 0.6);
          const mat = new THREE.MeshStandardMaterial({ color: 0x26d07c });
          m = new THREE.Mesh(geo, mat);
          m.position.set(n.pos[0], 0, n.pos[1]);
          scene.add(m);
          meshes[n.node] = m;
        }
        const mat = m.material as THREE.MeshStandardMaterial;
        if (n.anomaly) {
          mat.color.set(0xff4d5e);
          mat.emissive = new THREE.Color(0x550000);
          m.scale.setScalar(1.4);
          alarmed.add(n.node);
        } else {
          const h = Math.max(0, Math.min(1, n.health));
          mat.color.setRGB(1 - h, 0.35 + 0.5 * h, 0.4);
          mat.emissive = new THREE.Color(0x000000);
          m.scale.setScalar(1);
          m.rotation.y = 0;
          alarmed.delete(n.node);
        }
      });
      setAnomalies(up.nodes.filter((n) => n.anomaly));
    };

    const onResize = () => {
      if (!el) return;
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      ws.close();
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <main style={{ maxWidth: 1080, margin: "0 auto", padding: 20 }}>
      <header style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
        <strong style={{ fontSize: 18 }}>idt</strong>
        <span style={{ color: "var(--muted)" }}>
          digital twin · Go hub · Rust point-cloud · Python GNN · Three.js
        </span>
        <span style={{ marginLeft: "auto", color: connected ? "var(--ok)" : "var(--muted)" }}>
          {connected ? "● live" : "○ offline"}
        </span>
      </header>

      <div className="card" style={{ marginTop: 14, overflow: "hidden" }}>
        <div ref={mountRef} style={{ width: "100%", height: 460 }} />
      </div>

      <div className="card" style={{ marginTop: 12, padding: 14 }}>
        <div style={{ color: "var(--muted)", marginBottom: 6 }}>
          ACTIVE ANOMALIES ({anomalies.length})
        </div>
        {anomalies.length === 0 && <div style={{ color: "var(--muted)" }}>All machines nominal.</div>}
        {anomalies.map((n) => (
          <div key={n.node} style={{ padding: "8px 0", borderTop: "1px solid var(--border)" }}>
            <strong style={{ color: "var(--alarm)" }}>{n.node}</strong>{" "}
            <span style={{ color: "var(--muted)" }}>health {n.health.toFixed(2)}</span>
            {n.incident && (
              <div style={{ color: "var(--muted)" }}>
                [{n.incident.severity}] {n.incident.kind} → {n.incident.repair.join(" · ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
