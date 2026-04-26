---
when: 2026-04-26T14:21:50Z
why: rename the CLI command and Python package from grc to sn to reflect its purpose as a Security Now sync tool
what: full rename of grc package, command, and all references to sn v1.2.0
model: github-copilot/claude-sonnet-4.6
tags: [refactor, rename, cli, packaging]
---

Renamed the Python package directory from `src/grc/` to `src/sn/`, updated `pyproject.toml` (project name, console entry point), replaced all `grc` import references in source and tests, updated `prog`, `USER_AGENT`, `bump-version.sh`, `BLUEPRINT.md`, and `CONTEXT.md`. No backward compatibility shim was kept. Bumped to v1.2.0.
