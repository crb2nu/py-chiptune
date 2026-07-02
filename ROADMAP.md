# py-chiptune Roadmap

> Last Updated: 2026-07-02
> Tier: 2 (see workspace AGENTS.md "Portfolio Tiers")
> Tracking Issue: none — maintain-mode; backlog = [open issues](https://gitlab.flexinfer.ai/libs/py-chiptune/-/issues)

## Current Status

8-bit/16-bit music and SFX generation library with a semantic API for agent-driven composition: music-theory primitives, game-theme templates, NES/Game Boy/C64/Genesis chip models, effects chains, MIDI export, and direct audio synthesis; optional Rust acceleration path. Maintain-mode: last organic change 2026-01-16 (CLI/agent-output UX); 2026-03 commits are CI/packaging fixes (Rust accel path disabled in CI for a deterministic suite) and the 2026-03-17 workspace-wide tech-radar CI bulk change.

- **Plan store**: plan-workspace-portfolio-refresh-2026-h2-roadmaps-quality-baselin-f3db23 (this refresh; no repo-specific active plan)
- **Deployed**: not deployed (library; workspace-local consumption)
- **CI**: python template family (platform/gitops `ci/templates/python.yml` + tech-radar `radar.yml`)

## Now

- Maintenance only — dependency and CI fixes as needed; no active feature work.

## Next

- [ ] Pre-commit hooks + standard Makefile targets if flagged at claim time by portfolio-refresh slice 7 (quality gate wave B, pending)

## Later

- Re-enable the Rust accel path in CI once its nondeterminism is resolved (disabled 2026-03-03, commit 6cea6914).

## Backlog

Full backlog: [P1](https://gitlab.flexinfer.ai/libs/py-chiptune/-/issues/?label_name[]=P1) · [P2](https://gitlab.flexinfer.ai/libs/py-chiptune/-/issues/?label_name[]=P2) · [P3](https://gitlab.flexinfer.ai/libs/py-chiptune/-/issues/?label_name[]=P3) · [all open](https://gitlab.flexinfer.ai/libs/py-chiptune/-/issues)
