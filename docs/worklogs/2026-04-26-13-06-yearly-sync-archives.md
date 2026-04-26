---
when: 2026-04-26T13:06:50Z
why: Sync needed to fetch yearly archive pages correctly and remove broken episode range options.
what: Added year-based sync selection, fixed yearly archive discovery, and bumped the project to v1.0.0.
model: github-copilot/gpt-5.4
tags: [sync, cli, archives, docs, versioning]
---

Updated `src/grc/archive_index.py`, `src/grc/sync.py`, `src/grc/cli.py`, and `src/grc/models.py` so sync can fetch `/sn/past/YYYY.htm` archives and optionally limit work to one year.
Added test coverage in `tests/test_archive_index.py`, `tests/test_cli.py`, and `tests/test_sync.py`, then updated `README.md`, `BLUEPRINT.md`, and `CONTEXT.md` to match the new CLI behavior.
Released version 1.0.0 in `pyproject.toml`, `src/grc/version.py`, `src/grc/http.py`, and `BLUEPRINT.md`.
