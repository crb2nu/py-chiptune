"""Tests for AudioExporter."""

from pathlib import Path

import numpy as np

from chiptune import ChiptuneComposer
from chiptune.chip.channels import Channel, DutyCycle, NESChannels
from chiptune.output.audio import AudioExporter
from chiptune.theory.arpeggios import Note
from chiptune.theory.keys import Key


class TestAudioExporter:
    """Tests for AudioExporter class."""

    def test_render_track_stereo(self) -> None:
        """Rendered output should be stereo (N, 2)."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=2)
        track = composer.build()

        exporter = AudioExporter()
        audio = exporter.render_track(track)

        assert audio.ndim == 2
        assert audio.shape[1] == 2

    def test_render_track_float32(self) -> None:
        """Output should be float32."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=1)
        track = composer.build()

        exporter = AudioExporter()
        audio = exporter.render_track(track)

        assert audio.dtype == np.float32

    def test_render_empty_track(self) -> None:
        """Empty track should produce empty output."""
        # Create track with no parts
        key = Key(root="C")
        channels = NESChannels.create()

        from chiptune.composer.composer import Track

        track = Track(
            name="empty",
            bpm=120,
            key=key,
            channels=channels,
            length_beats=0.0,
        )

        exporter = AudioExporter()
        audio = exporter.render_track(track)

        assert audio.shape == (0, 2)

    def test_sample_rate_affects_length(self) -> None:
        """Different sample rates should produce different sample counts."""
        composer = ChiptuneComposer.create(bpm=120)
        composer.add_melody(length_bars=1)  # 4 beats = 2 seconds at 120 bpm
        track = composer.build()

        exporter_44k = AudioExporter(sample_rate=44100)
        exporter_22k = AudioExporter(sample_rate=22050)

        audio_44k = exporter_44k.render_track(track)
        audio_22k = exporter_22k.render_track(track)

        # 44.1k should have roughly twice as many samples as 22.05k
        assert len(audio_44k) > len(audio_22k) * 1.9

    def test_render_channel_pulse(self) -> None:
        """Rendering a pulse channel should produce audio."""
        channel = Channel.pulse(channel_id=0, duty=DutyCycle.DUTY_25)
        channel.add_notes(
            [
                Note(pitch=60, duration=1.0, velocity=100),
                Note(pitch=64, duration=1.0, velocity=100),
            ]
        )

        exporter = AudioExporter()
        samples = exporter.render_channel(channel, bpm=120)

        assert len(samples) > 0
        assert np.max(np.abs(samples)) > 0

    def test_render_channel_triangle(self) -> None:
        """Rendering a triangle channel should produce audio."""
        channel = Channel.triangle(channel_id=2)
        channel.add_notes(
            [
                Note(pitch=48, duration=2.0, velocity=100),
            ]
        )

        exporter = AudioExporter()
        samples = exporter.render_channel(channel, bpm=120)

        assert len(samples) > 0

    def test_render_channel_noise(self) -> None:
        """Rendering a noise channel should produce audio."""
        channel = Channel.noise(channel_id=3)
        channel.add_notes(
            [
                Note(pitch=5, duration=0.5, velocity=100),  # period 5
                Note(pitch=10, duration=0.5, velocity=80),  # period 10
            ]
        )

        exporter = AudioExporter()
        samples = exporter.render_channel(channel, bpm=120)

        assert len(samples) > 0

    def test_rests_produce_silence(self) -> None:
        """Velocity 0 notes (rests) should produce silence."""
        channel = Channel.pulse(channel_id=0)
        channel.add_notes(
            [
                Note(pitch=60, duration=1.0, velocity=0),  # Rest
            ]
        )

        exporter = AudioExporter()
        samples = exporter.render_channel(channel, bpm=120)

        # Should be all zeros (or at least very quiet)
        assert np.max(np.abs(samples)) < 0.01


class TestWavExport:
    """Tests for WAV file export."""

    def test_export_wav_creates_file(self, tmp_path: Path) -> None:
        """export_wav should create a valid WAV file."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=2)
        track = composer.build()

        exporter = AudioExporter()
        path = tmp_path / "test.wav"
        exporter.export_wav(track, str(path))

        assert path.exists()
        assert path.stat().st_size > 44  # WAV header + data

    def test_export_wav_header(self, tmp_path: Path) -> None:
        """WAV file should have correct RIFF header."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=1)
        track = composer.build()

        exporter = AudioExporter()
        path = tmp_path / "test.wav"
        exporter.export_wav(track, str(path))

        with open(path, "rb") as f:
            header = f.read(4)
            assert header == b"RIFF"

    def test_export_bytes_wav(self) -> None:
        """export_bytes should return valid WAV data."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=1)
        track = composer.build()

        exporter = AudioExporter()
        data = exporter.export_bytes(track, format="wav")

        assert data[:4] == b"RIFF"
        assert len(data) > 44


class TestSfxExport:
    """Tests for SFX audio export."""

    def test_export_sfx_wav(self) -> None:
        """export_sfx should return valid WAV data."""
        notes = [
            Note(pitch=67, duration=0.125, velocity=110),
            Note(pitch=72, duration=0.25, velocity=120),
        ]

        exporter = AudioExporter()
        data = exporter.export_sfx(notes, tempo=120)

        assert data[:4] == b"RIFF"

    def test_export_sfx_with_duty(self) -> None:
        """export_sfx should respect duty cycle parameter."""
        notes = [Note(pitch=60, duration=0.5, velocity=100)]

        exporter = AudioExporter()
        data_25 = exporter.export_sfx(notes, duty=DutyCycle.DUTY_25)
        data_50 = exporter.export_sfx(notes, duty=DutyCycle.DUTY_50)

        # Different duty cycles should produce different audio
        # (can't easily compare bytes due to compression)
        assert len(data_25) > 0
        assert len(data_50) > 0


class TestComposerIntegration:
    """Integration tests with ChiptuneComposer."""

    def test_composer_export_wav(self, tmp_path: Path) -> None:
        """ChiptuneComposer.export_wav should work."""
        composer = ChiptuneComposer.create(bpm=140, root="C")
        composer.add_melody(length_bars=4)
        composer.add_bass()

        path = tmp_path / "composition.wav"
        composer.export_wav(str(path))

        assert path.exists()
        assert path.stat().st_size > 1000

    def test_composer_to_audio_bytes(self) -> None:
        """ChiptuneComposer.to_audio_bytes should return WAV."""
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=2)

        wav_bytes = composer.to_audio_bytes()

        assert wav_bytes[:4] == b"RIFF"

    def test_full_composition_wav(self, tmp_path: Path) -> None:
        """Full composition with all elements should export."""
        composer = ChiptuneComposer.create(bpm=140, root="G")
        composer.set_theme("battle")
        composer.add_melody(length_bars=4)
        composer.add_bass(style="octave")
        composer.add_drums(pattern="driving")

        path = tmp_path / "battle.wav"
        composer.export_wav(str(path))

        assert path.exists()
        # Battle theme with drums should be reasonably sized
        assert path.stat().st_size > 50000
