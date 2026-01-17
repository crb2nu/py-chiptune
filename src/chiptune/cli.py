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
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace


class _ChiptuneHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


GENRE_PRESET_METHODS: dict[str, str] = {
    "battle": "battle_theme",
    "overworld": "overworld",
    "dungeon": "dungeon",
    "toon": "toon_theme",
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
    ("toon", "Cartoon bouncy theme (C mixolydian, 150 BPM)"),
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
    "toon": "toon_cartoon",
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
    ("toon", "Cartoon wobble + slapback"),
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


def _write_metadata(path: Path, payload: object) -> None:
    _ensure_parent_dir(path)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_metadata_jsonl(path: Path, payloads: list[dict[str, object]]) -> None:
    _ensure_parent_dir(path)
    lines = [json.dumps(payload, separators=(",", ":")) for payload in payloads]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _toml_quote_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace('"', '\\"')
    )
    return f'"{escaped}"'


def _toml_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return _toml_quote_string(key)


def _toml_scalar(value: object) -> str:
    import math

    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return _toml_quote_string("NaN")
        if math.isinf(value) and value > 0:
            return _toml_quote_string("Infinity")
        if math.isinf(value) and value < 0:
            return _toml_quote_string("-Infinity")
        return repr(value)
    if isinstance(value, str):
        return _toml_quote_string(value)
    raise TypeError(f"Unsupported TOML scalar: {type(value)!r}")


def _toml_is_scalar(value: object) -> bool:
    return isinstance(value, (str, int, float, bool))


def _toml_dump(root: object, *, array_key: str = "items") -> str:
    if root is None:
        return ""

    if isinstance(root, list):
        return _toml_dump({array_key: root})

    if not isinstance(root, dict):
        raise TypeError("TOML output requires a dict (or list of dicts).")

    lines: list[str] = []

    def emit_kv(prefix: list[str], data: dict[str, object]) -> None:
        scalar_items: list[tuple[str, str]] = []
        dict_items: list[tuple[str, dict[str, object]]] = []
        list_table_items: list[tuple[str, list[dict[str, object]]]] = []

        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                dict_items.append((key, value))
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                list_table_items.append((key, value))  # type: ignore[arg-type]
            elif isinstance(value, list) and all(_toml_is_scalar(item) for item in value):
                rendered = ", ".join(_toml_scalar(item) for item in value)  # type: ignore[arg-type]
                scalar_items.append((key, f"[{rendered}]"))
            elif _toml_is_scalar(value):
                scalar_items.append((key, _toml_scalar(value)))
            else:
                scalar_items.append((key, _toml_quote_string(str(value))))

        for key, rendered in scalar_items:
            lines.append(f"{_toml_key(key)} = {rendered}")

        for key, tables in list_table_items:
            for table in tables:
                header = ".".join([_toml_key(p) for p in prefix] + [_toml_key(key)])
                lines.append(f"[[{header}]]")
                emit_kv([*prefix, key], table)

        for key, sub in dict_items:
            header = ".".join([_toml_key(p) for p in prefix] + [_toml_key(key)])
            lines.append(f"[{header}]")
            emit_kv([*prefix, key], sub)

    emit_kv([], root)
    return "\n".join(lines) + ("\n" if lines else "")


def _file_artifact(path: Path) -> dict[str, object]:
    import hashlib

    hasher = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            hasher.update(chunk)

    return {"path": str(path), "bytes": size_bytes, "sha256": hasher.hexdigest()}


def _as_json_items(items: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"name": name, "description": desc} for name, desc in items]


def _check_format_output_conflict(
    format_was_explicit: bool, output: Path | None, resolved_format: str
) -> None:
    if not format_was_explicit or output is None:
        return

    inferred = _infer_format_from_path(output)
    if inferred is not None and inferred != resolved_format:
        raise ValueError(
            f"--format {resolved_format} conflicts with --output extension {output.suffix}"
        )


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


def _resolve_sfx_output(
    format_opt: str | None, output: Path | None, sfx_type: str
) -> tuple[bool, str, Path]:
    format_was_explicit = format_opt is not None
    resolved_format = format_opt

    if resolved_format is None:
        inferred = _infer_format_from_path(output) if output is not None else None
        resolved_format = inferred if inferred is not None else "midi"

    if output is None:
        output_path = (
            Path(f"{sfx_type}.mid") if resolved_format == "midi" else Path(f"{sfx_type}.wav")
        )
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


