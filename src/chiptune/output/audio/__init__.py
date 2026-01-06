"""Audio synthesis and export for chiptune compositions.

Provides NES-authentic waveform generation, ADSR envelopes,
and export to WAV/OGG formats.
"""

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
]
