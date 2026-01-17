# Implementation Plan

## Scope

Continue polishing `src/chiptune/cli.py`:
- Keep `--json`/`--metadata` outputs consistent and accurate.
- Keep `ruff` happy (esp. complexity/statement-count checks).
- Preserve lazy-import strategy so optional deps don’t break basic CLI usage.

## Milestones

1. Fix `generate --json` track metadata correctness.
2. Refactor `sfx` implementation to reduce complexity and enable future expansion.
3. Validate with `ruff` + `pytest`, then ship via commit/push.

## Plan

1. Update JSON payload creation to derive track properties from generated `Track` objects (bpm/time signature/duration).
2. Extract helper functions for `sfx` wav/midi/play/metadata paths to reduce branching in `cmd_sfx`.
3. Add/update unit tests covering corrected metadata fields.
4. Run `ruff check` + targeted `pytest` and iterate until green.

## Test Plan

- `ruff check src/chiptune/cli.py`
- `pytest tests/test_cli.py -q`

## Rollout / Backout

- Rollout: normal commit to main branch and push.
- Backout: revert the commit(s) if schema/CLI regressions appear.

## Acceptance Criteria

- `chiptune generate --json` includes accurate track info.
- `chiptune sfx` supports wav/midi/play without ruff complexity violations.
- `ruff` and `pytest` pass locally.

## Risks / Dependencies

- Optional audio deps may not be installed in all environments; keep failures actionable via `chiptune doctor`.

## Sources

- [S1] `.loom/10-research.md`