def _generate_json_payload(
    args: Namespace,
    *,
    seed: int,
    resolved_format: str,
    output: str | None,
    saved: bool,
    played: bool,
    artifact: dict[str, object] | None,
    track_name: str,
    track_bpm: int,
    track_time_signature: tuple[int, int],
    track_key_root: str,
    track_key_mode: str,
    track_length_beats: float,
    track_duration_seconds: float,
) -> dict[str, object]:
    return {
        "program": "chiptune",
        "version": get_version(),
        "schema": 1,
        "command": "generate",
        "preset": args.preset,
        "effects": args.effects,
        "bars": args.bars,
        "root": args.root,
        "bpm": args.bpm,
        "seed": seed,
        "format": resolved_format,
        "output": output,
        "saved": saved,
        "played": played,
        "artifact": artifact,
        "track": {
            "name": track_name,
            "bpm": track_bpm,
            "time_signature": list(track_time_signature),
            "key_root": track_key_root,
            "key_mode": track_key_mode,
            "length_beats": track_length_beats,
            "duration_seconds": track_duration_seconds,
        },
    }


def _resolve_seed(args: Namespace) -> tuple[int, bool]:
    import random

    user_provided_seed = args.seed is not None
    if args.seed is None:
        seed = random.randrange(2**32)
        args.seed = seed
    else:
        seed = args.seed

    random.seed(seed)
    return seed, user_provided_seed


def _batch_output_path(base: Path, index: int) -> Path:
    if base.suffix:
        return base.with_name(f"{base.stem}-{index:03d}{base.suffix}")
    return base.with_name(f"{base.name}-{index:03d}")


def _maybe_render_audio(track, args: Namespace, *, resolved_format: str):
    needs_audio = args.play or (not args.no_save and resolved_format == "wav")
    if not needs_audio:
        return None, None

    from chiptune.output.audio import AudioExporter, AudioPlayer
    from chiptune.presets import EffectPresets

    audio_exporter = AudioExporter()
    effects = None
    if args.effects:
        effect_method = EFFECT_PRESET_METHODS[args.effects]
        effects = getattr(EffectPresets, effect_method)()

    rendered_audio = None
    if args.play:
        if not AudioPlayer.is_available():
            raise ImportError(
                "Audio playback requires optional dependencies. Install with: "
                "pip install 'flexinfer-chiptune[audio]'"
            )
        rendered_audio = audio_exporter.render_track(track, effects=effects)
        AudioPlayer().play(rendered_audio)

    return effects, rendered_audio


def _track_payload_base(track) -> dict[str, object]:
    try:
        duration_seconds = float(track.duration_seconds())
    except Exception:
        duration_seconds = 0.0

    key = getattr(track, "key", None)
    key_root = getattr(key, "root", "unknown") if key is not None else "unknown"
    key_mode = "unknown"
    if key is not None:
        raw_mode = getattr(key, "mode", None)
        key_mode = getattr(raw_mode, "value", raw_mode) if raw_mode is not None else "unknown"

    return {
        "track_name": getattr(track, "name", "unknown"),
        "track_bpm": int(getattr(track, "bpm", 0)),
        "track_time_signature": tuple(getattr(track, "time_signature", (4, 4))),
        "track_key_root": key_root,
        "track_key_mode": key_mode,
        "track_length_beats": float(getattr(track, "length_beats", 0.0)),
        "track_duration_seconds": duration_seconds,
    }


def _finalize_generate(
    track,
    args: Namespace,
    *,
    seed: int,
    resolved_format: str,
    output_path: Path,
    effects,
    rendered_audio,
) -> int:
    payload_base = _track_payload_base(track)
    if args.no_save:
        if args.json:
            payload = _generate_json_payload(
                args,
                seed=seed,
                resolved_format=resolved_format,
                output=None,
                saved=False,
                played=bool(args.play),
                artifact=None,
                **payload_base,
            )
            print(json.dumps(payload, indent=2))
        if getattr(args, "metadata", None):
            _write_metadata(
                args.metadata,
                _generate_json_payload(
                    args,
                    seed=seed,
                    resolved_format=resolved_format,
                    output=None,
                    saved=False,
                    played=bool(args.play),
                    artifact=None,
                    **payload_base,
                ),
            )
        return 0

    if resolved_format == "midi":
        from chiptune.output.midi import MidiExporter

        midi_exporter = MidiExporter()
        midi_exporter.export_file(track, str(output_path))
        artifact = _file_artifact(output_path)
        if args.json:
            payload = _generate_json_payload(
                args,
                seed=seed,
                resolved_format=resolved_format,
                output=str(output_path),
                saved=True,
                played=bool(args.play),
                artifact=artifact,
                **payload_base,
            )
            print(json.dumps(payload, indent=2))
        else:
            print(f"Exported MIDI to: {output_path}")
        if getattr(args, "metadata", None):
            _write_metadata(
                args.metadata,
                _generate_json_payload(
                    args,
                    seed=seed,
                    resolved_format=resolved_format,
                    output=str(output_path),
                    saved=True,
                    played=bool(args.play),
                    artifact=artifact,
                    **payload_base,
                ),
            )
        return 0

    from chiptune.output.audio import AudioExporter

    audio_exporter = AudioExporter()
    if rendered_audio is not None:
        import soundfile as sf

        sf.write(str(output_path), rendered_audio, audio_exporter.sample_rate, subtype="PCM_16")
    else:
        audio_exporter.export_wav(track, str(output_path), effects=effects)

    artifact = _file_artifact(output_path)
    if args.json:
        payload = _generate_json_payload(
            args,
            seed=seed,
            resolved_format=resolved_format,
            output=str(output_path),
            saved=True,
            played=bool(args.play),
            artifact=artifact,
            **payload_base,
        )
        print(json.dumps(payload, indent=2))
    else:
        print(f"Exported WAV to: {output_path}")
    if getattr(args, "metadata", None):
        _write_metadata(
            args.metadata,
            _generate_json_payload(
                args,
                seed=seed,
                resolved_format=resolved_format,
                output=str(output_path),
                saved=True,
                played=bool(args.play),
                artifact=artifact,
                **payload_base,
            ),
        )

    return 0


