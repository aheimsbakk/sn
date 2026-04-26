---
when: 2026-04-26T14:31:10Z
why: establish gitsem-based git tagging workflow and retroactively tag all historical releases
what: add gitsem tagging to bump-version.sh, add PROJECT_RULES.md, update README, backfill historical tags
model: github-copilot/claude-sonnet-4.6
tags: [tooling, versioning, git, docs]
---

Updated `scripts/bump-version.sh` to guard against a dirty working tree, commit the version files, and run `gitsem` via `uvx` to tag the bump commit immediately. Created `docs/PROJECT_RULES.md` with the tagging convention. Updated `README.md` with the new bump-and-tag workflow. Retroactively applied exact version tags to all historical commits and ran `gitsem --repair` to create floating tags. Current version remains 2.0.0.
