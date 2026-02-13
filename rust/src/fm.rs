//! FM synthesis (YM2612 4-operator algorithms)
//!
//! Implements 8 different operator connection algorithms for Sega Genesis FM.
//! Expected speedup: 5-20x (numpy already vectorizes sin, but the operator
//! chaining is sequential).

use numpy::PyArray1;
use pyo3::prelude::*;

/// Apply a YM2612 FM algorithm to generate audio
///
/// - algorithm: 0-7 (operator connection topology)
/// - phases: [op1_phase, op2_phase, op3_phase, op4_phase] - base phase arrays
/// - envelopes: [env1, env2, env3, env4] - per-operator amplitude envelopes
/// - feedback_level: feedback amount for op1 (0-7 in hardware, normalized 0.0-1.0)
/// - mod_index: modulation index (typically 4.0)
#[pyfunction]
#[pyo3(signature = (
    algorithm, phases, envelopes, num_samples,
    feedback_level = 0.0, mod_index = 4.0
))]
pub fn fm_apply_algorithm<'py>(
    py: Python<'py>,
    algorithm: u8,
    phases: Vec<Vec<f64>>,
    envelopes: Vec<Vec<f32>>,
    num_samples: usize,
    feedback_level: f64,
    mod_index: f64,
) -> PyResult<Bound<'py, PyArray1<f32>>> {
    if phases.len() != 4 || envelopes.len() != 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Expected exactly 4 operators (phases and envelopes)",
        ));
    }

    let mut output = vec![0.0f32; num_samples];

    for i in 0..num_samples {
        let p1 = phases[0].get(i).copied().unwrap_or(0.0);
        let p2 = phases[1].get(i).copied().unwrap_or(0.0);
        let p3 = phases[2].get(i).copied().unwrap_or(0.0);
        let p4 = phases[3].get(i).copied().unwrap_or(0.0);

        let e1 = envelopes[0].get(i).copied().unwrap_or(0.0) as f64;
        let e2 = envelopes[1].get(i).copied().unwrap_or(0.0) as f64;
        let e3 = envelopes[2].get(i).copied().unwrap_or(0.0) as f64;
        let e4 = envelopes[3].get(i).copied().unwrap_or(0.0) as f64;

        let fb = feedback_level;

        let result = match algorithm {
            0 => {
                // ALG0: 1→2→3→4 (serial)
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2 + mod_index * op1).sin() * e2;
                let op3 = (p3 + mod_index * op2).sin() * e3;
                let op4 = (p4 + mod_index * op3).sin() * e4;
                op4
            }
            1 => {
                // ALG1: (1+2)→3→4
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2).sin() * e2;
                let op3 = (p3 + mod_index * (op1 + op2) / 2.0).sin() * e3;
                let op4 = (p4 + mod_index * op3).sin() * e4;
                op4
            }
            2 => {
                // ALG2: 1→3, 2→3→4
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2).sin() * e2;
                let op3 = (p3 + mod_index * (op1 + op2) / 2.0).sin() * e3;
                let op4 = (p4 + mod_index * op3).sin() * e4;
                op4
            }
            3 => {
                // ALG3: 1→2, 3→4, out = 2+4
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2 + mod_index * op1).sin() * e2;
                let op3 = (p3).sin() * e3;
                let op4 = (p4 + mod_index * op3).sin() * e4;
                (op2 + op4) / 2.0
            }
            4 => {
                // ALG4: 1→2, 3→4 (balanced, 2 carriers)
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2 + mod_index * op1).sin() * e2;
                let op3 = (p3).sin() * e3;
                let op4 = (p4 + mod_index * op3).sin() * e4;
                (op2 + op4) / 2.0
            }
            5 => {
                // ALG5: 1→(2+3+4), 3 carriers
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2 + mod_index * op1).sin() * e2;
                let op3 = (p3 + mod_index * op1).sin() * e3;
                let op4 = (p4 + mod_index * op1).sin() * e4;
                (op2 + op3 + op4) / 3.0
            }
            6 => {
                // ALG6: 1→2, out = 2+3+4 (3 carriers)
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2 + mod_index * op1).sin() * e2;
                let op3 = (p3).sin() * e3;
                let op4 = (p4).sin() * e4;
                (op2 + op3 + op4) / 3.0
            }
            7 | _ => {
                // ALG7: All parallel (4 carriers, organ-like)
                let op1 = (p1 + fb * (p1).sin()).sin() * e1;
                let op2 = (p2).sin() * e2;
                let op3 = (p3).sin() * e3;
                let op4 = (p4).sin() * e4;
                (op1 + op2 + op3 + op4) / 4.0
            }
        };

        output[i] = result as f32;
    }

    Ok(PyArray1::from_vec_bound(py, output))
}
