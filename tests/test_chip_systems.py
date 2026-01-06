"""Tests for chip system emulators."""

import numpy as np
import pytest

from chiptune.chip.systems import (
    ChipType,
    FMAlgorithm,
    FMOperator,
    FMVoice,
    GameBoyChip,
    GBDutyCycle,
    GBNoiseVoice,
    GBPulseVoice,
    GBWaveVoice,
    GenesisChip,
    SIDChip,
    SIDFilter,
    SIDFilterMode,
    SIDRevision,
    SIDVoice,
    SIDWaveform,
    VoiceType,
    midi_to_frequency,
)
from chiptune.theory.arpeggios import Note


class TestMidiToFrequency:
    """Tests for MIDI conversion utilities."""

    def test_a4_is_440hz(self) -> None:
        """A4 (MIDI 69) should be 440 Hz."""
        assert midi_to_frequency(69) == pytest.approx(440.0)

    def test_octave_doubles_frequency(self) -> None:
        """Going up an octave should double frequency."""
        freq_c4 = midi_to_frequency(60)
        freq_c5 = midi_to_frequency(72)
        assert freq_c5 == pytest.approx(freq_c4 * 2, rel=0.001)


class TestGameBoyChip:
    """Tests for Game Boy DMG chip."""

    def test_create_chip(self) -> None:
        """Should create chip with 4 voices."""
        chip = GameBoyChip.create()
        assert chip.chip_type == ChipType.GAMEBOY
        assert len(chip.voices) == 4

    def test_voice_types(self) -> None:
        """Should have correct voice types."""
        chip = GameBoyChip()
        assert chip.pulse1.voice_type == VoiceType.PULSE
        assert chip.pulse2.voice_type == VoiceType.PULSE
        assert chip.wave.voice_type == VoiceType.WAVETABLE
        assert chip.noise.voice_type == VoiceType.NOISE

    def test_pulse_sweep(self) -> None:
        """Pulse 1 should have sweep capability."""
        chip = GameBoyChip()
        assert chip.pulse1.has_sweep is True
        assert chip.pulse2.has_sweep is False

    def test_pulse_generation(self) -> None:
        """Pulse voice should generate samples."""
        voice = GBPulseVoice(voice_id=0, duty_cycle=GBDutyCycle.DUTY_50)
        samples = voice.generate_samples(440.0, 0.1, 0.5, 44100)

        assert len(samples) > 0
        assert samples.dtype == np.float32
        assert np.max(np.abs(samples)) <= 0.5

    def test_wave_generation(self) -> None:
        """Wave voice should generate samples from wavetable."""
        voice = GBWaveVoice(voice_id=2)
        samples = voice.generate_samples(220.0, 0.1, 0.5, 44100)

        assert len(samples) > 0
        assert samples.dtype == np.float32

    def test_custom_wavetable(self) -> None:
        """Should accept custom wavetable."""
        chip = GameBoyChip()
        custom_wt = [15] * 16 + [0] * 16  # Square wave
        chip.set_wavetable(custom_wt)

        assert chip.wave.wavetable == custom_wt

    def test_wavetable_presets(self) -> None:
        """Should have wavetable presets."""
        assert len(GBWaveVoice.TRIANGLE) == 32
        assert len(GBWaveVoice.SAW) == 32
        assert len(GBWaveVoice.SINE_APPROX) == 32

    def test_noise_generation(self) -> None:
        """Noise voice should generate samples."""
        voice = GBNoiseVoice(voice_id=3)
        samples = voice.generate_samples(100.0, 0.1, 0.5, 44100)

        assert len(samples) > 0
        assert samples.dtype == np.float32

    def test_render_empty(self) -> None:
        """Should handle empty render gracefully."""
        chip = GameBoyChip()
        result = chip.render(tempo=120.0)
        assert result.shape == (0, 2)

    def test_render_with_notes(self) -> None:
        """Should render notes to stereo."""
        chip = GameBoyChip()
        chip.pulse1.add_note(Note(pitch=60, duration=1.0, velocity=100))

        result = chip.render(tempo=120.0)

        assert result.shape[1] == 2  # Stereo
        assert len(result) > 0

    def test_presets(self) -> None:
        """Should have preset constructors."""
        sine_chip = GameBoyChip.with_sine_wave()
        saw_chip = GameBoyChip.with_saw_wave()

        assert sine_chip.wave.wavetable == list(GBWaveVoice.SINE_APPROX)
        assert saw_chip.wave.wavetable == list(GBWaveVoice.SAW)


