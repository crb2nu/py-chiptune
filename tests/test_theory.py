"""Tests for music theory modules."""


from chiptune.theory.arpeggios import Arpeggio, ArpeggioPattern, Note
from chiptune.theory.chords import Chord, ChordProgression, ChordQuality
from chiptune.theory.keys import Key, Mode
from chiptune.theory.scales import Scale, ScaleType


class TestKey:
    """Tests for Key class."""

    def test_create_major_key(self) -> None:
        key = Key(root="C", mode=Mode.IONIAN)
        assert key.root == "C"
        assert key.mode == Mode.IONIAN
        assert key.root_midi == 60

    def test_create_minor_key(self) -> None:
        key = Key(root="A", mode=Mode.AEOLIAN)
        assert key.root == "A"
        assert key.mode == Mode.AEOLIAN
        assert key.root_midi == 69

    def test_from_emotion_heroic(self) -> None:
        key = Key.from_emotion("heroic")
        assert key.mode == Mode.IONIAN

    def test_from_emotion_mysterious(self) -> None:
        key = Key.from_emotion("mysterious")
        assert key.mode == Mode.DORIAN

    def test_from_emotion_danger(self) -> None:
        key = Key.from_emotion("danger")
        assert key.mode == Mode.LOCRIAN

    def test_transpose(self) -> None:
        key = Key(root="C", mode=Mode.IONIAN)
        transposed = key.transpose(5)  # Up a fourth
        assert transposed.root == "F"
        assert transposed.mode == Mode.IONIAN

    def test_get_scale_pitches(self) -> None:
        key = Key(root="C", mode=Mode.IONIAN)
        pitches = key.get_scale_pitches(octave=4)
        assert pitches[0] == 60  # C4
        assert len(pitches) == 8  # Includes octave


class TestScale:
    """Tests for Scale class."""

    def test_major_scale(self) -> None:
        scale = Scale(root="C", scale_type=ScaleType.MAJOR)
        pitches = scale.get_pitches(octave=4, num_octaves=1)
        assert pitches[0] == 60  # C4
        assert len(pitches) == 8  # Includes octave

    def test_pentatonic_scale(self) -> None:
        scale = Scale(root="C", scale_type=ScaleType.PENTATONIC_MAJOR)
        pitches = scale.get_pitches(octave=4, num_octaves=1)
        # Pentatonic has 5 notes per octave plus the octave
        assert len(pitches) == 6

    def test_from_emotion(self) -> None:
        scale = Scale.from_emotion("peaceful")
        assert scale.scale_type == ScaleType.PENTATONIC_MAJOR

    def test_degree_to_pitch(self) -> None:
        scale = Scale(root="C", scale_type=ScaleType.MAJOR)
        assert scale.degree_to_pitch(1, octave=4) == 60  # C4
        assert scale.degree_to_pitch(3, octave=4) == 64  # E4
        assert scale.degree_to_pitch(5, octave=4) == 67  # G4

    def test_pitch_in_scale(self) -> None:
        scale = Scale(root="C", scale_type=ScaleType.MAJOR)
        assert scale.pitch_in_scale(60)  # C
        assert scale.pitch_in_scale(62)  # D
        assert not scale.pitch_in_scale(61)  # C#


class TestChord:
    """Tests for Chord class."""

    def test_major_chord(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        pitches = chord.get_pitches(octave=4)
        assert 60 in pitches  # C
        assert 64 in pitches  # E
        assert 67 in pitches  # G

    def test_minor_chord(self) -> None:
        chord = Chord(root="A", quality=ChordQuality.MINOR)
        pitches = chord.get_pitches(octave=4)
        assert 69 in pitches  # A
        assert 72 in pitches  # C
        assert 76 in pitches  # E

    def test_parse_chord(self) -> None:
        chord = Chord.parse("Cm")
        assert chord.root == "C"
        assert chord.quality == ChordQuality.MINOR

    def test_parse_chord_with_accidental(self) -> None:
        chord = Chord.parse("F#m7")
        assert chord.root == "F#"
        assert chord.quality == ChordQuality.MINOR_7

    def test_transpose(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        transposed = chord.transpose(5)
        assert transposed.root == "F"


class TestChordProgression:
    """Tests for ChordProgression class."""

    def test_from_preset(self) -> None:
        prog = ChordProgression.from_preset("victory")
        assert prog.numerals == ["I", "IV", "V", "I"]

    def test_get_chords(self) -> None:
        key = Key(root="C", mode=Mode.IONIAN)
        prog = ChordProgression(key=key, numerals=["I", "IV", "V", "I"])
        chords = prog.get_chords()
        assert len(chords) == 4
        assert chords[0].root == "C"
        assert chords[1].root == "F"
        assert chords[2].root == "G"

    def test_repeat(self) -> None:
        key = Key(root="C", mode=Mode.IONIAN)
        prog = ChordProgression(key=key, numerals=["I", "V"])
        repeated = prog.repeat(2)
        assert repeated.numerals == ["I", "V", "I", "V"]


class TestArpeggio:
    """Tests for Arpeggio class."""

    def test_from_chord(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        arp = Arpeggio.from_chord(chord, octave=4)
        notes = arp.to_notes()
        assert len(notes) == 3
        assert notes[0].pitch == 60  # C

    def test_pattern_up(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        arp = Arpeggio.from_chord(chord, octave=4, pattern=ArpeggioPattern.UP)
        notes = arp.to_notes()
        pitches = [n.pitch for n in notes]
        assert pitches == sorted(pitches)

    def test_pattern_down(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        arp = Arpeggio.from_chord(chord, octave=4, pattern=ArpeggioPattern.DOWN)
        notes = arp.to_notes()
        pitches = [n.pitch for n in notes]
        assert pitches == sorted(pitches, reverse=True)

    def test_fill_duration(self) -> None:
        chord = Chord(root="C", quality=ChordQuality.MAJOR)
        arp = Arpeggio.from_chord(chord, octave=4, note_duration=0.25)
        notes = arp.fill_duration(4.0)  # 4 beats
        total_duration = sum(n.duration for n in notes)
        assert total_duration <= 4.0


class TestNote:
    """Tests for Note class."""

    def test_create_note(self) -> None:
        note = Note(pitch=60, duration=1.0, velocity=100)
        assert note.pitch == 60
        assert note.duration == 1.0
        assert note.velocity == 100

    def test_transpose_note(self) -> None:
        note = Note(pitch=60, duration=1.0)
        transposed = note.transpose(12)  # Up an octave
        assert transposed.pitch == 72
