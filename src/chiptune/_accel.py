"""Rust acceleration dispatcher for chiptune.

Tries to import the Rust chiptune_core module. If unavailable,
all functions fall back to None and callers use the Python implementation.
"""

import os

_DISABLE_RUST = os.getenv("CHIPTUNE_DISABLE_RUST", "").lower() in {"1", "true", "yes"}

try:
    if _DISABLE_RUST:
        raise ImportError("Rust acceleration disabled by CHIPTUNE_DISABLE_RUST")
    from chiptune.chiptune_core import (
        nes_noise as _rust_nes_noise,
        sid_noise as _rust_sid_noise,
        tape_delay_process as _rust_tape_delay,
        chorus_process as _rust_chorus,
        pitch_sweep as _rust_pitch_sweep,
        lfo_generate as _rust_lfo,
        adsr_generate as _rust_adsr,
        mix_channels as _rust_mix_channels,
        constant_power_pan as _rust_constant_power_pan,
        fm_apply_algorithm as _rust_fm_algorithm,
    )
    RUST_AVAILABLE = True
except ImportError:
    try:
        if _DISABLE_RUST:
            raise ImportError("Rust acceleration disabled by CHIPTUNE_DISABLE_RUST")
        from chiptune_core import (
            nes_noise as _rust_nes_noise,
            sid_noise as _rust_sid_noise,
            tape_delay_process as _rust_tape_delay,
            chorus_process as _rust_chorus,
            pitch_sweep as _rust_pitch_sweep,
            lfo_generate as _rust_lfo,
            adsr_generate as _rust_adsr,
            mix_channels as _rust_mix_channels,
            constant_power_pan as _rust_constant_power_pan,
            fm_apply_algorithm as _rust_fm_algorithm,
        )
        RUST_AVAILABLE = True
    except ImportError:
        RUST_AVAILABLE = False
        _rust_nes_noise = None
        _rust_sid_noise = None
        _rust_tape_delay = None
        _rust_chorus = None
        _rust_pitch_sweep = None
        _rust_lfo = None
        _rust_adsr = None
        _rust_mix_channels = None
        _rust_constant_power_pan = None
        _rust_fm_algorithm = None

__all__ = [
    "RUST_AVAILABLE",
    "_rust_nes_noise",
    "_rust_sid_noise",
    "_rust_tape_delay",
    "_rust_chorus",
    "_rust_pitch_sweep",
    "_rust_lfo",
    "_rust_adsr",
    "_rust_mix_channels",
    "_rust_constant_power_pan",
    "_rust_fm_algorithm",
]
