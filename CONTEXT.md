# Context

## Project status

Greenfield project. No application code exists yet.

## Current goal

Build a Python CLI named `grc`.

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
