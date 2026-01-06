"""Tests for audio effects."""

import numpy as np
import pytest

from chiptune.output.audio.effects import (
    Chorus,
    EffectChain,
    EffectPresets,
    Ensemble,
    LFO,
    LFOShape,
    MultiTapDelay,
    ParallelChain,
    PitchBend,
    PitchSweep,
    Portamento,
    SweepDirection,
    TapeDelay,
    Tremolo,
    Unison,
    Vibrato,
    VibratoSample,
)


class TestLFO:
    """Tests for LFO oscillator."""

    def test_sine_shape(self) -> None:
        """Sine LFO should produce smooth oscillation."""
        lfo = LFO(rate=1.0, depth=1.0, shape=LFOShape.SINE)
        samples = lfo.generate(44100, sample_rate=44100)

        assert len(samples) == 44100
        assert np.max(samples) <= 1.0
        assert np.min(samples) >= -1.0

    def test_square_shape(self) -> None:
        """Square LFO should produce binary values."""
        lfo = LFO(rate=2.0, depth=1.0, shape=LFOShape.SQUARE)
        samples = lfo.generate(1000, sample_rate=1000)

        # Should only have values near +1 and -1
        unique = np.unique(np.round(samples, 1))
        assert len(unique) == 2

    def test_depth_scales_output(self) -> None:
        """Depth should scale output amplitude."""
        lfo_full = LFO(rate=1.0, depth=1.0)
        lfo_half = LFO(rate=1.0, depth=0.5)

        full = lfo_full.generate(1000, 44100)
        half = lfo_half.generate(1000, 44100)

        assert np.max(np.abs(full)) > np.max(np.abs(half))

    def test_delay(self) -> None:
        """LFO with delay should start silent."""
        lfo = LFO(rate=5.0, depth=1.0, delay=0.1)
        samples = lfo.generate(4410, sample_rate=44100)  # 0.1 seconds

        # First samples should be near zero
        assert np.abs(samples[0]) < 0.01

    def test_unipolar(self) -> None:
        """Unipolar output should be 0 to depth."""
        lfo = LFO(rate=1.0, depth=0.8)
        samples = lfo.generate_unipolar(1000, 44100)

        assert np.min(samples) >= 0
        assert np.max(samples) <= 0.8

    def test_presets(self) -> None:
        """Preset methods should return valid LFOs."""
        assert LFO.vibrato().rate == 5.0
        assert LFO.tremolo().rate == 4.0
        assert LFO.chiptune().shape == LFOShape.SQUARE


class TestTremolo:
    """Tests for tremolo effect."""

    def test_modulates_amplitude(self) -> None:
        """Tremolo should modulate amplitude."""
        samples = np.ones(4410, dtype=np.float32)  # 0.1 seconds of DC
        tremolo = Tremolo(rate=10.0, depth=0.5)

        output = tremolo.process(samples, sample_rate=44100)

        # Output should vary (not constant)
        assert np.std(output) > 0.1

    def test_preserves_length(self) -> None:
        """Output should be same length as input."""
        samples = np.random.randn(1000).astype(np.float32)
        tremolo = Tremolo()

        output = tremolo.process(samples)

        assert len(output) == len(samples)

    def test_presets(self) -> None:
        """Preset methods should return valid tremolos."""
        assert Tremolo.subtle().depth < Tremolo.hard().depth
        assert Tremolo.helicopter().rate > Tremolo.classic().rate


class TestTapeDelay:
    """Tests for tape delay effect."""

    def test_creates_echo(self) -> None:
        """Delay should create echoes."""
        # Impulse signal
        samples = np.zeros(44100, dtype=np.float32)
        samples[0] = 1.0

        delay = TapeDelay(delay_time=0.1, feedback=0.5, mix=0.5)
        output = delay.process(samples, sample_rate=44100)

        # Should have energy after the initial impulse
        post_delay = output[4410:]  # After 0.1s delay
        assert np.max(np.abs(post_delay)) > 0.1

    def test_feedback_creates_repeats(self) -> None:
        """Higher feedback should create more repeats."""
        samples = np.zeros(44100, dtype=np.float32)
        samples[0] = 1.0

        low_fb = TapeDelay(delay_time=0.1, feedback=0.2, mix=0.5)
        high_fb = TapeDelay(delay_time=0.1, feedback=0.7, mix=0.5)

        out_low = low_fb.process(samples, sample_rate=44100)
        out_high = high_fb.process(samples, sample_rate=44100)

        # Higher feedback = more energy in later samples
        late_energy_low = np.sum(np.abs(out_low[22050:]))
        late_energy_high = np.sum(np.abs(out_high[22050:]))
        assert late_energy_high > late_energy_low

    def test_presets(self) -> None:
        """Preset methods should return valid delays."""
        space = TapeDelay.space_echo()
        assert space.wow_depth > 0
        assert space.saturation > 0

        dub = TapeDelay.dub()
        assert dub.feedback > 0.5

        lofi = TapeDelay.lo_fi()
        assert lofi.tape_age > 0.5


