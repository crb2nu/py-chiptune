"""Command-line interface for py-chiptune.

Provides commands for generating chiptune music and sound effects
from the terminal.

Usage:
    chiptune generate --preset battle --output battle.wav
    chiptune sfx explosion --output explosion.mid
    chiptune list presets
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace


GENRE_PRESET_METHODS: dict[str, str] = {
    "battle": "battle_theme",
    "overworld": "overworld",
    "dungeon": "dungeon",
    "victory": "victory_fanfare",
    "title": "title_screen",
    "shop": "shop_theme",
    "sad": "sad_scene",
    "chase": "chase_scene",
}

GENRE_PRESET_ITEMS: list[tuple[str, str]] = [
    ("battle", "Intense battle/boss fight music (A minor, 165 BPM)"),
    ("overworld", "Adventurous exploration theme (C major, 120 BPM)"),
    ("dungeon", "Dark, mysterious atmosphere (E dorian, 85 BPM)"),
    ("victory", "Short victory fanfare (C lydian, 140 BPM)"),
    ("title", "Catchy title screen music (F major, 130 BPM)"),
    ("shop", "Cheerful shop/menu music (G mixolydian, 115 BPM)"),
    ("sad", "Emotional, melancholic scene (D minor, 70 BPM)"),
    ("chase", "Fast-paced action music (E phrygian, 185 BPM)"),
]

EFFECT_PRESET_METHODS: dict[str, str] = {
    "clean": "clean",
    "retro": "retro_gaming",
    "space": "space_adventure",
    "lofi": "lo_fi_nostalgia",
    "arcade": "arcade_cabinet",
    "dreamy": "dreamy",
    "dungeon": "dungeon_reverb",
    "boss": "boss_battle",
}

EFFECT_PRESET_ITEMS: list[tuple[str, str]] = [
    ("clean", "No effects - dry signal"),
    ("retro", "Classic retro gaming (subtle chorus + echo)"),
    ("space", "Sci-fi atmosphere (lush chorus + space delay)"),
    ("lofi", "Lo-fi nostalgia (tape delay + tremolo)"),
    ("arcade", "Bright arcade sound (chorus + slapback)"),
    ("dreamy", "Ethereal floating feel (heavy effects)"),
    ("dungeon", "Cavernous reverb atmosphere"),
    ("boss", "Punchy minimal effects for clarity"),
]

SFX_METHODS: dict[str, str] = {
    "jump": "jump",
    "land": "land",
    "coin": "coin_collect",
    "powerup": "powerup",
    "damage": "damage",
    "explosion": "explosion",
    "laser": "laser",
    "shield": "shield",
    "teleport": "teleport",
    "menu_select": "menu_select",
    "menu_confirm": "menu_confirm",
    "menu_back": "menu_back",
    "success": "success",
    "error": "error",
    "door_open": "door_open",
    "door_close": "door_close",
    "heartbeat": "heartbeat",
    "countdown": "countdown_tick",
    "countdown_final": "countdown_final",
}

SFX_ITEMS: list[tuple[str, str]] = [
    ("jump", "Character jump sound"),
    ("land", "Landing thud"),
    ("coin", "Coin/pickup collect"),
    ("powerup", "Power-up acquisition"),
    ("damage", "Take damage/hit"),
    ("explosion", "Explosion effect"),
    ("laser", "Laser/projectile fire"),
    ("shield", "Shield activation"),
    ("teleport", "Teleport effect"),
    ("menu_select", "Menu selection"),
    ("menu_confirm", "Menu confirm action"),
    ("menu_back", "Menu back/cancel"),
    ("success", "Success/achievement"),
    ("error", "Error/invalid action"),
    ("door_open", "Door opening"),
    ("door_close", "Door closing"),
    ("heartbeat", "Heartbeat/tension"),
    ("countdown", "Countdown tick"),
    ("countdown_final", "Final countdown stinger"),
]


def get_version() -> str:
    """Return the installed distribution version, with a source-tree fallback."""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:
        PackageNotFoundError = Exception  # type: ignore[assignment]
        version = None  # type: ignore[assignment]

    if version is not None:
        try:
            return version("flexinfer-chiptune")
        except PackageNotFoundError:
            pass

    try:
        from chiptune._version import __version__

        return __version__
    except Exception:
        return "unknown"


def _infer_format_from_path(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in {".mid", ".midi"}:
        return "midi"
    if suffix in {".wav"}:
        return "wav"
    return None


def _ensure_parent_dir(path: Path) -> None:
    parent = path.parent
    if str(parent) not in {"", "."}:
        parent.mkdir(parents=True, exist_ok=True)


def _as_json_items(items: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"name": name, "description": desc} for name, desc in items]


def _resolve_generate_output(format_opt: str | None, output: Path | None) -> tuple[bool, str, Path]:
    format_was_explicit = format_opt is not None
    resolved_format = format_opt

    if resolved_format is None:
        if output is not None:
            inferred = _infer_format_from_path(output)
            resolved_format = inferred if inferred is not None else "wav"
        else:
            resolved_format = "wav"

    if output is None:
        output_path = Path("output.mid") if resolved_format == "midi" else Path("output.wav")
    else:
        output_path = output
    if output_path.suffix == "":
        output_path = output_path.with_suffix(".mid" if resolved_format == "midi" else ".wav")

    return format_was_explicit, resolved_format, output_path


def _build_track(args: Namespace):
    from chiptune.presets import GenrePresets

    preset_method = GENRE_PRESET_METHODS[args.preset]
    preset_factory = getattr(GenrePresets, preset_method)
    composer = preset_factory(root=args.root) if args.root else preset_factory()

    if args.bpm:
        composer.bpm = args.bpm

    composer.add_melody(length_bars=args.bars)

    if not args.no_counter:
        composer.add_countermelody()

    if not args.no_bass:
        composer.add_bass()

    if not args.no_drums and args.preset not in ["sad", "victory"]:
        composer.add_drums()

    return composer.build()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="chiptune",
        description="Generate retro 8-bit/16-bit style music and sound effects.",
        epilog=(
            "Examples:\n"
            "  chiptune generate --preset battle --output battle.wav\n"
            "  chiptune generate --preset overworld --format midi --output overworld.mid\n"
            "  chiptune generate --preset battle --play --no-save\n"
            "  chiptune sfx coin --output coin.mid\n"
            "  chiptune list all\n"
            "  chiptune list --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full exception tracebacks on errors",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate chiptune music",
        description="Generate music using genre presets or custom settings.",
    )
    gen_parser.add_argument(
        "--preset",
        "-p",
        choices=[name for name, _ in GENRE_PRESET_ITEMS],
        default="overworld",
        help="Genre preset (default: overworld)",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output file path (default: output.wav / output.mid)",
    )
    gen_parser.add_argument(
        "--bars",
        "-b",
        type=int,
        default=8,
        help="Length in bars (default: 8)",
    )
    gen_parser.add_argument(
        "--root",
        "-r",
        default=None,
        help="Root note (e.g., C, A, F#). Overrides preset default.",
    )
    gen_parser.add_argument(
        "--bpm",
        type=int,
        default=None,
        help="Tempo in BPM. Overrides preset default.",
    )
    gen_parser.add_argument(
        "--effects",
        "-e",
        choices=[name for name, _ in EFFECT_PRESET_ITEMS],
        default="retro",
        help="Effect preset (default: retro)",
    )
    gen_parser.add_argument(
        "--no-drums",
        action="store_true",
        help="Exclude drums from the track",
    )
    gen_parser.add_argument(
        "--no-bass",
        action="store_true",
        help="Exclude bass from the track",
    )
    gen_parser.add_argument(
        "--no-counter",
        action="store_true",
        help="Exclude countermelody from the track",
    )
    gen_parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    gen_parser.add_argument(
        "--format",
        "-f",
        choices=["wav", "midi"],
        default=None,
        help="Output format (default: inferred from --output, else wav)",
    )
    gen_parser.add_argument(
        "--play",
        action="store_true",
        help="Play the generated audio (requires optional 'audio' extras)",
    )
    gen_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write an output file (useful with --play)",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # SFX command
    sfx_parser = subparsers.add_parser(
        "sfx",
        help="Generate sound effects",
        description="Generate retro game sound effects as MIDI.",
    )
    sfx_parser.add_argument(
        "type",
        choices=[name for name, _ in SFX_ITEMS],
        help="Type of sound effect to generate",
    )
    sfx_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output file path (default: <type>.mid)",
    )
    sfx_parser.set_defaults(func=cmd_sfx)

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available presets and options",
        description="Display available presets, effects, and sound effect types.",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    list_parser.add_argument(
        "category",
        nargs="?",
        choices=["presets", "effects", "sfx", "all"],
        default="all",
        help="Category to list (default: all)",
    )
    list_parser.set_defaults(func=cmd_list)

    return parser


def cmd_generate(args: Namespace) -> int:
    """Execute the generate command."""
    import random

    # Set seed if provided
    if args.seed is not None:
        random.seed(args.seed)

    format_was_explicit, resolved_format, output_path = _resolve_generate_output(
        args.format, args.output
    )
    if format_was_explicit and args.output is not None:
        inferred = _infer_format_from_path(args.output)
        if inferred is not None and inferred != resolved_format:
            raise ValueError(
                f"--format {resolved_format} conflicts with --output extension {args.output.suffix}"
            )

    if not args.no_save:
        _ensure_parent_dir(output_path)

    track = _build_track(args)

    needs_audio = args.play or (not args.no_save and resolved_format == "wav")
    effects = None
    rendered_audio = None

    if needs_audio:
        from chiptune.output.audio import AudioExporter, AudioPlayer
        from chiptune.presets import EffectPresets

        audio_exporter = AudioExporter()
        if args.effects:
            effect_method = EFFECT_PRESET_METHODS[args.effects]
            effects = getattr(EffectPresets, effect_method)()

        if args.play:
            if not AudioPlayer.is_available():
                raise ImportError(
                    "Audio playback requires optional dependencies. Install with: "
                    "pip install 'flexinfer-chiptune[audio]'"
                )
            rendered_audio = audio_exporter.render_track(track, effects=effects)
            AudioPlayer().play(rendered_audio)

    if args.no_save:
        return 0

    if resolved_format == "midi":
        from chiptune.output.midi import MidiExporter

        midi_exporter = MidiExporter()
        midi_exporter.export_file(track, str(output_path))
        print(f"Exported MIDI to: {output_path}")
        return 0

    from chiptune.output.audio import AudioExporter

    audio_exporter = AudioExporter()
    if rendered_audio is not None:
        import soundfile as sf

        sf.write(str(output_path), rendered_audio, audio_exporter.sample_rate, subtype="PCM_16")
    else:
        audio_exporter.export_wav(track, str(output_path), effects=effects)

    print(f"Exported WAV to: {output_path}")

    return 0


def cmd_sfx(args: Namespace) -> int:
    """Execute the sfx command."""
    from chiptune.sfx.effects import SFXGenerator

    sfx = SFXGenerator()

    output_path: Path = args.output or Path(f"{args.type}.mid")
    if output_path.suffix == "":
        output_path = output_path.with_suffix(".mid")

    _ensure_parent_dir(output_path)

    method_name = SFX_METHODS[args.type]
    generator_method = getattr(sfx, method_name)

    # Generate MIDI bytes
    midi_bytes = generator_method()

    # Save to file
    sfx.save(midi_bytes, str(output_path))

    print(f"Exported {args.type} SFX to: {output_path}")
    return 0


def cmd_list(args: Namespace) -> int:
    """Execute the list command."""
    category = args.category

    if args.json:
        payload: dict[str, object] = {}
        if category in ("presets", "all"):
            payload["presets"] = _as_json_items(GENRE_PRESET_ITEMS)
        if category in ("effects", "all"):
            payload["effects"] = _as_json_items(EFFECT_PRESET_ITEMS)
        if category in ("sfx", "all"):
            payload["sfx"] = _as_json_items(SFX_ITEMS)

        print(json.dumps(payload, indent=2))
        return 0

    if category in ("presets", "all"):
        print("\nGenre Presets:")
        print("-" * 40)
        for name, desc in GENRE_PRESET_ITEMS:
            print(f"  {name:12} {desc}")

    if category in ("effects", "all"):
        print("\nEffect Presets:")
        print("-" * 40)
        for name, desc in EFFECT_PRESET_ITEMS:
            print(f"  {name:12} {desc}")

    if category in ("sfx", "all"):
        print("\nSound Effects (outputs MIDI):")
        print("-" * 40)
        for name, desc in SFX_ITEMS:
            print(f"  {name:14} {desc}")

    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        return code

    if args.command is None:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except Exception as e:
        if getattr(args, "debug", False):
            raise
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
