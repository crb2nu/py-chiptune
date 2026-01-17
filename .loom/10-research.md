# Research Brief

## Problem

Make `chiptune` CLI outputs useful for both humans and agents:
- Add stable machine-readable JSON metadata for generated artifacts.
- Add ergonomic shell completions and self-diagnostics.
- Keep optional audio/MIDI deps from breaking import/usage.

## Questions

- Q1: What makes CLI JSON output stable and automation-friendly?
- Q2: What are pragmatic patterns for shell completions without adding heavy deps?
- Q3: What SFX generator features (from retro tools like sfxr/jsfxr) are most valuable to surface?

## Constraints

- Prefer stdlib (`argparse`, `json`) and keep new dependencies optional.
- Avoid importing optional heavy deps at module import time.
- JSON output must be additive and versioned (stable keys like `program`, `version`, `schema`).

## Method

- What you inspected (files/commands/tools) and why

## Findings

### CLI JSON output + schema versioning

- Tools benefit from explicit schema/version metadata to allow downstream parsers/agents to branch safely as formats evolve.
- JSON Schema itself can declare dialect via `$schema`; schema versioning is commonly handled via separate schema files/paths or an explicit `version` field in the data.
- Related pattern: expose the schema via a CLI flag/command so automation can validate payloads.

### Shell completions

- For argparse CLIs, the typical “best” solution is `argcomplete`, but it’s an optional dependency and requires shell integration. For minimal-dep tools, shipping simple completion scripts for subcommands/options is a practical compromise.

### SFX UX inspiration (sfxr/jsfxr)

- SFX tools often expose “sound design knobs” (waveform, envelope, filters, arpeggio, etc.) and also support exporting to wav plus bundling metadata. Even if we don’t mirror all parameters, it’s useful to:
  - expose a deterministic seed
  - export wav quickly
  - emit metadata describing the chosen effect “kind” and output properties

## Options

### Option A

- Pros: keep current approach (custom `--json` payload + lightweight completion scripts), iterate incrementally.
- Cons: schema validation stays informal without a published JSON Schema.
- Risks: payload drift if we don’t explicitly version fields and keep backwards-compat.

### Option B

- Pros: add `chiptune schema` (prints JSON Schema for `--json` payloads) and potentially `--jsonl` for batch outputs.
- Cons: extra maintenance; schema needs versioning discipline.
- Risks: users start depending on schema; breaking changes become harder.

## Recommendation

Stick with Option A now, but add an explicit `schema` identifier and keep payloads additive. Consider Option B (`chiptune schema`) once payload stabilizes and after 1–2 iterations of real usage.

## Sources

Use stable references: workspace file paths with line numbers when possible (e.g. `src/foo.ts:42`), command outputs (include the command), and URLs.

- [S1] https://news.ycombinator.com/item?id=29435786
- [S2] https://stackoverflow.com/questions/61077293/is-there-a-standard-for-specifying-a-version-for-json-schema
- [S3] https://json-schema.org/understanding-json-schema/reference/schema
- [S4] https://kislyuk.github.io/argcomplete/
- [S5] https://github.com/grimfang4/sfxr/blob/master/sfxr/README.txt
