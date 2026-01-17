# Product Spec

## Summary

Make `flexinfer-chiptune` feel like a “real” CLI tool:
- Human-friendly by default (clear help, completions, actionable errors).
- Agent-friendly on demand (stable `--json` and `--metadata` outputs).
- Robust across environments (optional deps don’t break basic commands; `doctor` explains what’s missing).

## Goals

- Deterministic generation with clear seed handling.
- First-class metadata emission for generated artifacts.
- Easy install/diagnose story for optional audio/midi dependencies.

## Non-Goals

- Full DAW-grade editing, synthesis, or real-time sequencing.
- Mandating heavy dependencies for basic usage.

## Users / Stakeholders

- Developers generating music/SFX for games, demos, or agents.
- Agents/automation that need predictable artifact + metadata generation.

## Requirements

### Functional

- `chiptune generate --json` emits stable metadata for agent consumption.
- `chiptune sfx --format wav` can render wav (optional deps) and `--play` can audition it.
- `chiptune completion` can output bash/zsh scripts.

### Non-Functional

- CLI import time must not fail if optional deps are missing.
- Metadata formats must be additive and versioned.

## UX / Flows

- “Happy path”: generate music/SFX with defaults, save output, print short status to stderr.
- “Agent path”: run with `--json` and consume stdout as metadata, artifacts on disk.

## Data / APIs

- CLI JSON payloads include stable keys: `program`, `version`, `schema`, `command`, plus command-specific metadata.

## Rollout / Migration

- Additive flags/commands; keep existing behavior defaulting to text output.

## Observability

- Logs:
- stderr for human-oriented status; stdout reserved for machine-readable JSON.
- Metrics:
- Traces:

## Risks

- Optional deps (audio/midi) drift; keep `doctor` up to date.

## Open Questions

- Publish JSON Schema as a CLI command?

## Sources

- [S1] …
- [S1] `.loom/10-research.md`
