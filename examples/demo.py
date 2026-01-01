#!/usr/bin/env python3
"""Demo script showing py-chiptune capabilities.

Run this script to generate example MIDI files in the examples/ directory.
"""

from pathlib import Path

from chiptune import ChiptuneComposer, MusicAgent, Jingle, SFXGenerator
from chiptune.patterns.themes import GameTheme, MelodicContour
from chiptune.patterns.progressions import ProgressionBuilder, ProgressionMood
from chiptune.composer.composer import BassStyle, DrumStyle

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def demo_composer() -> None:
    """Demonstrate the ChiptuneComposer API."""
    print("=== ChiptuneComposer Demo ===\n")

    # Create a heroic battle theme
    print("Creating battle theme...")
    composer = (
        ChiptuneComposer.create(bpm=150, root="A", mode="minor")
        .set_theme(GameTheme.BATTLE)
        .add_melody(contour=MelodicContour.ASCENDING, length_bars=8)
        .add_bass(style=BassStyle.OCTAVE)
        .add_arpeggio_layer()
        .add_drums(pattern=DrumStyle.DRIVING)
    )
    composer.export_midi(str(OUTPUT_DIR / "battle_theme.mid"))
    print(f"  Saved: {OUTPUT_DIR / 'battle_theme.mid'}")

    # Create a peaceful overworld theme
    print("Creating overworld theme...")
    composer = (
        ChiptuneComposer.create(bpm=100, root="C", mode="major")
        .set_mood("peaceful")
        .add_melody(contour=MelodicContour.WAVE, length_bars=8)
        .add_bass(style=BassStyle.ROOT)
        .add_drums(pattern=DrumStyle.SPARSE)
    )
    composer.export_midi(str(OUTPUT_DIR / "overworld_theme.mid"))
    print(f"  Saved: {OUTPUT_DIR / 'overworld_theme.mid'}")

    # Create a boss theme
    print("Creating boss theme...")
    composer = (
        ChiptuneComposer.create(bpm=140, root="E", mode="phrygian")
        .set_theme(GameTheme.BOSS)
        .add_melody(contour=MelodicContour.PEAK, length_bars=8)
        .add_bass(style=BassStyle.WALKING)
        .add_arpeggio_layer()
        .add_drums(pattern=DrumStyle.DRIVING)
    )
    composer.export_midi(str(OUTPUT_DIR / "boss_theme.mid"))
    print(f"  Saved: {OUTPUT_DIR / 'boss_theme.mid'}")


def demo_agent_api() -> None:
    """Demonstrate the MusicAgent semantic API."""
    print("\n=== MusicAgent Demo ===\n")

    agent = MusicAgent()

    # Generate music from context descriptions
    contexts = [
        ("player enters the dark dungeon", "dungeon_music.mid"),
        ("shopping at the village merchant", "shop_music.mid"),
        ("victory celebration after boss defeat", "victory_music.mid"),
    ]

    for context, filename in contexts:
        print(f"Generating music for: '{context}'")
        midi_bytes = agent.compose_for_context(
            context=context,
            duration_seconds=20.0,
            intensity=0.6,
        )
        with open(OUTPUT_DIR / filename, "wb") as f:
            f.write(midi_bytes)
        print(f"  Saved: {OUTPUT_DIR / filename}")


def demo_jingles() -> None:
    """Demonstrate jingle generation."""
    print("\n=== Jingles Demo ===\n")

    from chiptune.output.midi import MidiExporter

    exporter = MidiExporter()

    jingles = [
        (Jingle.victory_fanfare(root="C", tempo=140), "jingle_victory.mid"),
        (Jingle.item_get(root="C", tempo=160), "jingle_item.mid"),
        (Jingle.level_up(root="C", tempo=150), "jingle_levelup.mid"),
        (Jingle.coin_collect(root="C", tempo=180), "jingle_coin.mid"),
        (Jingle.game_over(root="A", tempo=70), "jingle_gameover.mid"),
    ]

    for jingle, filename in jingles:
        print(f"Creating {jingle.jingle_type.value} jingle...")
        exporter.export_jingle_file(jingle, str(OUTPUT_DIR / filename))
        print(f"  Saved: {OUTPUT_DIR / filename}")


def demo_sfx() -> None:
    """Demonstrate sound effect generation."""
    print("\n=== Sound Effects Demo ===\n")

    sfx = SFXGenerator()

    effects = [
        ("coin_collect", sfx.coin_collect()),
        ("jump", sfx.jump()),
        ("explosion", sfx.explosion()),
        ("powerup", sfx.powerup()),
        ("damage", sfx.damage()),
        ("menu_select", sfx.menu_select()),
        ("menu_confirm", sfx.menu_confirm()),
        ("laser", sfx.laser()),
        ("teleport", sfx.teleport()),
    ]

    for name, midi_bytes in effects:
        filename = f"sfx_{name}.mid"
        print(f"Creating {name} sound effect...")
        sfx.save(midi_bytes, str(OUTPUT_DIR / filename))
        print(f"  Saved: {OUTPUT_DIR / filename}")


def demo_progressions() -> None:
    """Demonstrate chord progression building."""
    print("\n=== Progression Builder Demo ===\n")

    from chiptune.theory.keys import Mode

    # Build a custom progression
    print("Building custom epic progression...")
    builder = (
        ProgressionBuilder.in_key("D", Mode.AEOLIAN)  # D minor
        .add("i", 4)
        .add("bVII", 4)
        .add("bVI", 4)
        .add("V", 4)
    )
    progression = builder.build()
    chords = progression.get_chords()
    print(f"  Chords: {[c.root for c in chords]}")
    print(f"  Numerals: {builder.numerals}")

    # Use preset moods
    for mood in [ProgressionMood.TRIUMPHANT, ProgressionMood.MYSTERIOUS]:
        builder = ProgressionBuilder.from_mood(mood, root="C")
        print(f"  {mood.value}: {builder.numerals}")


def main() -> None:
    """Run all demos."""
    print("py-chiptune Demo")
    print("=" * 50)

    demo_composer()
    demo_agent_api()
    demo_jingles()
    demo_sfx()
    demo_progressions()

    print("\n" + "=" * 50)
    print(f"All files saved to: {OUTPUT_DIR}")
    print("\nPlay the MIDI files with any DAW or MIDI player!")
    print("For best results, use a chiptune/8-bit synth plugin.")


if __name__ == "__main__":
    main()
