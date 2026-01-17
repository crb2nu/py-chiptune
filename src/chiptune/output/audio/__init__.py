"""Audio synthesis and export for chiptune compositions.

Provides NES-authentic waveform generation, ADSR envelopes,
audio effects, and export to WAV/OGG formats.
"""

from __future__ import annotations

import importlib
from typing import Any

from chiptune.output.audio.envelope import ADSREnvelope
from chiptune.output.audio.exporter import AudioExporter
from chiptune.output.audio.mixer import ChannelMixer
from chiptune.output.audio.playback import AudioPlayer
from chiptune.output.audio.waveforms import (
    NoiseGenerator,
    PulseWaveGenerator,
    TriangleWaveGenerator,
    midi_to_frequency,
)

__all__ = [
    "AudioExporter",
    "AudioPlayer",
    "ADSREnvelope",
    "ChannelMixer",
    "PulseWaveGenerator",
    "TriangleWaveGenerator",
    "NoiseGenerator",
    "midi_to_frequency",
    "effects",
]


def __getattr__(name: str) -> Any:
    if name == "effects":
        module = importlib.import_module("chiptune.output.audio.effects")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
