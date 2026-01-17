# Decisions

Record decisions as they are made, with date, rationale, and sources.

## Template

### YYYY-MM-DD: Decision title

- Decision:
- Rationale:
- Alternatives considered:
- Consequences:
- Sources:
  - [S1] …

### 2026-01-17: Keep CLI dependency-light and degrade gracefully

- Decision: Keep `chiptune` CLI in stdlib `argparse` and make optional audio/MIDI deps lazy/optional, surfaced via `doctor`.
- Rationale: The CLI should run in minimal environments (CI, agents) without optional deps causing import failures.
- Alternatives considered: Adopt `argcomplete`/Click/Typer + richer UI deps; require audio deps by default.
- Consequences: Some UX features are simpler (completion scripts are best-effort); optional features require explicit install.
- Sources:
  - [S1] `.loom/10-research.md`
