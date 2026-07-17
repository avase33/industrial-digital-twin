//! Volumetric point-cloud cleaning + geometric feature extraction.
//!
//! Raw LiDAR frames are noisy. This does statistical outlier removal (drop points
//! whose distance to the centroid exceeds mean + k·σ), recomputes the centroid on
//! the surviving points, and reports the spatial spread. Tight numeric loops over
//! coordinate arrays are exactly what Rust does far faster than Python.

use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct PointCloud {
    pub node: String,
    pub coords: Vec<[f64; 3]>,
}

#[derive(Serialize)]
pub struct Frame {
    pub node: String,
    pub centroid: [f64; 3],
    pub kept: usize,
    pub dropped: usize,
    pub spread: f64,
}

fn centroid(points: &[[f64; 3]]) -> [f64; 3] {
    let n = points.len().max(1) as f64;
    let mut c = [0.0; 3];
    for p in points {
        for i in 0..3 {
            c[i] += p[i];
        }
    }
    [c[0] / n, c[1] / n, c[2] / n]
}

fn dist(a: &[f64; 3], b: &[f64; 3]) -> f64 {
    ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2) + (a[2] - b[2]).powi(2)).sqrt()
}

/// Statistical outlier removal + centroid/spread. `k` is the σ multiplier.
pub fn clean(pc: &PointCloud, k: f64) -> Frame {
    if pc.coords.is_empty() {
        return Frame { node: pc.node.clone(), centroid: [0.0; 3], kept: 0, dropped: 0, spread: 0.0 };
    }
    let c = centroid(&pc.coords);
    let dists: Vec<f64> = pc.coords.iter().map(|p| dist(p, &c)).collect();
    let mean = dists.iter().sum::<f64>() / dists.len() as f64;
    let var = dists.iter().map(|d| (d - mean).powi(2)).sum::<f64>() / dists.len() as f64;
    let thresh = mean + k * var.sqrt();

    let kept: Vec<[f64; 3]> = pc
        .coords
        .iter()
        .zip(&dists)
        .filter(|(_, d)| **d <= thresh + 1e-12)
        .map(|(p, _)| *p)
        .collect();
    let dropped = pc.coords.len() - kept.len();

    let c2 = if kept.is_empty() { c } else { centroid(&kept) };
    let spread = if kept.is_empty() {
        0.0
    } else {
        kept.iter().map(|p| dist(p, &c2)).sum::<f64>() / kept.len() as f64
    };

    Frame { node: pc.node.clone(), centroid: c2, kept: kept.len(), dropped, spread }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn removes_a_far_outlier() {
        let pc = PointCloud {
            node: "M01".into(),
            coords: vec![
                [0.0, 0.0, 0.0],
                [0.1, 0.0, 0.0],
                [0.0, 0.1, 0.0],
                [0.05, 0.05, 0.0],
                [50.0, 50.0, 50.0], // outlier
            ],
        };
        let f = clean(&pc, 2.0);
        assert_eq!(f.dropped, 1);
        assert_eq!(f.kept, 4);
        assert!(f.centroid[0] < 1.0 && f.centroid[1] < 1.0);
        assert!(f.spread < 1.0);
    }

    #[test]
    fn empty_cloud_is_safe() {
        let f = clean(&PointCloud { node: "x".into(), coords: vec![] }, 2.0);
        assert_eq!(f.kept, 0);
        assert_eq!(f.dropped, 0);
    }
}
