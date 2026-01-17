"""Game sound effect generators.

Provides quick methods for generating common game sound effects
as MIDI, designed for the characteristic 8-bit/16-bit aesthetic.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from chiptune.output.midi import MidiExporter
from chiptune.theory.arpeggios import Note


class SFXGenerator(BaseModel):
    """Generate common game sound effects.

    All methods return MIDI bytes that can be played directly
    or saved to files.

    Example:
        ```python
        sfx = SFXGenerator()

        # Generate sounds
        coin = sfx.coin_collect()
        jump = sfx.jump()
        explosion = sfx.explosion()

        # Save to file
        sfx.save(coin, "coin.mid")
        ```
    """

    tempo: int = 180  # Fast tempo for quick effects
    base_octave: int = 5
    base_velocity: int = 100

    # Common pitch values for effects
    PITCHES: ClassVar[dict[str, int]] = {
        "low": 48,  # C3
        "mid": 60,  # C4
        "high": 72,  # C5
        "very_high": 84,  # C6
    }

    def _to_midi(self, notes: list[Note]) -> bytes:
        """Convert notes to MIDI bytes."""
        exporter = MidiExporter()
        return exporter.export_sfx_bytes(notes, self.tempo)

    def notes(self, kind: str) -> list[Note]:
        """Return the note sequence for an SFX pattern.

        Args:
            kind: SFX kind/method name (e.g., "coin_collect", "jump")
        """
        builder = getattr(self, f"_notes_{kind}", None)
        if builder is None:
            raise ValueError(f"Unknown SFX kind: {kind}")
        return builder()

    def _notes_coin_collect(self) -> list[Note]:
        return [
            Note(pitch=67, duration=0.0625, velocity=110),  # G4
            Note(pitch=72, duration=0.125, velocity=120),  # C5
        ]

    def coin_collect(self) -> bytes:
        """Generate coin collection sound.

        Classic ascending two-note blip.
        """
        return self._to_midi(self._notes_coin_collect())

    def _notes_jump(self) -> list[Note]:
        notes: list[Note] = []
        start_pitch = 48
        for i in range(6):
            notes.append(
                Note(
                    pitch=start_pitch + i * 4,
                    duration=0.03125,
                    velocity=100 - i * 10,
                )
            )
        return notes

    def jump(self) -> bytes:
        """Generate jump sound.

        Quick ascending pitch sweep.
        """
        return self._to_midi(self._notes_jump())

    def _notes_land(self) -> list[Note]:
        return [
            Note(pitch=36, duration=0.0625, velocity=110),  # C2
            Note(pitch=36, duration=0.0625, velocity=80),
        ]

    def land(self) -> bytes:
        """Generate landing sound.

        Short low thud.
        """
        return self._to_midi(self._notes_land())

    def _notes_explosion(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(8):
            pitch = 36 - i * 2
            notes.append(
                Note(
                    pitch=max(24, pitch),
                    duration=0.0625,
                    velocity=max(40, 120 - i * 10),
                )
            )
        return notes

    def explosion(self) -> bytes:
        """Generate explosion sound.

        Descending noise sweep with decay.
        """
        return self._to_midi(self._notes_explosion())

    def _notes_damage(self) -> list[Note]:
        return [
            Note(pitch=64, duration=0.0625, velocity=120),  # E4
            Note(pitch=60, duration=0.125, velocity=90),  # C4
        ]

    def damage(self) -> bytes:
        """Generate damage/hurt sound.

        Quick dissonant burst.
        """
        return self._to_midi(self._notes_damage())

    def _notes_powerup(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(8):
            notes.append(
                Note(
                    pitch=60 + i,
                    duration=0.0625,
                    velocity=80 + i * 5,
                )
            )
        notes.append(Note(pitch=72, duration=0.25, velocity=120))
        return notes

    def powerup(self) -> bytes:
        """Generate power-up sound.

        Ascending chromatic run with triumphant ending.
        """
        return self._to_midi(self._notes_powerup())

    def _notes_menu_select(self) -> list[Note]:
        return [
            Note(pitch=67, duration=0.0625, velocity=80),  # G4
        ]

    def menu_select(self) -> bytes:
        """Generate menu selection blip.

        Single short tone.
        """
        return self._to_midi(self._notes_menu_select())

    def _notes_menu_confirm(self) -> list[Note]:
        return [
            Note(pitch=60, duration=0.0625, velocity=90),  # C4
            Note(pitch=72, duration=0.125, velocity=100),  # C5
        ]

    def menu_confirm(self) -> bytes:
        """Generate menu confirmation sound.

        Two-note ascending confirmation.
        """
        return self._to_midi(self._notes_menu_confirm())

    def _notes_menu_back(self) -> list[Note]:
        return [
            Note(pitch=67, duration=0.0625, velocity=80),  # G4
            Note(pitch=60, duration=0.0625, velocity=70),  # C4
        ]

    def menu_back(self) -> bytes:
        """Generate menu back/cancel sound.

        Two-note descending.
        """
        return self._to_midi(self._notes_menu_back())

    def _notes_error(self) -> list[Note]:
        return [
            Note(pitch=36, duration=0.125, velocity=100),  # C2
            Note(pitch=35, duration=0.125, velocity=90),  # B1
        ]

    def error(self) -> bytes:
        """Generate error/invalid action sound.

        Low buzzer tone.
        """
        return self._to_midi(self._notes_error())

    def _notes_success(self) -> list[Note]:
        return [
            Note(pitch=60, duration=0.0625, velocity=100),  # C4
            Note(pitch=64, duration=0.0625, velocity=105),  # E4
            Note(pitch=67, duration=0.0625, velocity=110),  # G4
            Note(pitch=72, duration=0.125, velocity=120),  # C5
        ]

    def success(self) -> bytes:
        """Generate success sound.

        Quick major arpeggio.
        """
        return self._to_midi(self._notes_success())

    def _notes_door_open(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(4):
            notes.append(
                Note(
                    pitch=48 + i * 5,
                    duration=0.125,
                    velocity=80 + i * 10,
                )
            )
        return notes

    def door_open(self) -> bytes:
        """Generate door opening sound.

        Ascending sweep.
        """
        return self._to_midi(self._notes_door_open())

    def _notes_door_close(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(4):
            notes.append(
                Note(
                    pitch=60 - i * 5,
                    duration=0.125,
                    velocity=100 - i * 10,
                )
            )
        return notes

    def door_close(self) -> bytes:
        """Generate door closing sound.

        Descending sweep.
        """
        return self._to_midi(self._notes_door_close())

    def _notes_laser(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(5):
            notes.append(
                Note(
                    pitch=84 - i * 6,
                    duration=0.03125,
                    velocity=120 - i * 15,
                )
            )
        return notes

    def laser(self) -> bytes:
        """Generate laser/projectile sound.

        Quick descending zap.
        """
        return self._to_midi(self._notes_laser())

    def _notes_shield(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(6):
            pitch = 72 if i % 2 == 0 else 76
            notes.append(Note(pitch=pitch, duration=0.0625, velocity=90))
        return notes

    def shield(self) -> bytes:
        """Generate shield activation sound.

        Warbling tone.
        """
        return self._to_midi(self._notes_shield())

    def _notes_teleport(self) -> list[Note]:
        notes: list[Note] = []
        for i in range(6):
            notes.append(Note(pitch=48 + i * 6, duration=0.03125, velocity=100))
        for i in range(6):
            notes.append(Note(pitch=84 - i * 6, duration=0.03125, velocity=100))
        return notes

    def teleport(self) -> bytes:
        """Generate teleport sound.

        Ascending then descending sweep.
        """
        return self._to_midi(self._notes_teleport())

    def _notes_heartbeat(self) -> list[Note]:
        return [
            Note(pitch=36, duration=0.125, velocity=100),
            Note(pitch=36, duration=0.0625, velocity=80),
            Note(pitch=0, duration=0.25, velocity=0),  # Rest
            Note(pitch=36, duration=0.125, velocity=90),
            Note(pitch=36, duration=0.0625, velocity=70),
        ]

    def heartbeat(self) -> bytes:
        """Generate heartbeat/tension sound.

        Two low thumps.
        """
        return self._to_midi(self._notes_heartbeat())

    def _notes_countdown_tick(self) -> list[Note]:
        return [
            Note(pitch=80, duration=0.03125, velocity=100),
        ]

    def countdown_tick(self) -> bytes:
        """Generate countdown tick sound.

        Single percussive click.
        """
        return self._to_midi(self._notes_countdown_tick())

    def _notes_countdown_final(self) -> list[Note]:
        return [
            Note(pitch=48, duration=0.125, velocity=120),
            Note(pitch=60, duration=0.25, velocity=127),
        ]

    def countdown_final(self) -> bytes:
        """Generate final countdown sound.

        Dramatic final tick.
        """
        return self._to_midi(self._notes_countdown_final())

    def save(self, midi_bytes: bytes, path: str) -> None:
        """Save MIDI bytes to a file.

        Args:
            midi_bytes: MIDI data from any generator method
            path: Output file path
        """
        with open(path, "wb") as f:
            f.write(midi_bytes)
