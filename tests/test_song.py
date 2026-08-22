"""Song-structure composition tests."""

from typing import Any

import numpy as np
from chiptune.composer.song import SongSection, SongSpec, build_song, standard_structure


def _spec(**kw: Any) -> SongSpec:
    defaults: dict[str, Any] = {"preset_factory": "overworld", "root": "C", "bpm": 120, "seed": 42}
    defaults.update(kw)
    return SongSpec(**defaults)


def test_standard_structures_have_arcs() -> None:
    song = standard_structure("song")
    short = standard_structure("short")
    assert len(song) == 6 and len(short) == 6
    # The hook repeats: identical name+seed pairs appear twice.
    names = [(s.name, s.seed) for s in song]
    assert names.count(("chorus", 3)) == 2


def test_build_song_renders_structured_audio() -> None:
    song = build_song(_spec(sections=standard_structure("short")))
    assert song.dtype == np.float32 and song.ndim == 2 and song.shape[1] == 2
    assert len(song) > 30 * 44100  # structured render is a piece, not a loop
    assert float(np.max(np.abs(song))) <= 0.95  # mastered headroom


def test_build_song_is_deterministic() -> None:
    # Byte-exact determinism holds for pitched channels; the Rust NES noise
    # LFSR carries state across calls (no seed parameter yet), so drum
    # sections are excluded here. Musical material (notes/patterns) is
    # deterministic either way.
    quiet = [s for s in standard_structure("short") if "drums" not in s.layers]
    a = build_song(_spec(sections=quiet))
    b = build_song(_spec(sections=quiet))
    assert len(a) == len(b) and np.allclose(a, b)
    full_a = build_song(_spec(sections=standard_structure("short")))
    full_b = build_song(_spec(sections=standard_structure("short")))
    assert len(full_a) == len(full_b)  # same notes, noise phase may differ


def test_same_seed_sections_repeat_material() -> None:
    hook = SongSection(name="hook", bars=2, layers=["melody"], seed=9)
    other = SongSection(name="other", bars=2, layers=["melody"], seed=10)
    # Rendered standalone (no crossfade), same seed => identical material;
    # a different seed => different material.
    a = build_song(_spec(sections=[hook]))
    b = build_song(_spec(sections=[hook.model_copy()]))
    c = build_song(_spec(sections=[other]))
    assert np.allclose(a, b)
    assert len(a) != len(c) or not np.allclose(a, c)


def test_unknown_preset_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_song(_spec(preset_factory="djent"))