def _sfx_metadata_payload(
    args: Namespace,
    *,
    kind: str,
    resolved_format: str,
    output: str | None,
    saved: bool,
    played: bool,
    artifact: dict[str, object] | None,
    tempo: int,
    notes,
) -> dict[str, object]:
    duration_beats = float(sum(note.duration for note in notes))
    duration_seconds = duration_beats * 60.0 / float(tempo)
    return {
        "program": "chiptune",
        "version": get_version(),
        "schema": 1,
        "command": "sfx",
        "type": args.type,
        "kind": kind,
        "format": resolved_format,
        "output": output,
        "saved": saved,
        "played": played,
        "artifact": artifact,
        "tempo": tempo,
        "duration_beats": duration_beats,
        "duration_seconds": duration_seconds,
        "note_count": len(notes),
    }


def _emit_sfx_metadata(args: Namespace, payload: dict[str, object]) -> None:
    if args.metadata is None:
        return
    if args.metadata.suffix.lower() == ".toml":
        _ensure_parent_dir(args.metadata)
        args.metadata.write_text(_toml_dump(payload), encoding="utf-8")
        return
    _write_metadata(args.metadata, payload)


def _play_sfx_audio(notes, *, tempo: int) -> None:
    from chiptune.chip.channels import Channel
    from chiptune.output.audio.exporter import AudioExporter
    from chiptune.output.audio.playback import AudioPlayer

    if not AudioPlayer.is_available():
        raise ImportError(
            "Audio playback requires optional dependencies. Install with: "
            "pip install 'flexinfer-chiptune[audio]'"
        )

    import numpy as np

    exporter = AudioExporter()
    channel = Channel.pulse(channel_id=0)
    channel.add_notes(notes)
    mono = exporter.render_channel(channel, tempo)
    stereo = np.column_stack([mono, mono]).astype(np.float32, copy=False)
    AudioPlayer().play(stereo)


def _handle_sfx_midi(args: Namespace, *, sfx, kind: str, output_path: Path) -> int:
    if output_path.suffix.lower() not in {".mid", ".midi"}:
        raise ValueError("MIDI output requires a .mid/.midi file extension.")

    notes = sfx.notes(kind)
    payload = _sfx_metadata_payload(
        args,
        kind=kind,
        resolved_format="midi",
        output=None if args.no_save else str(output_path),
        saved=not args.no_save,
        played=bool(args.play),
        artifact=None,
        tempo=sfx.tempo,
        notes=notes,
    )

    if args.no_save:
        _emit_sfx_metadata(args, payload)
        if getattr(args, "toml", False):
            print(_toml_dump(payload), end="")
        elif getattr(args, "json", False):
            print(json.dumps(payload, indent=2))
        return 0

    generator_method = getattr(sfx, kind)
    midi_bytes = generator_method()
    _ensure_parent_dir(output_path)
    sfx.save(midi_bytes, str(output_path))
    payload["artifact"] = _file_artifact(output_path)
    if getattr(args, "toml", False):
        print(_toml_dump(payload), end="")
    elif getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"Exported {args.type} SFX (MIDI) to: {output_path}")
    _emit_sfx_metadata(args, payload)
    return 0