class TestChorus:
    """Tests for chorus effect."""

    def test_creates_movement(self) -> None:
        """Chorus should add movement/variation."""
        # Constant tone
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)
        samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        chorus = Chorus(voices=3, depth=3.0, rate=1.0, mix=0.5)
        output = chorus.process(samples, sample_rate=44100)

        # Output should differ from input
        diff = np.mean(np.abs(output - samples))
        assert diff > 0.01

    def test_preserves_length(self) -> None:
        """Output should be same length as input."""
        samples = np.random.randn(1000).astype(np.float32)
        chorus = Chorus.classic()

        output = chorus.process(samples)

        assert len(output) == len(samples)

    def test_presets(self) -> None:
        """Preset methods should return valid choruses."""
        assert Chorus.lush().voices >= Chorus.subtle().voices
        assert Chorus.shimmer().spread > 0


class TestUnison:
    """Tests for unison detuning."""

    def test_thickens_sound(self) -> None:
        """Unison should create thicker sound."""
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)
        samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        unison = Unison(voices=3, detune=10.0, mix=0.7)
        output = unison.process(samples, sample_rate=44100)

        # Should be different from original
        assert not np.allclose(output, samples)

    def test_presets(self) -> None:
        """Preset methods should return valid unisons."""
        supersaw = Unison.supersaw()
        assert supersaw.voices >= 5
        assert supersaw.detune >= 10.0


class TestEnsemble:
    """Tests for ensemble effect."""

    def test_creates_ensemble(self) -> None:
        """Ensemble should create rich layered sound."""
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)
        samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        ensemble = Ensemble.strings()
        output = ensemble.process(samples, sample_rate=44100)

        # Should differ from original
        assert not np.allclose(output, samples)

    def test_presets(self) -> None:
        """Preset methods should return valid ensembles."""
        assert Ensemble.strings().size >= 4
        assert Ensemble.choir().drift > 0


class TestVibrato:
    """Tests for vibrato effect."""

    def test_modulates_pitch(self) -> None:
        """Vibrato should generate frequency array."""
        vibrato = Vibrato(rate=5.0, depth=0.5)
        t = np.linspace(0, 1.0, 44100, dtype=np.float32)

        freqs = vibrato.modulate_frequency(440.0, t, sample_rate=44100)

        assert len(freqs) == len(t)
        # Should vary around base frequency
        assert np.min(freqs) < 440.0
        assert np.max(freqs) > 440.0

    def test_delay(self) -> None:
        """Vibrato delay should keep initial pitch stable."""
        vibrato = Vibrato(rate=5.0, depth=0.5, delay=0.2)
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)

        freqs = vibrato.modulate_frequency(440.0, t, sample_rate=44100)

        # Early samples should be near base frequency
        assert np.allclose(freqs[:100], 440.0, atol=5)


class TestPitchSweep:
    """Tests for NES-style pitch sweep."""

    def test_sweep_down(self) -> None:
        """Downward sweep should decrease frequency."""
        sweep = PitchSweep(direction=SweepDirection.DOWN, rate=2, shift=2)
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)

        freqs = sweep.modulate_frequency(440.0, t, sample_rate=44100)

        # Frequency should decrease over time
        assert freqs[-1] < freqs[0]

    def test_sweep_up(self) -> None:
        """Upward sweep should increase frequency."""
        sweep = PitchSweep(direction=SweepDirection.UP, rate=2, shift=2)
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)

        freqs = sweep.modulate_frequency(440.0, t, sample_rate=44100)

        # Frequency should increase over time
        assert freqs[-1] > freqs[0]


