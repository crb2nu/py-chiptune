//! ADSR envelope generation

use numpy::PyArray1;
use pyo3::prelude::*;

/// Generate ADSR envelope
///
/// Returns per-sample amplitude envelope values (0.0-1.0).
#[pyfunction]
#[pyo3(signature = (
    num_samples, sample_rate,
    attack = 0.01, decay = 0.1, sustain = 0.7, release = 0.1,
    sustain_time = 0.0
))]
pub fn adsr_generate<'py>(
    py: Python<'py>,
    num_samples: usize,
    sample_rate: f64,
    attack: f64,
    decay: f64,
    sustain: f64,
    release: f64,
    sustain_time: f64,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let attack_samples = (attack * sample_rate) as usize;
    let decay_samples = (decay * sample_rate) as usize;
    let sustain_samples = (sustain_time * sample_rate) as usize;
    let release_samples = (release * sample_rate) as usize;

    let mut envelope = vec![0.0f32; num_samples];

    for i in 0..num_samples {
        let value = if i < attack_samples {
            // Attack: ramp up from 0 to 1
            if attack_samples > 0 {
                i as f64 / attack_samples as f64
            } else {
                1.0
            }
        } else if i < attack_samples + decay_samples {
            // Decay: ramp down from 1 to sustain level
            let decay_pos = (i - attack_samples) as f64 / decay_samples.max(1) as f64;
            1.0 - (1.0 - sustain) * decay_pos
        } else if sustain_samples > 0 && i < attack_samples + decay_samples + sustain_samples {
            // Sustain
            sustain
        } else {
            // Release: ramp down from sustain to 0
            let release_start = if sustain_samples > 0 {
                attack_samples + decay_samples + sustain_samples
            } else {
                attack_samples + decay_samples
            };

            if i >= release_start && release_samples > 0 {
                let release_pos = (i - release_start) as f64 / release_samples as f64;
                (sustain * (1.0 - release_pos)).max(0.0)
            } else if sustain_time == 0.0 && i >= attack_samples + decay_samples {
                // No explicit sustain time — hold at sustain level
                sustain
            } else {
                0.0
            }
        };

        envelope[i] = value as f32;
    }

    Ok(PyArray1::from_vec_bound(py, envelope))
}
