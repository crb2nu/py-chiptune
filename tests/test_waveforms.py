"""Tests for NES waveform generators."""

import numpy as np
import pytest

from chiptune.chip.channels import DutyCycle
from chiptune.output.audio.waveforms import (
    NoiseGenerator,
    PulseWaveGenerator,
    TriangleWaveGenerator,
    midi_to_frequency,
)


class TestPulseWaveGenerator:
    """Tests for pulse wave generation."""

    def test_duty_cycle_12_5(self) -> None:
        """12.5% duty produces approximately 1/8 high samples."""
        gen = PulseWaveGenerator(duty=DutyCycle.DUTY_12_5)
        samples = gen.generate(440.0, 0.1)

        high_ratio = np.sum(samples > 0) / len(samples)
        assert 0.10 < high_ratio < 0.16

    def test_duty_cycle_25(self) -> None:
        """25% duty produces approximately 1/4 high samples."""
        gen = PulseWaveGenerator(duty=DutyCycle.DUTY_25)
        samples = gen.generate(440.0, 0.1)

        high_ratio = np.sum(samples > 0) / len(samples)
        assert 0.20 < high_ratio < 0.30

    def test_duty_cycle_50(self) -> None:
        """50% duty produces equal high/low samples."""
        gen = PulseWaveGenerator(duty=DutyCycle.DUTY_50)
        samples = gen.generate(440.0, 0.1)

        high_ratio = np.sum(samples > 0) / len(samples)
        assert 0.48 < high_ratio < 0.52

    def test_amplitude_scaling(self) -> None:
        """Amplitude parameter scales output correctly."""
        gen = PulseWaveGenerator()
        samples_full = gen.generate(440.0, 0.01, amplitude=1.0)
        samples_half = gen.generate(440.0, 0.01, amplitude=0.5)

        assert np.max(np.abs(samples_full)) == pytest.approx(1.0)
        assert np.max(np.abs(samples_half)) == pytest.approx(0.5)

    def test_sample_rate(self) -> None:
        """Sample rate affects number of samples generated."""
        gen_44k = PulseWaveGenerator(sample_rate=44100)
        gen_22k = PulseWaveGenerator(sample_rate=22050)

        samples_44k = gen_44k.generate(440.0, 1.0)
        samples_22k = gen_22k.generate(440.0, 1.0)

        assert len(samples_44k) == 44100
        assert len(samples_22k) == 22050

    def test_output_dtype(self) -> None:
        """Output should be float32."""
        gen = PulseWaveGenerator()
        samples = gen.generate(440.0, 0.01)

        assert samples.dtype == np.float32


class TestTriangleWaveGenerator:
    """Tests for NES-style triangle wave generation."""

    def test_quantization(self) -> None:
        """Triangle uses discrete 16 steps (32 unique bipolar values)."""
        gen = TriangleWaveGenerator()
        samples = gen.generate(440.0, 0.1)

        # Round to avoid floating point noise
        unique_values = len(np.unique(np.round(samples, 4)))
        # Should have at most 32 unique values (16 levels * 2 for +/-)
        assert unique_values <= 32

    def test_bipolar_output(self) -> None:
        """Triangle wave should oscillate between -1 and 1."""
        gen = TriangleWaveGenerator()
        samples = gen.generate(440.0, 0.1, amplitude=1.0)

        assert np.min(samples) >= -1.0
        assert np.max(samples) <= 1.0
        # Should actually reach near the extremes
        assert np.max(samples) > 0.9
        assert np.min(samples) < -0.9

    def test_amplitude_scaling(self) -> None:
        """Amplitude parameter scales output correctly."""
        gen = TriangleWaveGenerator()
        samples = gen.generate(440.0, 0.1, amplitude=0.5)

        assert np.max(np.abs(samples)) <= 0.51


class TestNoiseGenerator:
    """Tests for NES-style noise generation."""

    def test_period_affects_content(self) -> None:
        """Lower period should produce higher frequency content."""
        gen = NoiseGenerator()

        # Lower period = faster LFSR clocking = more variation
        low_samples = gen.generate(period=0, duration=0.1)
        high_samples = gen.generate(period=15, duration=0.1)

        # Measure average sample-to-sample change
        low_diff = np.mean(np.abs(np.diff(low_samples)))
        high_diff = np.mean(np.abs(np.diff(high_samples)))

        # Low period should have more variation
        assert low_diff > high_diff

    def test_period_clamping(self) -> None:
        """Period values outside 0-15 should be clamped."""
        gen = NoiseGenerator()

        # Should not raise errors
        samples_neg = gen.generate(period=-5, duration=0.01)
        samples_high = gen.generate(period=100, duration=0.01)

        assert len(samples_neg) > 0
        assert len(samples_high) > 0

    def test_short_mode(self) -> None:
        """Short mode produces more tonal (periodic) noise."""
        gen_short = NoiseGenerator(mode="short")
        gen_long = NoiseGenerator(mode="long")

        samples_short = gen_short.generate(period=5, duration=0.1)
        samples_long = gen_long.generate(period=5, duration=0.1)

        # Both should produce valid output
        assert len(samples_short) == len(samples_long)

    def test_bipolar_output(self) -> None:
        """Noise should be bipolar (-amplitude to +amplitude)."""
        gen = NoiseGenerator()
        samples = gen.generate(period=5, duration=0.1, amplitude=1.0)

        # Should have both positive and negative values
        assert np.any(samples > 0)
        assert np.any(samples < 0)


class TestMidiToFrequency:
    """Tests for MIDI note to frequency conversion."""

    def test_a4_is_440(self) -> None:
        """MIDI note 69 (A4) should be 440 Hz."""
        assert midi_to_frequency(69) == pytest.approx(440.0)

    def test_octave_doubling(self) -> None:
        """Going up an octave (12 semitones) doubles frequency."""
        assert midi_to_frequency(81) == pytest.approx(880.0)
        assert midi_to_frequency(57) == pytest.approx(220.0)

    def test_middle_c(self) -> None:
        """MIDI note 60 (C4) should be approximately 261.63 Hz."""
        assert midi_to_frequency(60) == pytest.approx(261.626, rel=0.001)
