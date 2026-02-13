//! NES hardware pitch sweep emulation
//!
//! Per-sample bit-shift sweep with configurable rate and direction.
//! Expected speedup: 50-100x.

use numpy::PyArray1;
use pyo3::prelude::*;

/// Generate NES-style pitch sweep frequency curve
///
/// Returns an array of per-sample frequencies.
/// - direction: "up" or "down"
/// - rate: 1-7 (sweep speed, lower = faster)
/// - shift: 1-7 (bit shift amount per step, higher = smaller change)
/// - start_delay: seconds before sweep starts
#[pyfunction]
#[pyo3(signature = (
    base_frequency, num_samples, sample_rate,
    direction = "up", rate = 2, shift = 3, start_delay = 0.0
))]
pub fn pitch_sweep<'py>(
    py: Python<'py>,
    base_frequency: f64,
    num_samples: usize,
    sample_rate: f64,
    direction: &str,
    rate: u32,
    shift: u32,
    start_delay: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let sweep_rate_hz = 120.0 / (rate.max(1) as f64 + 1.0);
    let samples_per_sweep = (sample_rate / sweep_rate_hz) as usize;
    let delay_samples = (start_delay * sample_rate) as usize;
    let is_up = direction == "up";

    let mut current_period = if base_frequency > 0.0 {
        sample_rate / base_frequency
    } else {
        sample_rate / 440.0
    };

    let mut frequencies = vec![0.0f64; num_samples];

    for i in 0..num_samples {
        if i < delay_samples {
            frequencies[i] = base_frequency;
        } else {
            frequencies[i] = if current_period > 0.0 {
                sample_rate / current_period
            } else {
                0.0
            };

            let active_i = i - delay_samples;
            if samples_per_sweep > 0 && active_i % samples_per_sweep == 0 && active_i > 0 {
                let delta = (current_period as u64) >> shift.min(7);

                if is_up {
                    current_period = (current_period - delta as f64).max(8.0);
                } else {
                    current_period = (current_period + delta as f64).min(0x7FF as f64);
                }
            }
        }
    }

    Ok(PyArray1::from_vec_bound(py, frequencies))
}
