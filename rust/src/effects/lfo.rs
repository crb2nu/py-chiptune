//! LFO (Low Frequency Oscillator) generation

use numpy::PyArray1;
use pyo3::prelude::*;
use std::f64::consts::PI;

/// Generate LFO waveform
///
/// - shape: "sine", "triangle", "square", "saw"
/// - rate: frequency in Hz
/// - depth: modulation depth (0.0-1.0)
/// - phase: initial phase in radians
#[pyfunction]
#[pyo3(signature = (num_samples, sample_rate, rate = 1.0, depth = 1.0, shape = "sine", phase = 0.0))]
pub fn lfo_generate<'py>(
    py: Python<'py>,
    num_samples: usize,
    sample_rate: f64,
    rate: f64,
    depth: f64,
    shape: &str,
    phase: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let mut output = vec![0.0f64; num_samples];

    for i in 0..num_samples {
        let t = i as f64 / sample_rate;
        let p = 2.0 * PI * rate * t + phase;

        let raw = match shape {
            "sine" => p.sin(),
            "triangle" => {
                let frac = (p / (2.0 * PI)).fract();
                let frac = if frac < 0.0 { frac + 1.0 } else { frac };
                if frac < 0.25 {
                    frac * 4.0
                } else if frac < 0.75 {
                    2.0 - frac * 4.0
                } else {
                    frac * 4.0 - 4.0
                }
            }
            "square" => {
                if p.sin() >= 0.0 { 1.0 } else { -1.0 }
            }
            "saw" => {
                let frac = (p / (2.0 * PI)).fract();
                let frac = if frac < 0.0 { frac + 1.0 } else { frac };
                2.0 * frac - 1.0
            }
            _ => p.sin(), // Default to sine
        };

        output[i] = raw * depth;
    }

    Ok(PyArray1::from_vec_bound(py, output))
}
