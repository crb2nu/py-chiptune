//! chiptune_core: High-performance Rust acceleration for py-chiptune
//!
//! Provides 50-200x speedups for per-sample audio loops that are bottlenecks
//! in the pure-Python implementation.

mod waveforms;
mod effects;
mod envelope;
mod mixer;
mod fm;

use pyo3::prelude::*;

/// Rust acceleration module for chiptune audio synthesis
#[pymodule]
fn chiptune_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Waveform generators
    m.add_function(wrap_pyfunction!(waveforms::nes_noise, m)?)?;
    m.add_function(wrap_pyfunction!(waveforms::sid_noise, m)?)?;

    // Effects
    m.add_function(wrap_pyfunction!(effects::tape_delay::tape_delay_process, m)?)?;
    m.add_function(wrap_pyfunction!(effects::chorus::chorus_process, m)?)?;
    m.add_function(wrap_pyfunction!(effects::pitch::pitch_sweep, m)?)?;
    m.add_function(wrap_pyfunction!(effects::lfo::lfo_generate, m)?)?;

    // Envelope
    m.add_function(wrap_pyfunction!(envelope::adsr_generate, m)?)?;

    // Mixer
    m.add_function(wrap_pyfunction!(mixer::mix_channels, m)?)?;
    m.add_function(wrap_pyfunction!(mixer::constant_power_pan, m)?)?;

    // FM synthesis
    m.add_function(wrap_pyfunction!(fm::fm_apply_algorithm, m)?)?;

    Ok(())
}