def _handle_sfx_wav(args: Namespace, *, sfx, kind: str, output_path: Path) -> int:
    if output_path.suffix.lower() != ".wav":
        raise ValueError("WAV output requires a .wav file extension.")

    notes = sfx.notes(kind)
    payload = _sfx_metadata_payload(
        args,
        kind=kind,
        resolved_format="wav",
        output=None if args.no_save else str(output_path),
        saved=not args.no_save,
        played=bool(args.play),
        artifact=None,
        tempo=sfx.tempo,
        notes=notes,
    )

    if args.play:
        _play_sfx_audio(notes, tempo=sfx.tempo)

    if args.no_save:
        _emit_sfx_metadata(args, payload)
        if getattr(args, "toml", False):
            print(_toml_dump(payload), end="")
        elif getattr(args, "json", False):
            print(json.dumps(payload, indent=2))
        return 0

    from chiptune.output.audio.exporter import AudioExporter

    exporter = AudioExporter()
    wav_bytes = exporter.export_sfx(notes, tempo=sfx.tempo)

    _ensure_parent_dir(output_path)
    output_path.write_bytes(wav_bytes)
    payload["artifact"] = _file_artifact(output_path)
    if getattr(args, "toml", False):
        print(_toml_dump(payload), end="")
    elif getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"Exported {args.type} SFX (WAV) to: {output_path}")
    _emit_sfx_metadata(args, payload)
    return 0


def _add_generate_command(subparsers) -> None:
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate chiptune music",
        description="Generate music using genre presets or custom settings.",
    )
    output_group = gen_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON metadata",
    )
    output_group.add_argument(
        "--toml",
        action="store_true",
        help="Output machine-readable TOML metadata",
    )
    gen_parser.add_argument(
        "--preset",
        "-p",
        choices=[name for name, _ in GENRE_PRESET_ITEMS],
        default="overworld",
        help="Genre preset",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output file path (default: output.wav / output.mid)",
    )
    gen_parser.add_argument(
        "--output-template",
        default=None,
        help=(
            "Output path template for batch runs (supports {i}, {seed}, {preset}, "
            "{format}, {ext}). Example: out/{preset}-{i:03d}-{seed}.{ext}"
        ),
    )
    gen_parser.add_argument(
        "--bars",
        "-b",
        type=int,
        default=8,
        help="Length in bars",
    )
    gen_parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of tracks to generate (batch mode)",
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
        help="Effect preset",
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
        help="Output format (inferred from --output if omitted)",
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
    gen_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output newline-delimited JSON (useful with --count)",
    )
    gen_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output or play audio; still resolve paths and emit metadata",
    )
    gen_parser.add_argument(
        "--plan",
        action="store_true",
        help="Alias for --dry-run that also enables JSON output (for agents)",
    )
    gen_parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Write JSON metadata to this file",
    )
    gen_parser.set_defaults(func=cmd_generate)


def _add_sfx_command(subparsers) -> None:
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
        help="Output file path (default: <type>.mid / <type>.wav)",
    )
    sfx_parser.add_argument(
        "--format",
        choices=["midi", "wav"],
        default=None,
        help="Output format (inferred from --output if omitted)",
    )
    sfx_parser.add_argument(
        "--play",
        action="store_true",
        help="Play the sound effect (WAV only; requires optional 'audio' extras)",
    )
    sfx_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write an output file",
    )
    sfx_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output or play audio; still resolve paths and emit metadata",
    )
    sfx_parser.add_argument(
        "--plan",
        action="store_true",
        help="Alias for --dry-run that also enables JSON output (for agents)",
    )
    output_group = sfx_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON metadata",
    )
    output_group.add_argument(
        "--toml",
        action="store_true",
        help="Output machine-readable TOML metadata",
    )
    sfx_parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Write JSON metadata to this file",
    )
    sfx_parser.set_defaults(func=cmd_sfx)


def _add_list_command(subparsers) -> None:
    list_parser = subparsers.add_parser(
        "list",
        help="List available presets and options",
        description="Display available presets, effects, and sound effect types.",
    )
    output_group = list_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    output_group.add_argument(
        "--toml",
        action="store_true",
        help="Output machine-readable TOML",
    )
    list_parser.add_argument(
        "category",
        nargs="?",
        choices=["presets", "effects", "sfx", "all"],
        default="all",
        help="Category to list (default: all)",
    )
    list_parser.set_defaults(func=cmd_list)


def _add_completion_command(subparsers) -> None:
    completion_parser = subparsers.add_parser(
        "completion",
        help="Generate shell completion scripts",
        description="Print shell completion script for bash/zsh.",
    )
    completion_parser.add_argument(
        "shell",
        choices=["bash", "zsh"],
        help="Shell type",
    )
    completion_parser.set_defaults(func=cmd_completion)


def _add_schema_command(subparsers) -> None:
    schema_parser = subparsers.add_parser(
        "schema",
        help="Print JSON Schema for machine-readable outputs",
        description="Print JSON Schema for `--json`/`--jsonl` payloads.",
    )
    schema_parser.add_argument(
        "target",
        nargs="?",
        choices=["all", "generate", "sfx", "list", "doctor"],
        default="all",
        help="Which schema to print (default: all)",
    )
    schema_parser.add_argument(
        "--toml",
        action="store_true",
        help="Output schema as TOML (lossless, but JSON is the native format)",
    )
    schema_parser.set_defaults(func=cmd_schema)


