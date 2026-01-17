# Loom Context Pack

## Quick Links

- Workspace snapshot: `00-workspace-snapshot.md`
- MCP inventory: `00-mcp-inventory.md`
- Research: `10-research.md`
- Product spec: `20-product-spec.md`
- Implementation plan: `30-implementation-plan.md`
- Decisions: `40-decisions.md`
- Worklog: `50-worklog.md`

## Current Goal

- [x] Make `flexinfer-chiptune` CLI a high-quality tool for humans and agents: deterministic outputs, machine-readable metadata, and optional audio/MIDI features that degrade gracefully when deps are missing.
- [x] Success criteria: `ruff check` clean, `pytest` passes, and CLI supports `generate --json`, `sfx --format wav` / `--play`, plus shell completions.

## Open Questions

- [ ] Should we publish a stable JSON Schema (`chiptune schema`) for `--json` payloads?
- [ ] Should `--json` also support JSON Lines (`--jsonl`) for batch generation?

## Risks

- [ ] Optional audio deps (numpy/scipy/soundfile/sounddevice) cause import failures; mitigate via lazy imports and `chiptune doctor`.
