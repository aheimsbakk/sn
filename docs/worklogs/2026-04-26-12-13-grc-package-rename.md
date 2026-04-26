---
when: 2026-04-26T12:13:23Z
why: Finalize the grc CLI package so direct uv and uvx usage matches the command name.
what: Renamed the Python package to grc, removed the grc_sync fallback, and added offline tests and packaging scripts.
model: github-copilot/gpt-5.4
tags: [python, cli, packaging, uv, tests]
---

Promoted the codebase to the `grc` package, removed the legacy `grc_sync` package, and updated docs in `README.md`, `BLUEPRINT.md`, and `CONTEXT.md` to match the new layout and version 0.2.0.
Added the offline test suite and real transcript fixtures under `tests/` to cover CLI behavior, parsing, manifest state, and sync/status flows.
Added `scripts/bump-version.sh` and `scripts/validate-worklog.sh`, and updated `.gitignore` for build and cache artifacts.
