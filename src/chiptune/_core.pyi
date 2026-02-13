"""Type stubs for chiptune_core Rust extension module."""

import numpy as np
import numpy.typing as npt

def nes_noise(
    period: int,
    num_samples: int,
    amplitude: float,
    sample_rate: float,
    mode: str = "long",
) -> npt.NDArray[np.float32]: ...

def sid_noise(
    frequency: float,
    num_samples: int,
    amplitude: float,
    sample_rate: float,
) -> npt.NDArray[np.float32]: ...

def tape_delay_process(
    samples: npt.NDArray[np.float32],
    sample_rate: float,
    delay_time: float = 0.3,
    feedback: float = 0.5,
    mix: float = 0.5,
    wow_depth: float = 0.003,
    flutter_depth: float = 0.001,
    saturation: float = 0.3,
    highcut: float = 3500.0,
) -> npt.NDArray[np.float32]: ...

def chorus_process(
    samples: npt.NDArray[np.float32],
    sample_rate: float,
    voices: int = 3,
    depth_ms: float = 3.0,
    rate: float = 0.8,
    mix: float = 0.5,
) -> npt.NDArray[np.float32]: ...

def pitch_sweep(
    base_frequency: float,
    num_samples: int,
    sample_rate: float,
    direction: str = "up",
    rate: int = 2,
    shift: int = 3,
    start_delay: float = 0.0,
) -> npt.NDArray[np.float64]: ...

def lfo_generate(
    num_samples: int,
    sample_rate: float,
    rate: float = 1.0,
    depth: float = 1.0,
    shape: str = "sine",
    phase: float = 0.0,
) -> npt.NDArray[np.float64]: ...

def adsr_generate(
    num_samples: int,
    sample_rate: float,
    attack: float = 0.01,
    decay: float = 0.1,
    sustain: float = 0.7,
    release: float = 0.1,
    sustain_time: float = 0.0,
) -> npt.NDArray[np.float32]: ...

def mix_channels(
    channels: list[tuple[npt.NDArray[np.float32], float, float]],
    num_samples: int,
) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]: ...

def constant_power_pan(
    samples: npt.NDArray[np.float32],
    pan: float,
) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]: ...

def fm_apply_algorithm(
    algorithm: int,
    phases: list[npt.NDArray[np.float64]],
    envelopes: list[npt.NDArray[np.float32]],
    num_samples: int,
    feedback_level: float = 0.0,
    mod_index: float = 4.0,
) -> npt.NDArray[np.float32]: ...