class TestPortamento:
    """Tests for portamento/glide."""

    def test_glides_to_target(self) -> None:
        """Portamento should glide from start to target frequency."""
        porta = Portamento(start_frequency=220.0, glide_time=0.1)
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)

        freqs = porta.modulate_frequency(440.0, t, sample_rate=44100)

        # Should start at start_frequency and end at target
        assert freqs[0] == pytest.approx(220.0, rel=0.1)
        assert freqs[-1] == pytest.approx(440.0, rel=0.01)


class TestPitchBend:
    """Tests for pitch bend."""

    def test_bends_up(self) -> None:
        """Positive bend should increase pitch."""
        bend = PitchBend(bend_semitones=2.0, bend_time=0.1, hold_time=0.1)
        t = np.linspace(0, 0.3, 13230, dtype=np.float32)

        freqs = bend.modulate_frequency(440.0, t, sample_rate=44100)

        # Should reach higher pitch
        assert np.max(freqs) > 440.0

    def test_returns_to_base(self) -> None:
        """Bend with return should come back to base pitch."""
        bend = PitchBend(
            bend_semitones=2.0, bend_time=0.05, hold_time=0.05, return_time=0.1
        )
        t = np.linspace(0, 0.5, 22050, dtype=np.float32)

        freqs = bend.modulate_frequency(440.0, t, sample_rate=44100)

        # End should be back at base frequency
        assert freqs[-1] == pytest.approx(440.0, rel=0.01)


class TestEffectChain:
    """Tests for effect chaining."""

    def test_chains_effects(self) -> None:
        """Chain should process through all effects."""
        samples = np.random.randn(1000).astype(np.float32) * 0.5

        chain = EffectChain(
            effects=[
                Tremolo(rate=5.0, depth=0.3),
                Chorus.subtle(),
            ]
        )

        output = chain.process(samples, sample_rate=44100)

        assert len(output) == len(samples)
        # Should be modified
        assert not np.allclose(output, samples)

    def test_pipe_operator(self) -> None:
        """| operator should chain effects."""
        chain = Tremolo() | Chorus.subtle()

        assert len(chain.effects) == 2

    def test_presets(self) -> None:
        """Effect presets should return valid chains."""
        ambient = EffectPresets.ambient()
        assert len(ambient.effects) >= 2

        retro = EffectPresets.retro()
        assert len(retro.effects) >= 1


class TestParallelChain:
    """Tests for parallel effect processing."""

    def test_parallel_mixing(self) -> None:
        """Parallel chain should mix effect outputs."""
        samples = np.ones(1000, dtype=np.float32)

        parallel = ParallelChain(
            chains=[
                Tremolo(rate=5.0, depth=0.5),
                Chorus.subtle(),
            ],
            levels=[0.5, 0.5],
            dry_level=0.0,
        )

        output = parallel.process(samples, sample_rate=44100)

        assert len(output) == len(samples)


class TestMultiTapDelay:
    """Tests for multi-tap delay."""

    def test_creates_multiple_echoes(self) -> None:
        """Multi-tap should create echoes at different times."""
        samples = np.zeros(44100, dtype=np.float32)
        samples[0] = 1.0

        delay = MultiTapDelay(
            taps=[0.1, 0.2, 0.3],
            tap_levels=[0.8, 0.5, 0.3],
            mix=0.5,
        )

        output = delay.process(samples, sample_rate=44100)

        # Should have energy at different delay times
        assert np.max(np.abs(output[4000:5000])) > 0.1
        assert np.max(np.abs(output[8000:9500])) > 0.05


class TestEffectDtype:
    """Tests for output dtype consistency."""

    def test_all_effects_output_float32(self) -> None:
        """All effects should output float32."""
        samples = np.random.randn(1000).astype(np.float32)

        effects = [
            Tremolo.classic(),
            TapeDelay.slapback(),
            Chorus.classic(),
            Unison.subtle(),
            Ensemble.synth_pad(),
            VibratoSample(),
        ]

        for effect in effects:
            output = effect.process(samples, sample_rate=44100)
            assert output.dtype == np.float32, f"{type(effect).__name__} wrong dtype"
