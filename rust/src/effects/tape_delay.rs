//! Tape delay effect (Roland Space Echo, Echoplex style)
//!
//! Per-sample delay buffer with feedback, wow/flutter modulation,
//! soft saturation, and lowpass filter. Expected speedup: 50-200x.

use numpy::PyArray1;
use pyo3::prelude::*;
use std::f64::consts::PI;

/// Process audio through a tape delay effect
#[pyfunction]
#[pyo3(signature = (
    samples, sample_rate, delay_time = 0.3, feedback = 0.5, mix = 0.5,
    wow_depth = 0.003, flutter_depth = 0.001, saturation = 0.3, highcut = 3500.0
))]
pub fn tape_delay_process<'py>(
    py: Python<'py>,
    samples: Vec<f32>,
    sample_rate: f64,
    delay_time: f64,
    feedback: f64,
    mix: f64,
    wow_depth: f64,
    flutter_depth: f64,
    saturation: f64,
    highcut: f64,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let num_samples = samples.len();
    let delay_samples = (delay_time * sample_rate) as usize;
    let buffer_size = delay_samples + (0.02 * sample_rate) as usize + num_samples;

    let mut delay_buffer = vec![0.0f64; buffer_size];
    let mut wet = vec![0.0f64; num_samples];

    // Pre-compute modulation
    let wow_rate = 0.8;
    let flutter_rate = 9.0;
    let wow_samples = (wow_depth * sample_rate) as i64;
    let flutter_samples = (flutter_depth * sample_rate) as i64;

    // Simple 1-pole lowpass for tape highcut
    let rc = 1.0 / (2.0 * PI * highcut);
    let dt = 1.0 / sample_rate;
    let alpha = dt / (rc + dt);
    let mut prev_filtered = 0.0f64;

    for i in 0..num_samples {
        let t = i as f64 / sample_rate;

        // Wow + flutter modulation
        let wow_mod = (2.0 * PI * wow_rate * t).sin()
            + 0.3 * (2.0 * PI * 1.3 * t).sin();
        let flutter_mod = (2.0 * PI * flutter_rate * t).sin();

        let mod_offset = (wow_mod * wow_samples as f64 + flutter_mod * flutter_samples as f64) as i64;
        let read_pos = (i as i64 + delay_samples as i64 + mod_offset).max(0) as usize;

        // Read from delay buffer
        let delayed = if read_pos < delay_buffer.len() {
            delay_buffer[read_pos]
        } else {
            0.0
        };

        // Write to delay buffer: input + feedback
        let write_pos = i + delay_samples;
        if write_pos < delay_buffer.len() {
            delay_buffer[write_pos] += samples[i] as f64 + delayed * feedback;
        }

        // Soft saturation (tanh)
        let saturated = if saturation > 0.0 {
            let drive = 1.0 + saturation * 3.0;
            (delayed * drive).tanh() / drive.tanh()
        } else {
            delayed
        };

        // 1-pole lowpass filter
        let filtered = prev_filtered + alpha * (saturated - prev_filtered);
        prev_filtered = filtered;

        wet[i] = filtered;
    }

    // Mix dry and wet
    let result: Vec<f32> = samples
        .iter()
        .zip(wet.iter())
        .map(|(&dry, &w)| (dry as f64 * (1.0 - mix) + w * mix) as f32)
        .collect();

    Ok(PyArray1::from_vec_bound(py, result))
}
