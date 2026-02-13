//! Noise waveform generators (NES LFSR, SID 23-bit LFSR)
//!
//! These are the biggest single bottleneck in py-chiptune:
//! Python for-loops over every sample with bit manipulation.
//! Expected speedup: 50-200x.

use numpy::PyArray1;
use pyo3::prelude::*;

/// NES-style 15-bit LFSR noise generator
///
/// Period table maps 0-15 to CPU clock cycles per LFSR shift.
/// feedback_bit: 1 for "long" mode (32767 steps), 6 for "short" mode (93 steps).
#[pyfunction]
#[pyo3(signature = (period, num_samples, amplitude, sample_rate, mode = "long"))]
pub fn nes_noise<'py>(
    py: Python<'py>,
    period: usize,
    num_samples: usize,
    amplitude: f32,
    sample_rate: f64,
    mode: &str,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    const NES_CPU_RATE: f64 = 1_789_773.0;

    const PERIOD_TABLE: [u32; 16] = [
        4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068,
    ];

    let period = period.min(15);
    let feedback_bit: u32 = if mode == "short" { 6 } else { 1 };

    let period_cycles = PERIOD_TABLE[period] as f64;
    let shifts_per_second = NES_CPU_RATE / period_cycles;
    let samples_per_shift = sample_rate / shifts_per_second;

    let mut lfsr: u32 = 1;
    let mut shift_counter: f64 = 0.0;

    let mut samples = vec![0.0f32; num_samples];

    for i in 0..num_samples {
        samples[i] = if (lfsr & 1) != 0 { amplitude } else { -amplitude };

        shift_counter += 1.0;
        while shift_counter >= samples_per_shift {
            shift_counter -= samples_per_shift;
            let feedback = (lfsr & 1) ^ ((lfsr >> feedback_bit) & 1);
            lfsr = (lfsr >> 1) | (feedback << 14);
        }
    }

    Ok(PyArray1::from_vec_bound(py, samples))
}

/// SID-style 23-bit LFSR noise generator (Commodore 64)
///
/// Complex bit-extraction pattern for authentic SID noise character.
#[pyfunction]
#[pyo3(signature = (frequency, num_samples, amplitude, sample_rate))]
pub fn sid_noise<'py>(
    py: Python<'py>,
    frequency: f64,
    num_samples: usize,
    amplitude: f32,
    sample_rate: f64,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    let samples_per_shift = if frequency > 0.0 {
        sample_rate / frequency
    } else {
        sample_rate // 1 Hz fallback
    };

    let mut lfsr: u32 = 0x7FFFF8;
    let mut shift_counter: f64 = 0.0;

    let mut samples = vec![0.0f32; num_samples];

    for i in 0..num_samples {
        // Extract output bits from specific LFSR positions (SID pattern)
        let output_bits: u32 = ((lfsr >> 20) & 1)
            | (((lfsr >> 18) & 1) << 1)
            | (((lfsr >> 14) & 1) << 2)
            | (((lfsr >> 11) & 1) << 3)
            | (((lfsr >> 9) & 1) << 4)
            | (((lfsr >> 5) & 1) << 5)
            | (((lfsr >> 2) & 1) << 6)
            | ((lfsr & 1) << 7);

        samples[i] = (output_bits as f32 / 128.0 - 0.5) * 2.0 * amplitude;

        shift_counter += 1.0;
        while shift_counter >= samples_per_shift {
            shift_counter -= samples_per_shift;
            // Feedback from bits 17 and 22
            let feedback = ((lfsr >> 17) ^ (lfsr >> 22)) & 1;
            lfsr = ((lfsr << 1) | feedback) & 0x7FFFFF;
        }
    }

    Ok(PyArray1::from_vec_bound(py, samples))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_nes_noise_long_mode() {
        Python::with_gil(|py| {
            let result = nes_noise(py, 4, 44100, 1.0, 44100.0, "long").unwrap();
            let arr = result.to_vec().unwrap();
            assert_eq!(arr.len(), 44100);
            // All values should be +/-1.0
            assert!(arr.iter().all(|&v| v == 1.0 || v == -1.0));
        });
    }

    #[test]
    fn test_nes_noise_short_mode() {
        Python::with_gil(|py| {
            let result = nes_noise(py, 4, 1000, 0.5, 44100.0, "short").unwrap();
            let arr = result.to_vec().unwrap();
            assert_eq!(arr.len(), 1000);
            assert!(arr.iter().all(|&v| v == 0.5 || v == -0.5));
        });
    }

    #[test]
    fn test_sid_noise() {
        Python::with_gil(|py| {
            let result = sid_noise(py, 440.0, 44100, 1.0, 44100.0).unwrap();
            let arr = result.to_vec().unwrap();
            assert_eq!(arr.len(), 44100);
            // Values should be in [-1.0, 1.0]
            assert!(arr.iter().all(|&v| v >= -1.0 && v <= 1.0));
        });
    }
}
