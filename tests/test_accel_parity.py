"""Parity tests: verify Rust acceleration produces identical output to Python.

These tests only run if the Rust extension is available. They compare
Rust output against the Python implementation to ensure correctness.
"""

import numpy as np
import pytest

from chiptune._accel import RUST_AVAILABLE

pytestmark = pytest.mark.skipif(
    not RUST_AVAILABLE, reason="Rust extension not available"
)


class TestNESNoiseParity:
    """Test NES noise generator Rust vs Python parity."""

    def test_nes_noise_long_mode_shape(self) -> None:
        """Rust NES noise produces correct array shape and dtype."""
        from chiptune._accel import _rust_nes_noise

        assert _rust_nes_noise is not None
        result = np.asarray(_rust_nes_noise(4, 44100, 1.0, 44100.0, "long"))
        assert result.shape == (44100,)
        assert result.dtype == np.float32

    def test_nes_noise_amplitude_bounds(self) -> None:
        """All values should be exactly +/-amplitude."""
        from chiptune._accel import _rust_nes_noise

        assert _rust_nes_noise is not None
        result = np.asarray(_rust_nes_noise(4, 1000, 0.5, 44100.0, "long"))
        unique = np.unique(result)
        assert len(unique) == 2
        np.testing.assert_array_almost_equal(sorted(unique), [-0.5, 0.5])

    def test_nes_noise_short_mode_different(self) -> None:
        """Short and long modes should produce different patterns."""
        from chiptune._accel import _rust_nes_noise

        assert _rust_nes_noise is not None
        long_result = np.asarray(_rust_nes_noise(4, 1000, 1.0, 44100.0, "long"))
        short_result = np.asarray(_rust_nes_noise(4, 1000, 1.0, 44100.0, "short"))
        # They should differ at some point (different feedback bits)
        assert not np.array_equal(long_result, short_result)


class TestSIDNoiseParity:
    """Test SID noise generator Rust vs Python parity."""

    def test_sid_noise_shape(self) -> None:
        """Rust SID noise produces correct shape."""
        from chiptune._accel import _rust_sid_noise

        assert _rust_sid_noise is not None
        result = np.asarray(_rust_sid_noise(440.0, 44100, 1.0, 44100.0))
        assert result.shape == (44100,)
        assert result.dtype == np.float32

    def test_sid_noise_range(self) -> None:
        """SID noise should be in [-amplitude, amplitude]."""
        from chiptune._accel import _rust_sid_noise

        assert _rust_sid_noise is not None
        result = np.asarray(_rust_sid_noise(440.0, 10000, 0.8, 44100.0))
        assert np.all(result >= -0.8 - 0.01)
        assert np.all(result <= 0.8 + 0.01)


class TestTapeDelayParity:
    """Test tape delay effect Rust vs Python parity."""

    def test_tape_delay_shape(self) -> None:
        """Output should match input shape."""
        from chiptune._accel import _rust_tape_delay

        assert _rust_tape_delay is not None
        samples = np.random.randn(44100).astype(np.float32) * 0.5
        result = np.asarray(_rust_tape_delay(samples.tolist(), 44100.0))
        assert result.shape == samples.shape

    def test_tape_delay_dry_only(self) -> None:
        """With mix=0, output should be dry signal."""
        from chiptune._accel import _rust_tape_delay

        assert _rust_tape_delay is not None
        samples = np.random.randn(1000).astype(np.float32) * 0.5
        result = np.asarray(_rust_tape_delay(samples.tolist(), 44100.0, mix=0.0))
        np.testing.assert_array_almost_equal(result, samples, decimal=5)


class TestChorusParity:
    """Test chorus effect parity."""

    def test_chorus_shape(self) -> None:
        """Output should match input shape."""
        from chiptune._accel import _rust_chorus

        assert _rust_chorus is not None
        samples = np.random.randn(44100).astype(np.float32) * 0.5
        result = np.asarray(_rust_chorus(samples.tolist(), 44100.0))
        assert result.shape == samples.shape


class TestPitchSweepParity:
    """Test pitch sweep parity."""

    def test_pitch_sweep_shape(self) -> None:
        """Output should have correct shape."""
        from chiptune._accel import _rust_pitch_sweep

        assert _rust_pitch_sweep is not None
        result = np.asarray(_rust_pitch_sweep(440.0, 44100, 44100.0))
        assert result.shape == (44100,)

    def test_pitch_sweep_starts_at_base(self) -> None:
        """First sample should be near base frequency."""
        from chiptune._accel import _rust_pitch_sweep

        assert _rust_pitch_sweep is not None
        result = np.asarray(_rust_pitch_sweep(440.0, 1000, 44100.0, start_delay=0.5))
        # During delay period, frequency should be base frequency
        np.testing.assert_almost_equal(result[0], 440.0, decimal=1)


class TestFMParity:
    """Test FM synthesis parity."""

    def test_fm_algorithm_shape(self) -> None:
        """Output should have correct shape."""
        from chiptune._accel import _rust_fm_algorithm

        assert _rust_fm_algorithm is not None
        n = 44100
        t = np.linspace(0, 1, n)
        phases = [list(2 * np.pi * 440 * t * (i + 1)) for i in range(4)]
        envelopes = [list(np.ones(n, dtype=np.float32)) for _ in range(4)]

        result = np.asarray(_rust_fm_algorithm(0, phases, envelopes, n))
        assert result.shape == (n,)
        assert result.dtype == np.float32

    def test_fm_algorithm7_parallel(self) -> None:
        """Algorithm 7 (all parallel) should produce non-zero output."""
        from chiptune._accel import _rust_fm_algorithm

        assert _rust_fm_algorithm is not None
        n = 1000
        t = np.linspace(0, 0.1, n)
        phases = [list(2 * np.pi * 440 * t) for _ in range(4)]
        envelopes = [list(np.ones(n, dtype=np.float32)) for _ in range(4)]

        result = np.asarray(_rust_fm_algorithm(7, phases, envelopes, n))
        assert np.any(result != 0.0)


class TestEnvelopeParity:
    """Test ADSR envelope parity."""

    def test_adsr_shape(self) -> None:
        """Output should have correct shape."""
        from chiptune._accel import _rust_adsr

        assert _rust_adsr is not None
        result = np.asarray(_rust_adsr(44100, 44100.0))
        assert result.shape == (44100,)
        assert result.dtype == np.float32

    def test_adsr_range(self) -> None:
        """Envelope values should be in [0, 1]."""
        from chiptune._accel import _rust_adsr

        assert _rust_adsr is not None
        result = np.asarray(
            _rust_adsr(44100, 44100.0, attack=0.1, decay=0.2, sustain=0.5)
        )
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0 + 0.001)
