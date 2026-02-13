//! Chorus effect with multi-voice delay modulation
//!
//! Creates multiple delayed voices with LFO-modulated delay times.
//! Expected speedup: 30-100x.

use numpy::PyArray1;
use pyo3::prelude::*;
use std::f64::consts::PI;

/// Process audio through a chorus effect
#[pyfunction]
#[pyo3(signature = (samples, sample_rate, voices = 3, depth_ms = 3.0, rate = 0.8, mix = 0.5))]
pub fn chorus_process<'py>(
    py: Python<'py>,
    samples: Vec<f32>,
    sample_rate: f64,
    voices: usize,
    depth_ms: f64,
    rate: f64,
    mix: f64,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let num_samples = samples.len();
    let base_delay_samples = (0.020 * sample_rate) as usize; // 20ms base delay
    let depth_samples = (depth_ms / 1000.0 * sample_rate) as f64;

    let mut wet = vec![0.0f64; num_samples];

    for voice in 0..voices {
        let voice_rate = rate * (1.0 + voice as f64 * 0.1);
        let phase_offset = voice as f64 / voices as f64;
        let voice_level = 1.0 - (voice as f64 - (voices as f64 - 1.0) / 2.0).abs()
            / voices as f64 * 0.15;

        for i in 0..num_samples {
            let t = i as f64 / sample_rate;
            let lfo = (2.0 * PI * voice_rate * t + phase_offset * 2.0 * PI).sin();
            let delay_mod = (lfo * depth_samples) as i64;
            let read_pos = i as i64 - base_delay_samples as i64 - delay_mod;

            if read_pos >= 0 && (read_pos as usize) < num_samples {
                wet[i] += samples[read_pos as usize] as f64 * voice_level;
            }
        }
    }

    // Normalize by voice count
    let norm = 1.0 / voices as f64;
    for v in wet.iter_mut() {
        *v *= norm;
    }

    // Mix dry and wet
    let result: Vec<f32> = samples
        .iter()
        .zip(wet.iter())
        .map(|(&dry, &w)| (dry as f64 * (1.0 - mix) + w * mix) as f32)
        .collect();

    Ok(PyArray1::from_vec_bound(py, result))
}
