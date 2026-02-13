//! Audio mixing with constant-power panning

use numpy::PyArray1;
use pyo3::prelude::*;
use std::f64::consts::PI;

/// Mix multiple mono channels into a stereo output
///
/// channels: list of (samples, volume, pan) tuples
/// pan: -1.0 (left) to 1.0 (right), 0.0 = center
#[pyfunction]
pub fn mix_channels<'py>(
    py: Python<'py>,
    channels: Vec<(Vec<f32>, f32, f32)>,
    num_samples: usize,
) -> PyResult<(Bound<'py, PyArray1<f32>>, Bound<'py, PyArray1<f32>>)> {
    let mut left = vec![0.0f64; num_samples];
    let mut right = vec![0.0f64; num_samples];

    for (samples, volume, pan) in &channels {
        let vol = *volume as f64;
        // Constant-power panning
        let angle = (*pan as f64 + 1.0) * PI / 4.0; // 0 to PI/2
        let left_gain = angle.cos() * vol;
        let right_gain = angle.sin() * vol;

        let len = samples.len().min(num_samples);
        for i in 0..len {
            let s = samples[i] as f64;
            left[i] += s * left_gain;
            right[i] += s * right_gain;
        }
    }

    // Clamp to [-1.0, 1.0]
    let left_f32: Vec<f32> = left.iter().map(|&v| v.clamp(-1.0, 1.0) as f32).collect();
    let right_f32: Vec<f32> = right.iter().map(|&v| v.clamp(-1.0, 1.0) as f32).collect();

    Ok((
        PyArray1::from_vec_bound(py, left_f32),
        PyArray1::from_vec_bound(py, right_f32),
    ))
}

/// Apply constant-power panning to a mono signal
///
/// Returns (left, right) stereo pair.
#[pyfunction]
pub fn constant_power_pan<'py>(
    py: Python<'py>,
    samples: Vec<f32>,
    pan: f32,
) -> PyResult<(Bound<'py, PyArray1<f32>>, Bound<'py, PyArray1<f32>>)> {
    let angle = (pan as f64 + 1.0) * PI / 4.0;
    let left_gain = angle.cos() as f32;
    let right_gain = angle.sin() as f32;

    let left: Vec<f32> = samples.iter().map(|&s| s * left_gain).collect();
    let right: Vec<f32> = samples.iter().map(|&s| s * right_gain).collect();

    Ok((
        PyArray1::from_vec_bound(py, left),
        PyArray1::from_vec_bound(py, right),
    ))
}
