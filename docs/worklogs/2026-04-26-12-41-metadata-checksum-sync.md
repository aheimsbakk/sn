---
when: 2026-04-26T12:41:09Z
why: Avoid re-downloading unchanged transcripts during forced sync runs.
what: Added metadata-derived source_sha tracking, force-sync skip logic, tests, docs, and bumped the project to v0.4.0.
model: github-copilot/gpt-5.4
tags: [sync, manifest, frontmatter, docs, tests, version]
---

Added metadata-based checksum support in `src/grc/http.py`, `src/grc/sync.py`, `src/grc/models.py`, `src/grc/manifest.py`, and `src/grc/markdown_writer.py` so `--force` can compare remote headers before downloading transcripts. Updated `tests/test_sync.py`, `tests/test_manifest.py`, and `tests/test_markdown_writer.py` plus `README.md`, `BLUEPRINT.md`, and `CONTEXT.md` to document the new `source_sha` behavior; release version is now v0.4.0.
