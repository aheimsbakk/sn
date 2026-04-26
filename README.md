# grc

`grc` is a Python command-line tool that downloads and stores Security Now transcripts from GRC as local Markdown files.

The supported Python package name is `grc`.

## What it does

- Syncs transcript files from the GRC Security Now archive
- Stores transcripts as UTF-8 Markdown with YAML front matter
- Stores a lightweight metadata-derived `source_sha` in front matter
- Reads the stored Markdown files and their front matter as the local source of truth
- Reports archive status, including missing or failed transcripts

## Quick start

1. Create a virtual environment and install the project:

```bash
uv venv
uv pip install -e .
```

2. Sync a small set of recent episodes into the current directory:

```bash
uv run grc sync --latest 2
```

3. Check archive status:

```bash
uv run grc status
```

The tool writes transcript Markdown files directly into the chosen archive directory.

## Usage

### Show help

```bash
uv run grc --help
```

### Sync transcripts

Sync the latest five episodes:

```bash
uv run grc sync --latest 5
```

Sync one archive year:

```bash
uv run grc sync --year 2005
```

Sync all discovered years:

```bash
uv run grc sync
```

Sync into a different archive directory:

```bash
uv run grc -d ./archive sync --latest 3
```

See what would happen without writing files:

```bash
uv run grc sync --latest 2 --dry-run
```

Re-check episodes even if they already exist locally:

```bash
uv run grc sync --latest 2 --force
```

With `--force`, the tool first compares a lightweight checksum built from remote metadata headers. If the checksum matches the stored `source_sha`, it skips the full transcript download.

Prefer HTML transcripts instead of text transcripts:

```bash
uv run grc sync --latest 2 --source-preference html
```

### Check archive status

Show summary counts:

```bash
uv run grc status
```

Show only non-present episodes:

```bash
uv run grc status --missing
```

Get machine-readable output:

```bash
uv run grc status --json
```

## Configuration

### Global options

- `-h`, `--help`: show help
- `-V`, `--version`: show version
- `-v`, `--verbose`: show fetch progress on stderr; repeat for more detail later
- `-d`, `--archive-dest PATH`: choose the archive root directory

### `sync` options

- `--year YYYY`: sync only one archive year; omit it to sync all discovered years
- `--latest N`: sync only the most recent `N` episodes
- `--force`: re-check existing episodes and rewrite only when the remote metadata checksum changes
- `--dry-run`: plan work without writing output files
- `--pause-seconds FLOAT`: delay between HTTP requests, default `2.0`
- `--timeout-seconds FLOAT`: request timeout, default `20.0`
- `--max-retries N`: retry count, default `2`
- `--backoff-seconds FLOAT`: retry backoff base, default `5.0`
- `--source-preference {auto,txt,html}`: transcript source preference, default `auto`

### `status` options

- `--missing`: list only non-present episodes
- `--json`: emit JSON instead of text

### Exit codes

#### `grc sync`

- `0`: success
- `2`: completed with one or more `remote_missing`, `fetch_error`, or `parse_error` results
- `1`: fatal error

#### `grc status`

- `0`: archive is readable and has no non-present states
- `2`: archive is readable and contains one or more non-present states
- `1`: fatal error

## Archive layout

When you use the current directory as the archive root, the tool writes:

```text
./
  sn-1000-one-thousand.md
```

## Run tests

Run the offline test suite with:

```bash
uv run python -m unittest discover -s tests
```

## Scripts

### `scripts/bump-version.sh`

Bumps the project version in release files.

```bash
scripts/bump-version.sh minor
```

### `scripts/validate-worklog.sh`

Validates a worklog file before commit.

```bash
scripts/validate-worklog.sh docs/worklogs/2026-04-26-12-13-grc-package-rename.md
```

## Contributing

- Keep tests offline
- Keep source under `src/`
- Keep tests under `tests/`
- Update `BLUEPRINT.md` and `CONTEXT.md` when behavior changes
