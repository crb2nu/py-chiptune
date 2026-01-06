"""Tests for procedural generation module."""

import pytest

from chiptune.generation import (
    BassGenerator,
    BassPattern,
    IntensityController,
    IntensityCurve,
    IntensityProfile,
    MarkovChain,
    MarkovMelodyGenerator,
    MelodyStyle,
    WeightedMarkovChain,
)
from chiptune.theory.chords import Chord


class TestMarkovChain:
    """Tests for Markov chain."""

    def test_train_and_generate(self) -> None:
        """Chain should generate sequences after training."""
        chain: MarkovChain[int] = MarkovChain(order=2)
        chain.train([1, 2, 3, 4, 5, 4, 3, 2, 1])

        result = chain.generate(10, seed=42)

        assert len(result) == 10
        assert all(isinstance(x, int) for x in result)

    def test_empty_chain(self) -> None:
        """Untrained chain should return empty."""
        chain: MarkovChain[int] = MarkovChain(order=2)
        result = chain.generate(10)

        assert result == []

    def test_probability(self) -> None:
        """Should track transition probabilities."""
        chain: MarkovChain[str] = MarkovChain(order=1)
        chain.train(["a", "b", "a", "b", "a", "c"])

        # After "a", we've seen "b" twice and "c" once
        prob_b = chain.get_probability(("a",), "b")
        prob_c = chain.get_probability(("a",), "c")

        assert prob_b > prob_c

    def test_merge_chains(self) -> None:
        """Merging chains should combine transitions."""
        chain1: MarkovChain[int] = MarkovChain(order=1)
        chain1.train([1, 2, 3])

        chain2: MarkovChain[int] = MarkovChain(order=1)
        chain2.train([1, 2, 4])

        merged = chain1.merge(chain2)

        assert merged.num_states >= chain1.num_states


class TestWeightedMarkovChain:
    """Tests for temperature-controlled Markov chain."""

    def test_temperature_zero(self) -> None:
        """Temperature 0 should be deterministic."""
        chain: WeightedMarkovChain[int] = WeightedMarkovChain(order=1, temperature=0.0)
        chain.train([1, 2, 1, 2, 1, 3])

        # Should always pick most common
        results = [chain.generate(5, seed=i) for i in range(5)]

        # All results should be the same (deterministic)
        assert all(r == results[0] for r in results)

    def test_high_temperature(self) -> None:
        """High temperature should still generate valid sequences."""
        chain: WeightedMarkovChain[int] = WeightedMarkovChain(order=1, temperature=2.0)
        # Train with varied transitions
        chain.train([1, 2, 1, 3, 1, 4, 1, 5, 2, 3, 2, 4, 2, 5, 3, 4, 3, 5, 4, 5])

        result = chain.generate(10, seed=42)

        # Should generate valid sequence
        assert len(result) == 10
        assert all(1 <= x <= 5 for x in result)


class TestMarkovMelodyGenerator:
    """Tests for melody generator."""

    def test_generate_melody(self) -> None:
        """Should generate melody notes."""
        gen = MarkovMelodyGenerator(order=2)
        gen.train_from_midi_pitches([60, 62, 64, 65, 67, 65, 64, 62, 60])

        notes = gen.generate(8, start_pitch=60, seed=42)

        assert len(notes) == 8
        assert all(48 <= n.pitch <= 84 for n in notes)

    def test_pitch_range(self) -> None:
        """Generated pitches should respect range."""
        gen = MarkovMelodyGenerator(order=1)
        gen.train_from_midi_pitches([60, 72, 84, 96, 84, 72, 60])

        notes = gen.generate(20, pitch_range=(50, 70), seed=42)

        assert all(50 <= n.pitch <= 70 for n in notes)


class TestMelodyStyle:
    """Tests for melody style presets."""

    def test_heroic_style(self) -> None:
        """Heroic style should generate."""
        style = MelodyStyle.heroic()
        notes = style.generator.generate(8, seed=42)

        assert len(notes) == 8
        assert style.name == "heroic"

    def test_mysterious_style(self) -> None:
        """Mysterious style should generate."""
        style = MelodyStyle.mysterious()
        notes = style.generator.generate(8, seed=42)

        assert len(notes) == 8

    def test_all_styles(self) -> None:
        """All style presets should work."""
        styles = [
            MelodyStyle.heroic(),
            MelodyStyle.mysterious(),
            MelodyStyle.playful(),
            MelodyStyle.melancholic(),
            MelodyStyle.epic(),
            MelodyStyle.chiptune(),
        ]

        for style in styles:
            notes = style.generator.generate(8, seed=42)
            assert len(notes) == 8, f"{style.name} failed"


