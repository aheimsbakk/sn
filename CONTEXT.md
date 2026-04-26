# Context

## Project status

Phase 1 scaffold exists. The package, CLI, core sync modules, and offline tests are in place.

## Current goal

Build out the Python CLI named `grc` from the Phase 1 archive plan.

Phase 1 includes:

- `grc sync`
- `grc status`

## Locked decisions

- source code lives under `src/`
- tests live under `tests/`
- project must be installable with `uv`
- tests must stay offline
- transcripts are stored locally as UTF-8 Markdown
- text transcripts are the primary source
- HTML transcripts are a fallback source
- default archive destination is the current working directory
- output archive directory is changeable with `-d` / `--archive-dest`
- sync must be serial and polite to `grc.com`
- preserve source license text in front matter when present
- prefer Python standard library functionality where practical
- tests use `unittest`
- exit codes are `0` success, `1` error, `2` partial error
- use `lxml` directly for HTML parsing
- use `PyYAML` for front matter output
- existing archived transcripts are only refreshed with `--force`
- title slug length is capped at 32 characters and filenames always include the episode number
- sync timeout, retry count, and backoff have defaults and are configurable

## Implemented now

- `pyproject.toml` with `setuptools` build backend and `uv`-friendly editable install
- distribution package name `grc` so `uvx grc` works without `--from`
- tests run directly with `uv run python -m unittest discover -s tests`
- supported package `grc` under `src/`
- `grc sync` argument parsing and orchestration flow
- `grc status` text and JSON output
- polite HTTP client with user agent, timeout, pause, and retry support
- archive index parsing for main and yearly pages
- text transcript parsing with header alias support
- HTML transcript fallback parsing
- Markdown writer with YAML front matter
- manifest storage in `.grc-sync/manifest.json`
- offline `unittest` coverage for core modules
- real offline fixtures downloaded from GRC for episodes 1000 and 1074 plus the main archive page

## Known gaps

- no `__main__.py` module yet; the supported entry point is the `grc` console script
- no yearly archive fixture yet; current real fixture coverage uses the main archive page plus two real episodes
- `grc sync -v` now prints fetch progress to stderr for archive pages, transcript fetches, and stored files
- sync now saves the manifest in a `finally` block so completed work remains visible after an interrupt
- HTML parsing is intentionally conservative and may need refinement against real pages

## Metadata decision

Normalize transcript metadata across old and new transcripts.

Key normalized fields:

- `series`
- `episode`
- `title`
- `published`
- `speakers`
- `description`
- `audio_url`
- `transcript_url`
- `source_format`
- `original_encoding`
- `license`

## Sync status behavior

- missing transcripts are recorded locally
- missing transcripts are retried on later runs
- `grc status` reports missing items, local counts, and general archive status
- non-present states are `remote_missing`, `fetch_error`, and `parse_error`
- `grc status` exits `2` when non-present states exist

## Deferred work

- search command
- indexing strategy
- any non-sync features
