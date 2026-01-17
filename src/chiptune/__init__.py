"""py-chiptune: Retro game music generation library.

Generate 8-bit/16-bit style music and sound effects with a semantic API
that agents can use to programmatically compose music. Supports both
MIDI export and direct audio synthesis with authentic NES waveforms.
"""

from __future__ import annotations

import importlib
from typing import Any

from chiptune._version import __version__

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "MusicAgent": ("chiptune.composer.agent_api", "MusicAgent"),
    "ChiptuneComposer": ("chiptune.composer.composer", "ChiptuneComposer"),
    "AudioExporter": ("chiptune.output.audio", "AudioExporter"),
    "AudioPlayer": ("chiptune.output.audio", "AudioPlayer"),
    "Jingle": ("chiptune.patterns.jingles", "Jingle"),
    "SFXGenerator": ("chiptune.sfx.effects", "SFXGenerator"),
    "Scale": ("chiptune.theory.scales", "Scale"),
    "Chord": ("chiptune.theory.chords", "Chord"),
    "ChordProgression": ("chiptune.theory.chords", "ChordProgression"),
    "Key": ("chiptune.theory.keys", "Key"),
    "GenrePresets": ("chiptune.presets", "GenrePresets"),
    "EffectPresets": ("chiptune.presets", "EffectPresets"),
    "ChipPresets": ("chiptune.presets", "ChipPresets"),
    "QuickCompose": ("chiptune.presets", "QuickCompose"),
}

__all__ = [
    "__version__",
    "ChiptuneComposer",
    "MusicAgent",
    "Jingle",
    "SFXGenerator",
    "Scale",
    "Chord",
    "ChordProgression",
    "Key",
    "AudioExporter",
    "AudioPlayer",
    # Presets
    "GenrePresets",
    "EffectPresets",
    "ChipPresets",
    "QuickCompose",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))
