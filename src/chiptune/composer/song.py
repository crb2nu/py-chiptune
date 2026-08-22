"""Song-structure composition: sections with layering arcs, stitched and mastered.

The single-loop generate path renders one texture for N bars — musically flat.
A Song renders each section as its own composer pass (same key/tempo, its own
seed and layer stack), stitches sections with short equal-power crossfades,
and normalizes the result. Repeating a section name+seed repeats its material,
which is what makes a chorus a chorus.

Typical arc:
    intro   4 bars   melody                      sparse, quiet
    verse   8 bars   melody+bass                 groove enters
    chorus  8 bars   melody+counter+arp+drums    full texture (the hook)
    verse2  8 bars   melody+bass+drums           variation (new seed)
    chorus  8 bars   same seed as chorus         the hook returns
    outro   4 bars   melody+bass                 fading
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from chiptune.composer.composer import ChiptuneComposer
from chiptune.output.audio.exporter import AudioExporter

CROSSFADE_SECONDS = 0.03
TARGET_PEAK = 0.92

KNOWN_LAYERS = ("melody", "counter", "bass", "arp", "drums")


class SongSection(BaseModel):
    """One section of a song. Sections sharing name+seed repeat their material."""

    name: str = "section"
    bars: int = Field(default=8, ge=1, le=64)
    layers: list[str] = Field(default_factory=lambda: ["melody", "bass", "drums"])
    contour: str = "arch"  # arch, ascending, descending, wave
    bass_style: str = "root"  # root, octave, walking, arpeggiated
    drum_style: str = "basic"  # basic, driving, sparse
    arp_pattern: str = "up"
    counter_motion: str = "contrary"
    # Seed offset relative to the song seed; equal offsets -> identical material.
    seed: int = 0


class SongSpec(BaseModel):
    """A full song: shared key/tempo, per-section texture."""

    preset_factory: str = "overworld"  # GenrePresets method key (cli GENRE_PRESET_METHODS)
    root: str | None = None
    bpm: int | None = None
    sections: list[SongSection] = Field(default_factory=list)
    seed: int = 0


def standard_structure(kind: str = "song") -> list[SongSection]:
    """Built-in structures so callers don't have to hand-author sections."""
    if kind == "short":  # ~30-40s at 120bpm — film-score sized
        return [
            SongSection(name="intro", bars=2, layers=["melody"], contour="ascending", seed=1),
            SongSection(name="a", bars=4, layers=["melody", "bass"], seed=2),
            SongSection(
                name="b",
                bars=4,
                layers=["melody", "counter", "arp", "drums"],
                drum_style="driving",
                bass_style="octave",
                seed=3,
            ),
            SongSection(
                name="a2",
                bars=4,
                layers=["melody", "bass", "drums"],
                drum_style="sparse",
                seed=4,
            ),
            SongSection(
                name="b",
                bars=4,
                layers=["melody", "counter", "arp", "drums"],
                drum_style="driving",
                bass_style="octave",
                seed=3,
            ),
            SongSection(
                name="outro",
                bars=2,
                layers=["melody", "bass"],
                contour="descending",
                seed=5,
            ),
        ]
    # full song, ~1.5-2 min at 120bpm
    return [
        SongSection(name="intro", bars=4, layers=["melody"], contour="ascending", seed=1),
        SongSection(name="verse", bars=8, layers=["melody", "bass"], seed=2),
        SongSection(
            name="chorus",
            bars=8,
            layers=["melody", "counter", "arp", "drums"],
            drum_style="driving",
            bass_style="octave",
            seed=3,
        ),
        SongSection(
            name="verse2",
            bars=8,
            layers=["melody", "bass", "drums"],
            drum_style="sparse",
            bass_style="walking",
            seed=4,
        ),
        SongSection(
            name="chorus",
            bars=8,
            layers=["melody", "counter", "arp", "drums"],
            drum_style="driving",
            bass_style="octave",
            seed=3,
        ),
        SongSection(
            name="outro",
            bars=4,
            layers=["melody", "bass"],
            contour="descending",
            bass_style="root",
            seed=5,
        ),
    ]


def _render_section(
    section: SongSection,
    spec: SongSpec,
    exporter: AudioExporter,
    preset_factory: Any,
) -> NDArray[np.float32]:
    # Deterministic per-section material: same song seed + section seed
    # reproduces the same melody/bass/drum choices. Synthesis draws from both
    # python's and numpy's RNGs (noise channel), so seed both.
    random.seed(spec.seed * 7919 + section.seed)
    np.random.seed((spec.seed * 7919 + section.seed) % (2**32))

    composer: ChiptuneComposer = preset_factory(root=spec.root) if spec.root else preset_factory()
    if spec.bpm:
        composer.bpm = spec.bpm

    layers = [layer for layer in section.layers if layer in KNOWN_LAYERS]
    if "melody" in layers:
        composer.add_melody(contour=section.contour, length_bars=section.bars)
    if "counter" in layers:
        composer.add_countermelody(motion=section.counter_motion)
    if "arp" in layers:
        composer.add_arpeggio_layer()
    if "bass" in layers:
        composer.add_bass(style=section.bass_style)
    if "drums" in layers:
        composer.add_drums(pattern=section.drum_style)

    return exporter.render_track(composer.build())


def build_song(spec: SongSpec, effects: Any = None) -> NDArray[np.float32]:
    """Render all sections and stitch them into one mastered stereo array."""
    from chiptune.cli import GENRE_PRESET_METHODS
    from chiptune.presets import GenrePresets

    method = GENRE_PRESET_METHODS.get(spec.preset_factory)
    if method is None:
        raise ValueError(f"unknown preset {spec.preset_factory!r}")
    preset_factory = getattr(GenrePresets, method)

    sections = spec.sections or standard_structure("song")
    exporter = AudioExporter()
    rendered = [_render_section(s, spec, exporter, preset_factory) for s in sections]
    rendered = [r for r in rendered if len(r) > 0]
    if not rendered:
        raise ValueError("song rendered no audio")

    xfade = int(CROSSFADE_SECONDS * exporter.sample_rate)
    song = rendered[0]
    for part in rendered[1:]:
        n = min(xfade, len(song), len(part))
        if n > 0:
            # Equal-power crossfade to avoid clicks at section joins.
            t = np.linspace(0.0, np.pi / 2, n, dtype=np.float32)[:, None]
            tail = song[-n:] * np.cos(t) + part[:n] * np.sin(t)
            song = np.concatenate([song[:-n], tail, part[n:]])
        else:
            song = np.concatenate([song, part])

    # Master effects glue the sections together (echo tails across joins).
    if effects is not None:
        left = effects.process(song[:, 0], exporter.sample_rate)
        right = effects.process(song[:, 1], exporter.sample_rate)
        song = np.column_stack([left, right])

    peak = float(np.max(np.abs(song))) or 1.0
    return (song * (TARGET_PEAK / peak)).astype(np.float32)


def song_duration_seconds(song: NDArray[np.float32], sample_rate: int = 44100) -> float:
    return round(len(song) / sample_rate, 2)
