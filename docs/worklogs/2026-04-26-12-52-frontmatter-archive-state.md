---
when: 2026-04-26T12:52:55Z
why: Remove drift-prone manifest state and make stored transcript files the only local source of truth.
what: Replaced manifest storage with front-matter archive scanning, moved transcripts to the archive root, updated tests and docs, and bumped the project to v0.5.0.
model: github-copilot/gpt-5.4
tags: [sync, frontmatter, archive-state, docs, tests, version]
---

Added `src/grc/archive_state.py` and updated `src/grc/sync.py`, `src/grc/cli.py`, `src/grc/status.py`, and `src/grc/markdown_writer.py` so local state now comes from stored Markdown files and front matter instead of `.grc-sync/manifest.json`. Removed `src/grc/manifest.py`, moved transcript output to the archive root, replaced manifest tests with `tests/test_archive_state.py`, and updated the user and project docs; release version is now v0.5.0.