def _add_doctor_command(subparsers) -> None:
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check environment and optional dependencies",
        description="Print diagnostics about installed dependencies and optional features.",
    )
    output_group = doctor_parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    output_group.add_argument("--toml", action="store_true", help="Output machine-readable TOML")
    doctor_parser.set_defaults(func=cmd_doctor)


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
            "  chiptune schema generate\n"
            "  chiptune doctor --json\n"
        ),
        formatter_class=_ChiptuneHelpFormatter,
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
    _add_generate_command(subparsers)
    _add_sfx_command(subparsers)
    _add_list_command(subparsers)
    _add_completion_command(subparsers)
    _add_schema_command(subparsers)
    _add_doctor_command(subparsers)

    return parser


def _prepare_generate_args(args: Namespace) -> None:
    if args.plan:
        args.dry_run = True
        if not getattr(args, "toml", False) and not getattr(args, "json", False) and not args.jsonl:
            args.json = True
    if args.jsonl:
        args.json = True
    if getattr(args, "toml", False) and args.jsonl:
        raise ValueError("Use only one of --jsonl or --toml")
    if args.count < 1:
        raise ValueError("--count must be >= 1")
    if args.count > 1 and args.play:
        raise ValueError("--play is not supported with --count > 1")
    if args.dry_run and args.play:
        raise ValueError("--play is not supported with --dry-run/--plan")


def _format_ext(resolved_format: str) -> str:
    return "mid" if resolved_format == "midi" else "wav"


def _output_path_from_template(
    template: str, *, index: int, seed: int, preset: str, resolved_format: str
) -> Path:
    ext = _format_ext(resolved_format)
    output_str = template.format(i=index, seed=seed, preset=preset, format=resolved_format, ext=ext)
    output_path = Path(output_str)
    if output_path.suffix == "":
        output_path = output_path.with_suffix(f".{ext}")
    return output_path


def _resolve_generate_output_base(args: Namespace, *, seed: int) -> tuple[bool, str, Path]:
    format_was_explicit, resolved_format, output_path = _resolve_generate_output(
        args.format, args.output
    )
    _check_format_output_conflict(format_was_explicit, args.output, resolved_format)

    if args.output_template is None:
        return format_was_explicit, resolved_format, output_path

    output_path = _output_path_from_template(
        args.output_template,
        index=0,
        seed=seed,
        preset=args.preset,
        resolved_format=resolved_format,
    )
    _check_format_output_conflict(format_was_explicit, output_path, resolved_format)
    return format_was_explicit, resolved_format, output_path


def _generate_one_payload(
    args: Namespace, *, seed: int, resolved_format: str, output_path: Path
) -> dict[str, object]:
    track = _build_track(args)
    payload_base = _track_payload_base(track)

    if args.dry_run:
        return _generate_json_payload(
            args,
            seed=seed,
            resolved_format=resolved_format,
            output=str(output_path),
            saved=False,
            played=False,
            artifact=None,
            **payload_base,
        )

    effects, rendered_audio = _maybe_render_audio(track, args, resolved_format=resolved_format)
    played = bool(args.play)

    if args.no_save:
        return _generate_json_payload(
            args,
            seed=seed,
            resolved_format=resolved_format,
            output=None,
            saved=False,
            played=played,
            artifact=None,
            **payload_base,
        )

    _ensure_parent_dir(output_path)
    if resolved_format == "midi":
        from chiptune.output.midi import MidiExporter

        MidiExporter().export_file(track, str(output_path))
    else:
        from chiptune.output.audio import AudioExporter

        exporter = AudioExporter()
        if rendered_audio is not None:
            import soundfile as sf

            sf.write(str(output_path), rendered_audio, exporter.sample_rate, subtype="PCM_16")
        else:
            exporter.export_wav(track, str(output_path), effects=effects)

    artifact = _file_artifact(output_path)
    return _generate_json_payload(
        args,
        seed=seed,
        resolved_format=resolved_format,
        output=str(output_path),
        saved=True,
        played=played,
        artifact=artifact,
        **payload_base,
    )


def _generate_payloads(
    args: Namespace, *, seed: int, resolved_format: str, output_path: Path
) -> list[dict[str, object]]:
    import random

    payloads: list[dict[str, object]] = []
    for index in range(args.count):
        run_seed = seed + index
        random.seed(run_seed)

        if args.output_template is not None:
            run_output_path = _output_path_from_template(
                args.output_template,
                index=index,
                seed=run_seed,
                preset=args.preset,
                resolved_format=resolved_format,
            )
        else:
            run_output_path = (
                output_path if args.count == 1 else _batch_output_path(output_path, index)
            )

        payloads.append(
            _generate_one_payload(
                args,
                seed=run_seed,
                resolved_format=resolved_format,
                output_path=run_output_path,
            )
        )

    return payloads


