"""High-level composition API for chiptune music."""

from chiptune.composer.agent_api import MusicAgent
from chiptune.composer.composer import BassStyle, ChiptuneComposer, DrumStyle, Track

__all__ = ["ChiptuneComposer", "Track", "MusicAgent", "BassStyle", "DrumStyle"]
