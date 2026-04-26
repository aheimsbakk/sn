# grc

`grc` is a Python command-line tool that downloads Security Now transcripts from GRC and stores them as local Markdown files.

## What it does

- Syncs transcript files from the GRC Security Now archive
- Stores each transcript as a UTF-8 Markdown file with YAML front matter
- Records a lightweight metadata checksum (`source_sha`) in front matter to detect remote changes
- Reads stored Markdown files and their front matter as the local source of truth
- Reports archive status, including missing or failed transcripts

## Quick start

1. Create a virtual environment and install the project:

```bash
uv venv
uv pip install -e .
```

2. Sync the two most recent episodes into the current directory:

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

With `--force`, the tool compares a lightweight checksum built from remote metadata headers. If the checksum matches the stored `source_sha`, it skips the full transcript download.

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
- `-v`, `--verbose`: print fetch progress to stderr during sync
- `-d`, `--archive-dest PATH`: set the archive root directory (default: current directory)

### `sync` options

- `--year YYYY`: sync only one archive year; omit to sync all discovered years
- `--latest N`: sync only the most recent `N` episodes
- `--force`: re-check existing episodes and rewrite only when the remote metadata checksum changes
- `--dry-run`: plan work without writing output files
- `--pause-seconds FLOAT`: delay between HTTP requests (default `2.0`)
- `--timeout-seconds FLOAT`: request timeout in seconds (default `20.0`)
- `--max-retries N`: number of retries for transient fetch failures (default `2`)
- `--backoff-seconds FLOAT`: base delay for retry backoff in seconds (default `5.0`)
- `--source-preference {auto,txt,html}`: transcript source preference (default `auto`)

### `status` options

- `--missing`: list only non-present episodes
- `--json`: emit JSON instead of text

### Exit codes

#### `grc sync`

- `0`: all requested work completed successfully
- `2`: completed with one or more `remote_missing`, `fetch_error`, or `parse_error` results
- `1`: fatal error

#### `grc status`

- `0`: archive is readable and has no non-present states
- `2`: archive is readable and contains one or more non-present states
- `1`: fatal error

## Archive layout

The tool stores one Markdown file per episode directly in the archive root:

```text
./
  sn-0001-as-the-worm-turns-the-first-internet-worms-of-2005.md
  sn-1000-security-now-1000.md
  sn-1074-what-mythos-means.md
```

Each file includes YAML front matter with episode metadata followed by the full transcript body.

## Run tests

Run the offline test suite with:

```bash
uv run python -m unittest discover -s tests
```

All tests run offline against local fixtures. No test hits the live site.

## Scripts

### `scripts/bump-version.sh`

Bumps the project version in release files.

**Arguments:** `patch`, `minor`, or `major`

```bash
scripts/bump-version.sh minor
```

### `scripts/validate-worklog.sh`

Validates a worklog file against the required front-matter format before commit.

**Arguments:** path to a worklog file

```bash
scripts/validate-worklog.sh docs/worklogs/2026-04-26-12-13-grc-package-rename.md
```

## Contributing

- Keep all tests offline — no test may hit the live site
- Keep source code under `src/`
- Keep tests under `tests/`
- Run the full test suite before submitting changes
- Update `BLUEPRINT.md` and `CONTEXT.md` when behavior changes