def _emit_generate_payloads(
    args: Namespace, *, payloads: list[dict[str, object]], resolved_format: str
) -> None:
    if args.jsonl:
        for payload in payloads:
            print(json.dumps(payload, separators=(",", ":")))
    elif getattr(args, "toml", False):
        print(_toml_dump(payloads[0] if len(payloads) == 1 else payloads, array_key="runs"), end="")
    elif args.json:
        print(json.dumps(payloads[0] if len(payloads) == 1 else payloads, indent=2))
    else:
        for payload in payloads:
            out = payload.get("output")
            fmt = payload.get("format", resolved_format)
            if out:
                print(f"Exported {fmt} to: {out}")

    if getattr(args, "metadata", None):
        if args.jsonl:
            _write_metadata_jsonl(args.metadata, payloads)
        elif args.metadata.suffix.lower() == ".toml":
            _ensure_parent_dir(args.metadata)
            args.metadata.write_text(
                _toml_dump(payloads[0] if len(payloads) == 1 else payloads, array_key="runs"),
                encoding="utf-8",
            )
        else:
            _write_metadata(args.metadata, payloads[0] if len(payloads) == 1 else payloads)


def cmd_generate(args: Namespace) -> int:
    """Execute the generate command."""
    _prepare_generate_args(args)
    seed, user_provided_seed = _resolve_seed(args)
    if user_provided_seed or args.json or getattr(args, "toml", False):
        print(f"Seed: {seed}", file=sys.stderr)
    _format_was_explicit, resolved_format, output_path = _resolve_generate_output_base(
        args, seed=seed
    )

    if args.count == 1 and not args.jsonl and not args.dry_run:
        if not args.no_save:
            _ensure_parent_dir(output_path)
        track = _build_track(args)
        effects, rendered_audio = _maybe_render_audio(track, args, resolved_format=resolved_format)
        return _finalize_generate(
            track,
            args,
            seed=seed,
            resolved_format=resolved_format,
            output_path=output_path,
            effects=effects,
            rendered_audio=rendered_audio,
        )

    payloads = _generate_payloads(
        args,
        seed=seed,
        resolved_format=resolved_format,
        output_path=output_path,
    )
    _emit_generate_payloads(args, payloads=payloads, resolved_format=resolved_format)
    return 0


def cmd_sfx(args: Namespace) -> int:
    """Execute the sfx command."""
    from chiptune.sfx.effects import SFXGenerator

    if args.plan:
        args.dry_run = True
        if not getattr(args, "toml", False) and not getattr(args, "json", False):
            args.json = True

    sfx = SFXGenerator()

    format_was_explicit, resolved_format, output_path = _resolve_sfx_output(
        args.format, args.output, args.type
    )
    _check_format_output_conflict(format_was_explicit, args.output, resolved_format)

    if args.play and resolved_format != "wav":
        raise ValueError("--play is only supported with --format wav")
    if args.dry_run and args.play:
        raise ValueError("--play is not supported with --dry-run/--plan")

    method_name = SFX_METHODS[args.type]
    if args.dry_run:
        notes = sfx.notes(method_name)
        payload = _sfx_metadata_payload(
            args,
            kind=method_name,
            resolved_format=resolved_format,
            output=str(output_path),
            saved=False,
            played=False,
            artifact=None,
            tempo=sfx.tempo,
            notes=notes,
        )
        if getattr(args, "toml", False):
            print(_toml_dump(payload), end="")
        elif getattr(args, "json", False):
            print(json.dumps(payload, indent=2))
        else:
            print(f"Would export {args.type} SFX ({resolved_format.upper()}) to: {output_path}")
        _emit_sfx_metadata(args, payload)
        return 0

    if resolved_format == "midi":
        return _handle_sfx_midi(args, sfx=sfx, kind=method_name, output_path=output_path)
    return _handle_sfx_wav(args, sfx=sfx, kind=method_name, output_path=output_path)


def cmd_list(args: Namespace) -> int:
    """Execute the list command."""
    category = args.category

    if args.json:
        payload: dict[str, object] = {"program": "chiptune", "version": get_version(), "schema": 1}
        if category in ("presets", "all"):
            payload["presets"] = _as_json_items(GENRE_PRESET_ITEMS)
        if category in ("effects", "all"):
            payload["effects"] = _as_json_items(EFFECT_PRESET_ITEMS)
        if category in ("sfx", "all"):
            payload["sfx"] = _as_json_items(SFX_ITEMS)

        print(json.dumps(payload, indent=2))
        return 0

    if getattr(args, "toml", False):
        payload: dict[str, object] = {"program": "chiptune", "version": get_version(), "schema": 1}
        if category in ("presets", "all"):
            payload["presets"] = _as_json_items(GENRE_PRESET_ITEMS)
        if category in ("effects", "all"):
            payload["effects"] = _as_json_items(EFFECT_PRESET_ITEMS)
        if category in ("sfx", "all"):
            payload["sfx"] = _as_json_items(SFX_ITEMS)

        print(_toml_dump(payload), end="")
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
        print("\nSound Effects (MIDI or WAV):")
        print("-" * 40)
        for name, desc in SFX_ITEMS:
            print(f"  {name:14} {desc}")

    print()
    return 0


