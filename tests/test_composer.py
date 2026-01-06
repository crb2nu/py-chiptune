"""Tests for composer modules."""

from chiptune.composer.agent_api import MusicAgent
from chiptune.composer.composer import BassStyle, ChiptuneComposer, DrumStyle, Track
from chiptune.patterns.jingles import Jingle, JingleType
from chiptune.patterns.progressions import ProgressionBuilder, ProgressionMood
from chiptune.patterns.themes import GameTheme, MelodicContour, ThemeTemplate
from chiptune.theory.keys import Mode


class TestChiptuneComposer:
    """Tests for ChiptuneComposer class."""

    def test_create_composer(self) -> None:
        composer = ChiptuneComposer.create(bpm=120, root="C", mode="major")
        assert composer.bpm == 120
        assert composer.key.root == "C"
        assert composer.key.mode == Mode.IONIAN

    def test_set_mood_heroic(self) -> None:
        composer = ChiptuneComposer.create()
        composer.set_mood("heroic")
        assert composer.key.mode == Mode.IONIAN
        assert composer.bpm > 120  # Heroic speeds up tempo

    def test_set_theme(self) -> None:
        composer = ChiptuneComposer.create()
        composer.set_theme(GameTheme.BATTLE)
        assert composer.theme == GameTheme.BATTLE
        assert composer.progression is not None

    def test_add_melody(self) -> None:
        composer = ChiptuneComposer.create()
        composer.add_melody(contour=MelodicContour.ARCH, length_bars=4)
        assert len(composer.parts) == 1
        assert composer.parts[0].notes

    def test_add_bass(self) -> None:
        composer = ChiptuneComposer.create()
        composer.add_bass(style=BassStyle.ROOT)
        assert len(composer.parts) == 1
        assert composer.parts[0].notes

    def test_add_drums(self) -> None:
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=4)
        composer.add_drums(pattern=DrumStyle.BASIC)
        assert len(composer.parts) == 2

    def test_build_track(self) -> None:
        composer = ChiptuneComposer.create(bpm=140, root="G")
        composer.add_melody(length_bars=4)
        composer.add_bass()
        track = composer.build()
        assert isinstance(track, Track)
        assert track.bpm == 140
        assert track.key.root == "G"

    def test_fluent_api(self) -> None:
        composer = (
            ChiptuneComposer.create(bpm=120)
            .set_mood("heroic")
            .add_melody(length_bars=8)
            .add_bass()
            .add_drums()
        )
        assert len(composer.parts) == 3

    def test_to_midi_bytes(self) -> None:
        composer = ChiptuneComposer.create()
        composer.add_melody(length_bars=4)
        midi_bytes = composer.to_midi_bytes()
        assert isinstance(midi_bytes, bytes)
        assert len(midi_bytes) > 0
        # Check MIDI header
        assert midi_bytes[:4] == b"MThd"


class TestMusicAgent:
    """Tests for MusicAgent semantic API."""

    def test_compose_for_context_battle(self) -> None:
        agent = MusicAgent()
        midi = agent.compose_for_context("player enters battle", duration_seconds=10)
        assert isinstance(midi, bytes)
        assert len(midi) > 0

    def test_compose_for_context_peaceful(self) -> None:
        agent = MusicAgent()
        midi = agent.compose_for_context("relaxing in the village", intensity=0.2)
        assert isinstance(midi, bytes)

    def test_generate_sfx_coin(self) -> None:
        agent = MusicAgent()
        midi = agent.generate_sfx("coin_collect")
        assert isinstance(midi, bytes)
        assert len(midi) > 0

    def test_generate_sfx_level_up(self) -> None:
        agent = MusicAgent()
        midi = agent.generate_sfx("level_up")
        assert isinstance(midi, bytes)

    def test_compose_loop(self) -> None:
        agent = MusicAgent()
        midi = agent.compose_loop(mood="heroic", bars=8)
        assert isinstance(midi, bytes)

    def test_list_themes(self) -> None:
        themes = MusicAgent.list_themes()
        assert "battle" in themes
        assert "victory" in themes

    def test_list_moods(self) -> None:
        moods = MusicAgent.list_moods()
        assert "heroic" in moods
        assert "peaceful" in moods


class TestThemeTemplate:
    """Tests for ThemeTemplate class."""

    def test_for_theme_battle(self) -> None:
        template = ThemeTemplate.for_theme(GameTheme.BATTLE)
        assert template.tempo == 150
        assert template.intensity == 0.8

    def test_for_theme_peaceful(self) -> None:
        template = ThemeTemplate.for_theme(GameTheme.SHOP)
        assert template.tempo == 100
        assert template.intensity == 0.4

    def test_with_intensity(self) -> None:
        template = ThemeTemplate.for_theme(GameTheme.BATTLE)
        adjusted = template.with_intensity(0.3)  # Lower intensity slows tempo
        assert adjusted.intensity == 0.3
        # Tempo adjusts based on intensity difference from 0.5 baseline
        assert adjusted.tempo < template.tempo

    def test_transpose(self) -> None:
        template = ThemeTemplate.for_theme(GameTheme.VICTORY, root="C")
        transposed = template.transpose(5)
        assert transposed.key.root == "F"


class TestJingle:
    """Tests for Jingle class."""

    def test_create_victory_fanfare(self) -> None:
        jingle = Jingle.victory_fanfare()
        assert jingle.jingle_type == JingleType.VICTORY_FANFARE
        assert len(jingle.notes) > 0

    def test_create_item_get(self) -> None:
        jingle = Jingle.item_get()
        assert jingle.jingle_type == JingleType.ITEM_GET
        assert len(jingle.notes) > 0

    def test_transpose_jingle(self) -> None:
        jingle = Jingle.coin_collect(root="C")
        transposed = jingle.transpose(5)
        assert transposed.key.root == "F"

    def test_duration_beats(self) -> None:
        jingle = Jingle.victory_fanfare()
        assert jingle.duration_beats > 0

    def test_duration_seconds(self) -> None:
        jingle = Jingle.victory_fanfare(tempo=120)
        assert jingle.duration_seconds > 0


class TestProgressionBuilder:
    """Tests for ProgressionBuilder class."""

    def test_from_mood(self) -> None:
        builder = ProgressionBuilder.from_mood(ProgressionMood.TRIUMPHANT)
        assert builder.numerals == ["I", "IV", "V", "I"]

    def test_for_context(self) -> None:
        builder = ProgressionBuilder.for_context("battle")
        assert "i" in builder.numerals  # Minor chord

    def test_add_chords(self) -> None:
        builder = ProgressionBuilder.in_key("C", Mode.IONIAN)
        builder = builder.add("I", 4).add("IV", 4).add("V", 4).add("I", 4)
        assert builder.numerals == ["I", "IV", "V", "I"]
        assert builder.total_beats == 16

    def test_build(self) -> None:
        builder = ProgressionBuilder.from_mood(ProgressionMood.HEROIC)
        progression = builder.build()
        chords = progression.get_chords()
        assert len(chords) == 4
