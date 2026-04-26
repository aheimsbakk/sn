# sn

`sn` is a Python command-line tool that downloads Security Now transcripts from GRC and stores them as local Markdown files.

Source: <https://github.com/aheimsbakk/sn>

## What it does

- Syncs transcript files from the GRC Security Now archive
- Stores each transcript as a UTF-8 Markdown file with YAML front matter
- Records a lightweight metadata checksum (`source_sha`) in front matter to detect remote changes
- Reads stored Markdown files and their front matter as the local source of truth
- Reports archive status, including missing or failed transcripts

## Quick start

Sync the two most recent episodes into the current directory:

```bash
uvx --from git+https://github.com/aheimsbakk/sn sn sync --latest 2
```

Check archive status:

```bash
uvx --from git+https://github.com/aheimsbakk/sn sn status
```

The tool writes transcript Markdown files directly into the chosen archive directory.

## Usage

Install the tool for repeated use:

```bash
uv tool install git+https://github.com/aheimsbakk/sn
```

After installation, run `sn` directly. For one-off use without installing, replace `sn` with `uvx --from git+https://github.com/aheimsbakk/sn sn` in any command below.

### Show help

```bash
sn --help
```

### Sync transcripts

Sync the latest five episodes:

```bash
sn sync --latest 5
```

Sync one archive year:

```bash
sn sync --year 2005
```

Sync all discovered years:

```bash
sn sync
```

Sync into a different archive directory:

```bash
sn -d ./archive sync --latest 3
```

See what would happen without writing files:

```bash
sn sync --latest 2 --dry-run
```

Re-check episodes even if they already exist locally:

```bash
sn sync --latest 2 --force
```

With `--force`, the tool compares a lightweight checksum built from remote metadata headers. If the checksum matches the stored `source_sha`, it skips the full transcript download.

Prefer HTML transcripts instead of text transcripts:

```bash
sn sync --latest 2 --source-preference html
```

### Check archive status

Show summary counts:

```bash
sn status
```

Show only non-present episodes:

```bash
sn status --missing
```

Get machine-readable output:

```bash
sn status --json
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

#### `sn sync`

- `0`: all requested work completed successfully
- `2`: completed with one or more `remote_missing`, `fetch_error`, or `parse_error` results
- `1`: fatal error

#### `sn status`

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

## Development

Clone the repository and run the offline test suite:

```bash
git clone https://github.com/aheimsbakk/sn
cd sn
uv run python -m unittest discover -s tests
```

All tests run offline against local fixtures. No test hits the live site.

## Scripts

### `scripts/bump-version.sh`

Bumps the project version, commits the change, and applies floating semver tags via `gitsem`.

**Arguments:** `patch`, `minor`, or `major`

The working tree must be clean before running this script. It will refuse to run otherwise, to ensure the tag always lands on the correct commit.

```bash
scripts/bump-version.sh minor
```

After review, push the tags to the remote:

```bash
uvx --from git+https://github.com/aheimsbakk/gitsem gitsem --push
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
