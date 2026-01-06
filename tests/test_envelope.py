"""Tests for ADSR envelopes."""

import numpy as np
import pytest

from chiptune.output.audio.envelope import ADSREnvelope


class TestADSREnvelope:
    """Tests for ADSR envelope generation."""

    def test_attack_reaches_peak(self) -> None:
        """Attack phase should reach amplitude 1.0."""
        env = ADSREnvelope(
            attack_time=0.1,
            decay_time=0.0,
            sustain_level=1.0,
            release_time=0.0,
        )
        samples = env.generate(1.0, 44100)

        assert np.max(samples) >= 0.99

    def test_sustain_level(self) -> None:
        """Sustain phase should hold at specified level."""
        env = ADSREnvelope(
            attack_time=0.01,
            decay_time=0.01,
            sustain_level=0.5,
            release_time=0.01,
        )
        samples = env.generate(1.0, 44100)

        # Middle section should be at sustain level
        mid_idx = len(samples) // 2
        assert 0.45 < samples[mid_idx] < 0.55

    def test_release_to_zero(self) -> None:
        """Release phase should decay to zero."""
        env = ADSREnvelope(
            attack_time=0.01,
            decay_time=0.01,
            sustain_level=0.8,
            release_time=0.1,
        )
        samples = env.generate(0.5, 44100)

        # Last sample should be near zero
        assert samples[-1] < 0.1

    def test_velocity_scaling(self) -> None:
        """Velocity parameter should scale output amplitude."""
        env = ADSREnvelope.chip_lead()

        full = env.generate(1.0, 44100, velocity=1.0)
        half = env.generate(1.0, 44100, velocity=0.5)

        assert np.max(half) < np.max(full) * 0.6

    def test_zero_velocity(self) -> None:
        """Zero velocity should produce silence."""
        env = ADSREnvelope.chip_lead()
        samples = env.generate(1.0, 44100, velocity=0.0)

        assert np.max(np.abs(samples)) == 0.0

    def test_short_note(self) -> None:
        """Very short notes should still have valid envelopes."""
        env = ADSREnvelope(
            attack_time=0.1,
            decay_time=0.1,
            sustain_level=0.7,
            release_time=0.1,
        )
        # Duration shorter than ADSR phases
        samples = env.generate(0.05, 44100)

        assert len(samples) > 0
        assert not np.any(np.isnan(samples))

    def test_empty_duration(self) -> None:
        """Zero duration should return empty array."""
        env = ADSREnvelope.chip_lead()
        samples = env.generate(0.0, 44100)

        assert len(samples) == 0

    def test_output_dtype(self) -> None:
        """Output should be float32."""
        env = ADSREnvelope.chip_lead()
        samples = env.generate(1.0, 44100)

        assert samples.dtype == np.float32


class TestEnvelopePresets:
    """Tests for envelope preset factory methods."""

    def test_chip_lead_fast_attack(self) -> None:
        """Chip lead preset should have very fast attack."""
        env = ADSREnvelope.chip_lead()
        assert env.attack_time < 0.01

    def test_chip_bass_high_sustain(self) -> None:
        """Chip bass preset should have high sustain."""
        env = ADSREnvelope.chip_bass()
        assert env.sustain_level >= 0.8

    def test_pluck_zero_sustain(self) -> None:
        """Pluck preset should have zero sustain."""
        env = ADSREnvelope.pluck()
        assert env.sustain_level == 0.0

    def test_percussion_instant_attack(self) -> None:
        """Percussion preset should have instant attack."""
        env = ADSREnvelope.percussion()
        assert env.attack_time == 0.0

    def test_pad_slow_attack(self) -> None:
        """Pad preset should have slow attack."""
        env = ADSREnvelope.pad()
        assert env.attack_time >= 0.05
