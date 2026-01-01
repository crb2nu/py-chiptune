"""Chiptune hardware constraints and channel models."""

from chiptune.chip.channels import (
    Channel,
    ChannelType,
    DutyCycle,
    NESChannels,
    ChannelAllocator,
)
from chiptune.chip.effects import (
    ChipEffect,
    EffectType,
    Vibrato,
    PitchSlide,
    VolumeEnvelope,
    DutyCycleSweep,
)

__all__ = [
    "Channel",
    "ChannelType",
    "DutyCycle",
    "NESChannels",
    "ChannelAllocator",
    "ChipEffect",
    "EffectType",
    "Vibrato",
    "PitchSlide",
    "VolumeEnvelope",
    "DutyCycleSweep",
]