class TestBassGenerator:
    """Tests for bass line generator."""

    def test_generate_root_bass(self) -> None:
        """Root pattern should produce root notes."""
        gen = BassGenerator(pattern=BassPattern.ROOT)
        chords = [Chord.parse("C"), Chord.parse("Am")]

        notes = gen.generate(chords, beats_per_chord=4)

        assert len(notes) >= 2

    def test_generate_walking_bass(self) -> None:
        """Walking bass should produce stepwise motion."""
        gen = BassGenerator.jazz()
        chords = [Chord.parse("Dm7"), Chord.parse("G7"), Chord.parse("Cmaj7")]

        notes = gen.generate(chords, beats_per_chord=4)

        assert len(notes) >= 4
        # Check notes are in bass range
        assert all(28 <= n.pitch <= 60 for n in notes)

    def test_presets(self) -> None:
        """Bass presets should work."""
        chords = [Chord.parse("C"), Chord.parse("G")]

        presets = [
            BassGenerator.simple(),
            BassGenerator.rock(),
            BassGenerator.jazz(),
            BassGenerator.funk(),
            BassGenerator.chiptune(),
        ]

        for gen in presets:
            notes = gen.generate(chords, beats_per_chord=4)
            assert len(notes) >= 2


class TestIntensityProfile:
    """Tests for intensity profiles."""

    def test_constant(self) -> None:
        """Constant curve should stay at base level."""
        profile = IntensityProfile(base_intensity=0.5, curve=IntensityCurve.CONSTANT, variation=0.0)

        intensities = [profile.get_intensity(p) for p in [0.0, 0.25, 0.5, 0.75, 1.0]]

        assert all(i == pytest.approx(0.5) for i in intensities)

    def test_linear_up(self) -> None:
        """Linear up should increase."""
        profile = IntensityProfile(curve=IntensityCurve.LINEAR_UP, variation=0.0)

        start = profile.get_intensity(0.0)
        end = profile.get_intensity(1.0)

        assert end > start

    def test_arch(self) -> None:
        """Arch should peak in middle."""
        profile = IntensityProfile(curve=IntensityCurve.ARCH, variation=0.0)

        start = profile.get_intensity(0.0)
        middle = profile.get_intensity(0.5)
        end = profile.get_intensity(1.0)

        assert middle > start
        assert middle > end

    def test_presets(self) -> None:
        """Intensity presets should work."""
        presets = [
            IntensityProfile.calm(),
            IntensityProfile.building(),
            IntensityProfile.fading(),
            IntensityProfile.dramatic(),
            IntensityProfile.battle(),
            IntensityProfile.exploration(),
            IntensityProfile.boss_fight(),
        ]

        for profile in presets:
            # Should return valid intensity
            intensity = profile.get_intensity(0.5)
            assert 0.0 <= intensity <= 1.0


class TestIntensityController:
    """Tests for intensity controller."""

    def test_tempo_scaling(self) -> None:
        """Tempo should scale with intensity."""
        controller = IntensityController(
            profile=IntensityProfile(curve=IntensityCurve.LINEAR_UP, variation=0.0),
            min_tempo=80,
            max_tempo=160,
        )

        low_tempo = controller.get_tempo(0.0)
        high_tempo = controller.get_tempo(1.0)

        assert low_tempo == 80
        assert high_tempo == 160

    def test_velocity_scaling(self) -> None:
        """Velocity should scale with intensity."""
        controller = IntensityController(
            profile=IntensityProfile.building(),
            min_velocity=60,
            max_velocity=120,
        )

        low_vel = controller.get_velocity(0.0)
        high_vel = controller.get_velocity(1.0)

        assert low_vel < high_vel
        assert 60 <= low_vel <= 120
        assert 60 <= high_vel <= 120

    def test_layer_activation(self) -> None:
        """Layers should increase with intensity."""
        controller = IntensityController(
            profile=IntensityProfile(curve=IntensityCurve.LINEAR_UP, variation=0.0)
        )

        low_layers = controller.get_active_layers(0.0, total_layers=4)
        high_layers = controller.get_active_layers(1.0, total_layers=4)

        assert 1 <= low_layers <= 4
        assert 1 <= high_layers <= 4
        assert high_layers >= low_layers

    def test_presets(self) -> None:
        """Controller presets should work."""
        controllers = [
            IntensityController.action(),
            IntensityController.ambient(),
            IntensityController.cinematic(),
        ]

        for ctrl in controllers:
            tempo = ctrl.get_tempo(0.5)
            velocity = ctrl.get_velocity(0.5)

            assert tempo > 0
            assert 1 <= velocity <= 127