class TestSIDChip:
    """Tests for Commodore 64 SID chip."""

    def test_create_chip(self) -> None:
        """Should create chip with 3 voices."""
        chip = SIDChip.create()
        assert chip.chip_type == ChipType.SID
        assert len(chip.voices) == 3

    def test_waveform_selection(self) -> None:
        """Should support multiple waveforms."""
        voice = SIDVoice(voice_id=0)

        for waveform in SIDWaveform:
            voice.waveform = waveform
            samples = voice.generate_samples(440.0, 0.05, 0.5, 44100)
            assert len(samples) > 0

    def test_pulse_width(self) -> None:
        """Pulse width should affect sound."""
        voice = SIDVoice(voice_id=0, waveform=SIDWaveform.PULSE)

        samples_25 = voice.generate_samples(440.0, 0.01, 0.5, 44100)
        voice.pulse_width = 0.75
        samples_75 = voice.generate_samples(440.0, 0.01, 0.5, 44100)

        # Different pulse widths should produce different samples
        assert not np.allclose(samples_25, samples_75)

    def test_noise_generation(self) -> None:
        """SID noise should use 23-bit LFSR."""
        voice = SIDVoice(voice_id=0, waveform=SIDWaveform.NOISE)
        samples = voice.generate_samples(1000.0, 0.1, 0.5, 44100)

        assert len(samples) > 0
        # Noise should have variation
        assert np.std(samples) > 0.1

    def test_filter_modes(self) -> None:
        """Should support all filter modes."""
        samples = np.sin(np.linspace(0, 100 * np.pi, 4410)).astype(np.float32)

        for mode in SIDFilterMode:
            filt = SIDFilter(cutoff=1000.0, resonance=0.5, mode=mode)
            output = filt.process(samples, 44100)
            assert len(output) == len(samples)

    def test_filter_revision(self) -> None:
        """6581 and 8580 should sound different."""
        samples = np.sin(np.linspace(0, 100 * np.pi, 4410)).astype(np.float32)

        filt_6581 = SIDFilter(
            cutoff=1000.0,
            resonance=0.5,
            mode=SIDFilterMode.LOWPASS,
            revision=SIDRevision.R6581,
        )
        filt_8580 = SIDFilter(
            cutoff=1000.0,
            resonance=0.5,
            mode=SIDFilterMode.LOWPASS,
            revision=SIDRevision.R8580,
        )

        out_6581 = filt_6581.process(samples.copy(), 44100)
        out_8580 = filt_8580.process(samples.copy(), 44100)

        # Revisions should process differently
        assert not np.allclose(out_6581, out_8580)

    def test_render_with_filter(self) -> None:
        """Should apply filter to voices."""
        chip = SIDChip()
        chip.voice1.add_note(Note(pitch=60, duration=1.0, velocity=100))
        chip.filter_mode = SIDFilterMode.LOWPASS
        chip.filter_cutoff = 500.0

        result = chip.render(tempo=120.0)

        assert result.shape[1] == 2
        assert len(result) > 0

    def test_presets(self) -> None:
        """Should have preset constructors."""
        lead = SIDChip.lead_preset()
        bass = SIDChip.bass_preset()
        arp = SIDChip.arpeggio_preset()

        assert lead.filter_mode == SIDFilterMode.LOWPASS
        assert bass.voice1.waveform == SIDWaveform.SAWTOOTH
        assert arp.filter_mode == SIDFilterMode.BANDPASS


