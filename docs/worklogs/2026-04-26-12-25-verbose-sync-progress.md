---
when: 2026-04-26T12:25:51Z
why: Make sync progress visible and preserve completed work after an interrupted run.
what: Added verbose sync progress output, interrupt-safe manifest saves, and bumped the project to v0.3.0.
model: github-copilot/gpt-5.4
tags: [sync, cli, manifest, tests, docs, version]
---

Added stderr progress output for archive and transcript fetches in `src/grc/sync.py` and passed verbose settings through `src/grc/cli.py`.
Added tests in `tests/test_sync.py` and `tests/test_cli.py` to cover verbose output and manifest persistence on interrupt.
Updated `README.md`, `BLUEPRINT.md`, and `CONTEXT.md` to document the new behavior, and bumped release files to version 0.3.0.
