"""py-chiptune: Retro game music generation library.

Generate 8-bit/16-bit style MIDI music and sound effects with a semantic API
that agents can use to programmatically compose music.
"""

from chiptune.composer.composer import ChiptuneComposer
from chiptune.composer.agent_api import MusicAgent
from chiptune.patterns.jingles import Jingle
from chiptune.sfx.effects import SFXGenerator
from chiptune.theory.scales import Scale
from chiptune.theory.chords import Chord, ChordProgression
from chiptune.theory.keys import Key

__version__ = "0.1.0"

__all__ = [
    "ChiptuneComposer",
    "MusicAgent",
    "Jingle",
    "SFXGenerator",
    "Scale",
    "Chord",
    "ChordProgression",
    "Key",
]