class TestGenesisChip:
    """Tests for Sega Genesis YM2612 FM chip."""

    def test_create_chip(self) -> None:
        """Should create chip with 6 FM channels."""
        chip = GenesisChip.create()
        assert chip.chip_type == ChipType.GENESIS
        assert len(chip.voices) == 6

    def test_fm_voice_type(self) -> None:
        """All voices should be FM type."""
        chip = GenesisChip()
        for voice in chip.voices:
            assert voice.voice_type == VoiceType.FM

    def test_all_algorithms(self) -> None:
        """Should support all 8 FM algorithms."""
        voice = FMVoice(voice_id=0)

        for alg in FMAlgorithm:
            voice.algorithm = alg
            samples = voice.generate_samples(440.0, 0.05, 0.5, 44100)
            assert len(samples) > 0, f"Algorithm {alg} failed"

    def test_operator_settings(self) -> None:
        """Operators should affect sound."""
        voice = FMVoice(voice_id=0, algorithm=FMAlgorithm.ALG4)

        # Default settings
        samples1 = voice.generate_samples(440.0, 0.05, 0.5, 44100)

        # Modify operator
        voice.op1.multiple = 2.0
        voice.op1.total_level = 20
        samples2 = voice.generate_samples(440.0, 0.05, 0.5, 44100)

        # Should produce different output
        assert not np.allclose(samples1, samples2)

    def test_feedback(self) -> None:
        """Feedback should add harmonics."""
        voice = FMVoice(voice_id=0, algorithm=FMAlgorithm.ALG7)

        voice.op1.feedback = 0
        samples_no_fb = voice.generate_samples(440.0, 0.05, 0.5, 44100)

        voice.op1.feedback = 7
        samples_fb = voice.generate_samples(440.0, 0.05, 0.5, 44100)

        # Feedback should change the sound
        assert not np.allclose(samples_no_fb, samples_fb)

    def test_envelope(self) -> None:
        """Operator envelope should shape amplitude."""
        op = FMOperator(attack_rate=31, decay_rate=20, sustain_level=5, release_rate=15)
        env = op.generate_envelope(4410, 44100)

        assert len(env) == 4410
        # Should start at 0 and have some shape
        assert env[0] < env[100]  # Attack rises

    def test_lfo(self) -> None:
        """LFO should modulate sound."""
        chip = GenesisChip()
        chip.ch1.add_note(Note(pitch=60, duration=0.5, velocity=100))

        chip.lfo_enable = False
        _ = chip.render(tempo=120.0)  # Render without LFO

        chip.lfo_enable = True
        chip.lfo_frequency = 8.0
        chip.ch1.amplitude_mod_sensitivity = 3
        chip.ch1.clear()
        chip.ch1.add_note(Note(pitch=60, duration=0.5, velocity=100))
        result_lfo = chip.render(tempo=120.0)

        # LFO should run without error
        assert len(result_lfo) > 0

    def test_render_stereo(self) -> None:
        """Should render to stereo with panning."""
        chip = GenesisChip()
        chip.ch1.add_note(Note(pitch=60, duration=1.0, velocity=100))
        chip.pan[0] = -1.0  # Full left

        result = chip.render(tempo=120.0)

        assert result.shape[1] == 2
        # Left channel should be louder than right
        left_rms = np.sqrt(np.mean(result[:, 0] ** 2))
        right_rms = np.sqrt(np.mean(result[:, 1] ** 2))
        assert left_rms > right_rms

    def test_presets(self) -> None:
        """Should have preset constructors."""
        brass = GenesisChip.brass_preset()
        bass = GenesisChip.bass_preset()
        bell = GenesisChip.bell_preset()
        strings = GenesisChip.strings_preset()

        # Presets should have specific settings
        assert brass.ch1.algorithm == FMAlgorithm.ALG4
        assert bass.ch1.algorithm == FMAlgorithm.ALG0
        assert bell.ch1.op2.multiple == 3.5  # Inharmonic
        assert strings.lfo_enable is True


class TestChipComparison:
    """Tests comparing different chip systems."""

    def test_all_chips_render(self) -> None:
        """All chips should be able to render."""
        chips = [
            GameBoyChip.create(),
            SIDChip.create(),
            GenesisChip.create(),
        ]

        for chip in chips:
            # Add note to first voice
            chip.voices[0].add_note(Note(pitch=60, duration=0.5, velocity=100))
            result = chip.render(tempo=120.0)

            assert result.shape[1] == 2, f"{chip.name} should output stereo"
            assert len(result) > 0, f"{chip.name} should produce samples"

    def test_chips_sound_different(self) -> None:
        """Different chips should produce different sounds."""
        gb = GameBoyChip.create()
        sid = SIDChip.create()
        genesis = GenesisChip.create()

        for chip in [gb, sid, genesis]:
            chip.voices[0].add_note(Note(pitch=60, duration=0.1, velocity=100))

        gb_samples = gb.render(tempo=120.0)
        sid_samples = sid.render(tempo=120.0)
        genesis_samples = genesis.render(tempo=120.0)

        # All should be different
        min_len = min(len(gb_samples), len(sid_samples), len(genesis_samples))
        assert not np.allclose(gb_samples[:min_len], sid_samples[:min_len])
        assert not np.allclose(sid_samples[:min_len], genesis_samples[:min_len])