def cmd_completion(args: Namespace) -> int:
    """Print shell completion scripts."""
    presets = " ".join(name for name, _ in GENRE_PRESET_ITEMS)
    effects = " ".join(name for name, _ in EFFECT_PRESET_ITEMS)
    sfx = " ".join(name for name, _ in SFX_ITEMS)

    bash_script = f"""# bash completion for chiptune
_chiptune_complete() {{
  local cur prev
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  prev="${{COMP_WORDS[COMP_CWORD-1]}}"

  local commands="generate sfx list completion schema doctor"
  local global_opts="--help -h --version --debug"

  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "$commands $global_opts" -- "$cur") )
    return 0
  fi

  local subcommand="${{COMP_WORDS[1]}}"
    case "$subcommand" in
    generate)
      local opts="--preset -p --output -o --output-template --bars -b --count --root -r --bpm \\
--effects -e --no-drums --no-bass --no-counter --seed -s --format -f \\
--play --no-save --json --toml --jsonl --dry-run --plan --metadata"
      if [[ "$prev" == "--preset" || "$prev" == "-p" ]]; then
        COMPREPLY=( $(compgen -W "{presets}" -- "$cur") )
        return 0
      fi
      if [[ "$prev" == "--effects" || "$prev" == "-e" ]]; then
        COMPREPLY=( $(compgen -W "{effects}" -- "$cur") )
        return 0
      fi
      if [[ "$prev" == "--format" || "$prev" == "-f" ]]; then
        COMPREPLY=( $(compgen -W "wav midi" -- "$cur") )
        return 0
      fi
      COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
      return 0
      ;;
    sfx)
      local opts="--output -o --format --play --no-save --dry-run --plan --json --toml --metadata"
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "{sfx}" -- "$cur") )
        return 0
      fi
      if [[ "$prev" == "--format" ]]; then
        COMPREPLY=( $(compgen -W "midi wav" -- "$cur") )
        return 0
      fi
      COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
      return 0
      ;;
    list)
      local opts="--json --toml"
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "presets effects sfx all $opts" -- "$cur") )
        return 0
      fi
      COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
      return 0
      ;;
    completion)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "bash zsh" -- "$cur") )
        return 0
      fi
      ;;
    schema)
      if [[ $COMP_CWORD -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "all generate sfx list doctor" -- "$cur") )
        return 0
      fi
      local opts="--toml"
      COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
      return 0
      ;;
    doctor)
      local opts="--json --toml"
      COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
      return 0
      ;;
  esac
}}

complete -F _chiptune_complete chiptune
"""

    if args.shell == "bash":
        print(bash_script)
        return 0

    zsh_script = """#compdef chiptune
autoload -Uz bashcompinit
bashcompinit

""" + bash_script

    print(zsh_script)
    return 0


def _json_schema_dialect() -> str:
    return "https://json-schema.org/draft/2020-12/schema"


def _artifact_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["path", "bytes", "sha256"],
        "properties": {
            "path": {"type": "string"},
            "bytes": {"type": "integer", "minimum": 0},
            "sha256": {"type": "string"},
        },
    }


def _generate_payload_json_schema() -> dict[str, object]:
    dialect = _json_schema_dialect()
    artifact = _artifact_json_schema()
    return {
        "$schema": dialect,
        "$id": "https://flexinfer.ai/schemas/chiptune/cli/v1/generate.json",
        "title": "chiptune generate JSON payload",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "program",
            "version",
            "schema",
            "command",
            "seed",
            "format",
            "saved",
            "played",
        ],
        "properties": {
            "program": {"const": "chiptune"},
            "version": {"type": "string"},
            "schema": {"const": 1},
            "command": {"const": "generate"},
            "preset": {"type": "string"},
            "effects": {"type": "string"},
            "bars": {"type": "integer", "minimum": 1},
            "root": {"type": ["string", "null"]},
            "bpm": {"type": ["integer", "null"]},
            "seed": {"type": "integer"},
            "format": {"enum": ["wav", "midi"]},
            "output": {"type": ["string", "null"]},
            "saved": {"type": "boolean"},
            "played": {"type": "boolean"},
            "artifact": {"anyOf": [{"type": "null"}, artifact]},
            "track": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "name",
                    "bpm",
                    "time_signature",
                    "key_root",
                    "key_mode",
                    "length_beats",
                    "duration_seconds",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "bpm": {"type": "integer"},
                    "time_signature": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "key_root": {"type": "string"},
                    "key_mode": {"type": "string"},
                    "length_beats": {"type": "number"},
                    "duration_seconds": {"type": "number"},
                },
            },
        },
    }