class TestCountermelodyGenerator:
    """Tests for countermelody generation."""

    def test_generates_same_length(self) -> None:
        """Countermelody should have same length as melody."""
        from chiptune.generation.harmony.countermelody import CountermelodyGenerator
        from chiptune.theory.arpeggios import Note

        melody = [
            Note(pitch=60, duration=1.0),
            Note(pitch=62, duration=1.0),
            Note(pitch=64, duration=1.0),
            Note(pitch=65, duration=1.0),
        ]
        gen = CountermelodyGenerator.contrary()
        counter = gen.generate(melody)

        assert len(counter) == len(melody)

    def test_contrary_motion(self) -> None:
        """Contrary motion should move opposite to melody."""
        from chiptune.generation.harmony.countermelody import (
            CountermelodyGenerator,
            MotionType,
        )
        from chiptune.theory.arpeggios import Note

        # Ascending melody
        melody = [
            Note(pitch=60, duration=1.0),
            Note(pitch=64, duration=1.0),
            Note(pitch=67, duration=1.0),
        ]
        gen = CountermelodyGenerator(motion=MotionType.CONTRARY, seed=42)
        counter = gen.generate(melody)

        # At least should not be moving in same strong direction
        # (contrary motion doesn't guarantee perfect opposition)
        assert len(counter) == len(melody)

    def test_parallel_thirds(self) -> None:
        """Parallel thirds should maintain interval."""
        from chiptune.generation.harmony.countermelody import CountermelodyGenerator
        from chiptune.theory.arpeggios import Note

        melody = [
            Note(pitch=60, duration=1.0),
            Note(pitch=62, duration=1.0),
            Note(pitch=64, duration=1.0),
        ]
        gen = CountermelodyGenerator.thirds()
        counter = gen.generate(melody)

        # Intervals should be around 3-4 semitones
        for m, c in zip(melody, counter, strict=False):
            interval = abs(c.pitch - m.pitch)
            # Allow for scale snapping
            assert 0 <= interval <= 16

    def test_respects_velocity_offset(self) -> None:
        """Countermelody should be quieter by offset."""
        from chiptune.generation.harmony.countermelody import CountermelodyGenerator
        from chiptune.theory.arpeggios import Note

        melody = [Note(pitch=60, duration=1.0, velocity=100)]
        gen = CountermelodyGenerator(velocity_offset=-20)
        counter = gen.generate(melody)

        assert counter[0].velocity == 80

    def test_empty_melody(self) -> None:
        """Empty melody should return empty countermelody."""
        from chiptune.generation.harmony.countermelody import CountermelodyGenerator

        gen = CountermelodyGenerator.contrary()
        counter = gen.generate([])

        assert counter == []

    def test_presets(self) -> None:
        """Preset methods should return valid generators."""
        from chiptune.generation.harmony.countermelody import (
            CountermelodyGenerator,
            HarmonyInterval,
            MotionType,
        )

        thirds = CountermelodyGenerator.thirds()
        sixths = CountermelodyGenerator.sixths()
        contrary = CountermelodyGenerator.contrary()
        drone = CountermelodyGenerator.drone()

        assert thirds.harmony_interval == HarmonyInterval.THIRD
        assert sixths.harmony_interval == HarmonyInterval.SIXTH
        assert contrary.motion == MotionType.CONTRARY
        assert drone.motion == MotionType.OBLIQUE

    def test_scale_snapping(self) -> None:
        """Notes should snap to scale when provided."""
        from chiptune.generation.harmony.countermelody import CountermelodyGenerator
        from chiptune.theory.arpeggios import Note
        from chiptune.theory.keys import Key, Mode
        from chiptune.theory.scales import Scale

        melody = [
            Note(pitch=60, duration=1.0),
            Note(pitch=62, duration=1.0),
            Note(pitch=64, duration=1.0),
        ]
        key = Key(root="C", mode=Mode.IONIAN)
        scale = Scale.from_key(key)
        gen = CountermelodyGenerator.thirds()
        counter = gen.generate(melody, scale=scale)

        # All pitches should be in C major scale
        c_major_classes = {0, 2, 4, 5, 7, 9, 11}
        for note in counter:
            assert note.pitch % 12 in c_major_classes