class TestNES2A03:
    """Tests for NES 2A03 APU chip system."""

    def test_create(self) -> None:
        """Should create NES chip with 4 voices."""
        from chiptune.chip.systems import NES2A03

        nes = NES2A03.create()

        assert len(nes.voices) == 4
        assert nes.chip_type.value == "nes"

    def test_pulse_waveform(self) -> None:
        """Pulse voice should generate pulse waves."""
        from chiptune.chip.systems import NES2A03, NESDutyCycle

        nes = NES2A03.create()
        nes.pulse1.duty_cycle = NESDutyCycle.DUTY_50

        samples = nes.pulse1.generate_samples(440.0, 0.01, 1.0, 44100)

        assert len(samples) > 0
        # Square wave should oscillate between +1 and -1
        assert np.max(samples) > 0.9
        assert np.min(samples) < -0.9

    def test_triangle_no_volume(self) -> None:
        """Triangle should always play at full volume."""
        from chiptune.chip.systems import NES2A03

        nes = NES2A03.create()

        # Triangle has no volume control
        assert nes.triangle.has_volume_control is False

        samples = nes.triangle.generate_samples(220.0, 0.01, 0.5, 44100)
        # Amplitude argument is ignored for triangle
        assert len(samples) > 0

    def test_noise_periods(self) -> None:
        """Noise should use period-based frequencies."""
        from chiptune.chip.systems import NES2A03

        nes = NES2A03.create()

        # Period 0 = highest pitch, period 15 = lowest
        high = nes.noise.generate_samples(0.0, 0.01, 1.0, 44100)
        low = nes.noise.generate_samples(15.0, 0.01, 1.0, 44100)

        # Both should produce noise
        assert len(high) > 0
        assert len(low) > 0

    def test_duty_cycles(self) -> None:
        """Different duty cycles should produce different timbres."""
        from chiptune.chip.systems import NES2A03, NESDutyCycle

        nes = NES2A03.create()

        samples_25 = []
        for duty in [
            NESDutyCycle.DUTY_12_5,
            NESDutyCycle.DUTY_25,
            NESDutyCycle.DUTY_50,
        ]:
            nes.pulse1.duty_cycle = duty
            s = nes.pulse1.generate_samples(440.0, 0.01, 1.0, 44100)
            samples_25.append(s)

        # Different duty cycles should produce different waveforms
        assert not np.allclose(samples_25[0], samples_25[1])
        assert not np.allclose(samples_25[1], samples_25[2])

    def test_render_stereo(self) -> None:
        """Should render to stereo output."""
        from chiptune.chip.systems import NES2A03

        nes = NES2A03.create()
        nes.pulse1.add_note(Note(pitch=60, duration=0.5, velocity=100))

        result = nes.render(tempo=120.0)

        assert result.shape[1] == 2
        assert len(result) > 0

    def test_presets(self) -> None:
        """Should have preset constructors."""
        from chiptune.chip.systems import NES2A03

        classic = NES2A03.create()
        famitracker = NES2A03.famitracker_style()

        assert classic.name == "NES 2A03"
        assert famitracker.name == "NES 2A03"

    def test_included_in_comparison(self) -> None:
        """NES should work alongside other chips."""
        from chiptune.chip.systems import NES2A03, GameBoyChip, SIDChip

        chips = [
            NES2A03.create(),
            GameBoyChip.create(),
            SIDChip.create(),
        ]

        for chip in chips:
            chip.voices[0].add_note(Note(pitch=60, duration=0.1, velocity=100))
            result = chip.render(tempo=120.0)
            assert result.shape[1] == 2
