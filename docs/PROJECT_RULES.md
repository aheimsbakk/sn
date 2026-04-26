# Project Rules

## Versioning and Git tagging

### Rule: always tag the version-bump commit

Git tags must be placed on the version-bump commit, never on a prior commit.
The script `scripts/bump-version.sh` enforces this automatically by:

1. Refusing to run with a dirty working tree.
2. Rewriting version strings in `pyproject.toml`, `src/sn/version.py`, `src/sn/http.py`, and `BLUEPRINT.md`.
3. Staging those four files and creating a commit: `chore: bump version to <version>`.
4. Running `gitsem <version>` via `uvx` to apply floating semver tags to that commit.

**Never run `gitsem` manually on an arbitrary commit.**  Always go through `bump-version.sh`.

### Rule: use gitsem for tagging

All release tags are managed by `gitsem` from <https://github.com/aheimsbakk/gitsem>.
Do not create or move version tags by hand with `git tag`.

### Workflow

Bump and tag:

```bash
scripts/bump-version.sh [patch|minor|major]
```

Push tags to the remote after review:

```bash
uvx --from git+https://github.com/aheimsbakk/gitsem gitsem --push
```

Repair floating tags if they drift (e.g. after a force-push):

```bash
uvx --from git+https://github.com/aheimsbakk/gitsem gitsem --repair
```