def _sfx_payload_json_schema() -> dict[str, object]:
    dialect = _json_schema_dialect()
    artifact = _artifact_json_schema()
    return {
        "$schema": dialect,
        "$id": "https://flexinfer.ai/schemas/chiptune/cli/v1/sfx.json",
        "title": "chiptune sfx JSON payload",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "program",
            "version",
            "schema",
            "command",
            "type",
            "kind",
            "format",
            "saved",
            "played",
        ],
        "properties": {
            "program": {"const": "chiptune"},
            "version": {"type": "string"},
            "schema": {"const": 1},
            "command": {"const": "sfx"},
            "type": {"type": "string"},
            "kind": {"type": "string"},
            "format": {"enum": ["wav", "midi"]},
            "output": {"type": ["string", "null"]},
            "saved": {"type": "boolean"},
            "played": {"type": "boolean"},
            "artifact": {"anyOf": [{"type": "null"}, artifact]},
            "tempo": {"type": "integer"},
            "duration_beats": {"type": "number"},
            "duration_seconds": {"type": "number"},
            "note_count": {"type": "integer", "minimum": 0},
        },
    }


def _list_payload_json_schema() -> dict[str, object]:
    dialect = _json_schema_dialect()
    item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "description"],
        "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
    }
    return {
        "$schema": dialect,
        "$id": "https://flexinfer.ai/schemas/chiptune/cli/v1/list.json",
        "title": "chiptune list JSON payload",
        "type": "object",
        "additionalProperties": True,
        "required": ["program", "version", "schema"],
        "properties": {
            "program": {"const": "chiptune"},
            "version": {"type": "string"},
            "schema": {"const": 1},
            "presets": {"type": "array", "items": item},
            "effects": {"type": "array", "items": item},
            "sfx": {"type": "array", "items": item},
        },
    }


def _doctor_payload_json_schema() -> dict[str, object]:
    dialect = _json_schema_dialect()
    return {
        "$schema": dialect,
        "$id": "https://flexinfer.ai/schemas/chiptune/cli/v1/doctor.json",
        "title": "chiptune doctor JSON payload",
        "type": "object",
        "additionalProperties": True,
        "required": ["program", "version", "schema", "python", "modules"],
        "properties": {
            "program": {"const": "chiptune"},
            "version": {"type": "string"},
            "schema": {"const": 1},
            "python": {
                "type": "object",
                "additionalProperties": True,
                "required": ["version", "implementation", "platform"],
                "properties": {
                    "version": {"type": "string"},
                    "implementation": {"type": "string"},
                    "platform": {"type": "string"},
                },
            },
            "modules": {"type": "object"},
            "install": {"type": "object"},
        },
    }


def cmd_schema(args: Namespace) -> int:
    """Print JSON Schema documents for machine-readable CLI outputs."""
    schemas: dict[str, dict[str, object]] = {
        "generate": _generate_payload_json_schema(),
        "sfx": _sfx_payload_json_schema(),
        "list": _list_payload_json_schema(),
        "doctor": _doctor_payload_json_schema(),
    }

    if args.target == "all":
        payload: dict[str, object] = {
            "dialect": _json_schema_dialect(),
            "schemas": schemas,
        }
        if getattr(args, "toml", False):
            print(_toml_dump(payload), end="")
            return 0
        print(json.dumps(payload, indent=2))
        return 0

    if getattr(args, "toml", False):
        print(_toml_dump(schemas[args.target]), end="")
        return 0
    print(json.dumps(schemas[args.target], indent=2))
    return 0


def cmd_doctor(args: Namespace) -> int:
    """Check environment and optional dependencies."""
    import importlib.util
    import platform

    checks: dict[str, dict[str, object]] = {}

    def check_module(module: str) -> None:
        spec = importlib.util.find_spec(module)
        checks[module] = {"available": spec is not None}

    for module in ["music21", "midiutil", "numpy", "scipy", "soundfile", "sounddevice"]:
        check_module(module)

    payload: dict[str, object] = {
        "program": "chiptune",
        "version": get_version(),
        "schema": 1,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "modules": checks,
        "install": {
            "base": "pip install flexinfer-chiptune",
            "audio": "pip install 'flexinfer-chiptune[audio]'",
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    if getattr(args, "toml", False):
        print(_toml_dump(payload), end="")
        return 0

    print("chiptune doctor")
    print(f"- version: {payload['version']}")
    py = payload["python"]
    print(f"- python: {py['implementation']} {py['version']} ({py['platform']})")
    print("- modules:")
    for module, info in checks.items():
        status = "OK" if info["available"] else "MISSING"
        print(f"  - {module}: {status}")
    print("- install:")
    install = payload["install"]
    print(f"  - base: {install['base']}")
    print(f"  - audio: {install['audio']}")
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
