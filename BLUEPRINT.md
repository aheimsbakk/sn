# Blueprint: `grc` Security Now transcript archiver

## Goal

Build a small Python CLI that syncs Security Now podcast transcripts from GRC into a local UTF-8 Markdown archive.

This phase covers two subcommands:

- `grc sync`
- `grc status`

Search will be added later.

---

## Hard requirements

- Python project installable with `uv`
- Source code under `src/`
- Tests under `tests/`
- Tests must run fully offline
- CLI executable must be named `grc`
- CLI must support:
  - `--help` / `-h`
  - `--version` / `-V`
  - `--verbose` / `-v`
- Must sync transcripts from GRC Security Now archive pages
- Must rewrite every stored file as UTF-8
- Must convert transcripts into pure Markdown
- Default archive destination must be the current working directory
- User must be able to change the destination archive directory with `-d` / `--archive-dest`
- The tool must be polite to `grc.com`
- License text must be preserved in front matter when present
- Exit codes must be:
  - `0` success
  - `1` error
  - `2` partial error
- Prefer Python standard library functionality where practical
- Use `unittest` for the test suite

---

## What we learned from sample transcripts

I checked recent and old transcripts from both `.txt` and `.htm` sources.

### Observed `.txt` structure

Recent text transcripts include structured headers such as:

- `SERIES`
- `EPISODE`
- `DATE`
- `TITLE`
- `HOSTS`
- `SOURCE`
- `ARCHIVE`
- `DESCRIPTION`
- optional `SHOW TEASE`

Older text transcripts use slightly different names:

- `SPEAKERS` instead of `HOSTS`
- `SOURCE FILE` instead of `SOURCE`
- `FILE ARCHIVE` instead of `ARCHIVE`

After the header, the transcript body follows as plain text.

### Observed `.htm` structure

The HTML pages contain the transcript and useful metadata, but they also include site chrome, navigation, footer text, and other noise.

### Decision

Use `.txt` as the primary source because it is:

- smaller
- cleaner
- easier on the site
- easier to parse into Markdown

Use `.htm` only as a fallback when:

- the text transcript is missing
- the text transcript cannot be decoded safely
- the text transcript parses poorly
- the text transcript and HTML transcript disagree, and the text source appears unreliable

If `.txt` and `.htm` disagree, prefer `.htm` as the fallback source when the `.txt` source is missing, malformed, or otherwise unreliable.

---

## Metadata front matter decision

The front matter should help later search, but stay compact.

### Keep in front matter

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
- `source_sha`
- `license`

### Keep in the Markdown body, not front matter

- `SHOW TEASE`
- archive page chrome

Reason:

- `SHOW TEASE` is optional and often long
- site boilerplate is not useful search data
- search later will work better with a stable, small metadata block

Exception:

- preserve license and rights text in front matter when present

### Example front matter

```yaml
---
series: Security Now!
episode: 1074
title: What Mythos Means
published: 2026-04-14
speakers:
  - Steve Gibson
  - Leo Laporte
description: A San Francisco AI developer conference in two weeks. Thank goodness Anthropic was the one who created Mythos rather than any of our cyber adversaries.
audio_url: https://media.grc.com/sn/sn-1074.mp3
transcript_url: https://www.grc.com/sn/sn-1074.txt
source_format: txt
original_encoding: windows-1252
source_sha: 7a673f5d5cbf6f5a3b5ef7a1b8ea4ce9c11f8f8d6fe0f9f3d4d3ca83f0f8f95a
license: Copyright and license text preserved from the source transcript when present.
---
```

---

## Output format

Each synced episode becomes one Markdown file.

### File naming

```text
sn-1074-what-mythos-means.md
```

Rules:

- every filename must include the episode number
- use `sn-<episode>-<slug>.md`
- keep the title slug portion to a maximum of 32 characters
- normalize the slug to lowercase kebab-case

### Body layout

```md
# Security Now! Episode 1074: What Mythos Means

## Description

...

## Show tease

...

## Transcript

**Leo Laporte:** ...

**Steve Gibson:** ...
```

### Markdown conversion rules

- output must be UTF-8
- normalize line endings to `\n`
- use real Unicode punctuation, not HTML entities
- strip site chrome from HTML fallback pages
- keep speaker labels as bold Markdown labels
- preserve paragraph breaks
- do not emit raw HTML in the stored archive

---

## Scope of `grc sync`

`grc sync` should:

1. Read the main archive page at `https://www.grc.com/securitynow.htm`
2. Discover linked yearly archive pages
3. Parse episode listings from current and yearly archive pages
4. Derive transcript URLs for each episode
5. Download only what is needed
6. Convert to normalized Markdown
7. Store files in the chosen archive directory
8. Track local sync state so later runs stay polite and incremental
9. Mark missing transcripts and failures in local state
10. Retry missing transcripts on later runs

By default, `grc sync` should inspect the existing Markdown files in the archive destination and skip episodes that are already stored there. Rewriting changed remote transcripts is a `--force` behavior.

When `--force` is used, the tool should first compare a lightweight metadata-based checksum derived from response headers such as `ETag`, `Last-Modified`, and `Content-Length`. If that checksum matches the `source_sha` stored in the existing Markdown front matter, the tool should skip the full transcript download and keep the existing local file.

---

## CLI design

## Root command

```text
grc [global options] <command> [command options]
```

### Global options

- `-h`, `--help`
- `-V`, `--version`
- `-v`, `--verbose` (repeatable)
  - print fetch progress to stderr during sync so the user can see live work
- `-d`, `--archive-dest PATH`
  - archive root directory
  - default: current working directory

### First command

```text
grc sync
```

### Second command

```text
grc status
```

### `grc sync` options

- `--year YYYY`
  - sync only one archive year
  - when omitted, sync should discover and check all archive years linked from the front page
- `--latest N`
  - sync only the most recent N episodes
- `--force`
  - re-check existing episodes and rewrite only when the remote metadata checksum changes
- `--dry-run`
  - show what would be fetched and written
- `--pause-seconds FLOAT`
  - polite delay between network requests
- `--timeout-seconds FLOAT`
  - per-request timeout
- `--max-retries N`
  - retry count for transient fetch failures
- `--backoff-seconds FLOAT`
  - base delay for retry backoff
- `--source-preference {auto,txt,html}`
  - default: `auto`

### `grc status` options

- `--missing`
  - show only episodes in non-present states
- `--json`
  - machine-readable output

### `grc status` output

At minimum, report:

- total episodes discovered from archive indexes
- total episodes stored locally
- count of `present`
- count of `remote_missing`
- count of `fetch_error`
- count of `parse_error`

When listing non-present episodes, distinguish clearly between:

- `remote_missing`: transcript not currently published on the source site
- `fetch_error`: transcript fetch failed due to timeout, HTTP error, or other network issue
- `parse_error`: transcript was fetched but could not be normalized safely

### Defaults

- `--archive-dest`: current working directory
- `--pause-seconds`: default `2.0`
- `--timeout-seconds`: default `20.0`
- `--max-retries`: default `2`
- `--backoff-seconds`: default `5.0`
- `--source-preference`: default `auto`
- no parallel download mode in v1

### Exit codes

For `grc sync`:

- `0`: all requested work completed successfully
- `2`: command completed, but one or more episodes ended in `remote_missing`, `fetch_error`, or `parse_error`
- `1`: fatal command, configuration, or runtime error

For `grc status`:

- `0`: archive is readable and has no non-present states
- `2`: archive is readable, but contains `remote_missing`, `fetch_error`, or `parse_error` entries
- `1`: fatal command, configuration, or runtime error

Reason for serial sync:

- simpler
- safer
- kinder to `grc.com`

---

## Politeness rules for GRC

The tool must avoid behaving like a crawler.

### Required behavior

- one HTTP request at a time
- default delay of 2 seconds between requests
- clear user agent string
- strict request timeouts
- retry only a small number of times with backoff
- skip existing local episodes by default
- do not re-fetch all history on every run

### Sync strategy

Default sync should:

- fetch archive index pages
- compare discovered episodes with stored Markdown files and their front matter
- download only missing episodes unless `--force` is used
- retry episodes previously marked missing
- avoid checking already archived transcripts for remote changes unless `--force` is used

This keeps normal runs small and polite.

---

## Encoding and normalization strategy

The source files may use different encodings, so decoding must use raw bytes and a strict fallback chain.

### Decode order

1. honor HTTP charset if present
2. check BOM
3. try UTF-8 strict
4. fall back to Windows-1252
5. fall back to Latin-1 only as a last resort

### After decode

- normalize to Python `str`
- normalize newlines
- trim malformed control characters where safe
- always write local files as UTF-8 without BOM
- record the detected original encoding in front matter

Reason:

- prefer built-in Python functionality where possible
- keep the runtime dependency set minimal

---

## Archive layout

Given `--archive-dest /path/to/archive`, store:

```text
/path/to/archive/
  sn-0001-as-the-worm-turns-the-first-internet-worms-of-2005.md
  sn-1074-what-mythos-means.md
```

The archive directory itself is the source of truth. The tool must scan stored Markdown files, read their front matter, and use the actual files on disk to determine local state rather than relying on a separate manifest file.

---

## Python package layout

```text
src/
  grc/
    __init__.py
    cli.py
    version.py
    models.py
    archive_index.py
    http.py
    text_parser.py
    html_parser.py
    normalize.py
    markdown_writer.py
    archive_state.py
    sync.py
    status.py
tests/
  fixtures/
    archive/
    transcripts/
  test_cli.py
  test_archive_index.py
  test_text_parser.py
  test_html_parser.py
  test_normalize.py
  test_markdown_writer.py
  test_archive_state.py
  test_sync.py
  test_status.py
```

### Module responsibilities

- `cli.py`: argument parsing and command dispatch
- `archive_index.py`: parse current and yearly archive pages
- `http.py`: polite HTTP client, retries, timeouts, user agent
- `text_parser.py`: parse `.txt` transcript headers and body
- `html_parser.py`: parse transcript HTML fallback pages
- `normalize.py`: encoding detection, cleanup, Unicode normalization
- `markdown_writer.py`: front matter and Markdown rendering
- `archive_state.py`: scan stored Markdown files and derive local archive state from front matter
- `sync.py`: orchestration only
- `status.py`: summarize local archive coverage and missing transcripts

Notes:

- `__main__.py` is not required in v1 because the console entry point is `grc`
- `sync.py` now emits simple verbose progress lines directly during archive and transcript fetches

---

## Packaging plan

- project managed by `uv`
- standard `pyproject.toml`
- console script entry point named `grc`
- package import name: `grc`

### Planned runtime stack

- Python 3.12+
- standard library `argparse` for CLI
- standard library `urllib.request` for HTTP
- `lxml` for HTML parsing
- `PyYAML` for YAML front matter writing
- standard library `json`, `pathlib`, `dataclasses`, `re`, and `logging`

Prefer standard library functionality by default, but use `lxml` and `PyYAML` where they clearly reduce complexity and improve output quality.

### Implemented packaging details

- build backend: `setuptools`
- package name: `grc`
- current version: `1.0.1`
- editable install works with `uv pip install -e .`
- tests run with `uv run python -m unittest discover -s tests`

### Planned test stack

- `unittest`
- local fixtures only
- standard-library mocks and local fixture-driven tests

No test should hit the live site.

---

## Parsing rules

### Text transcript parser

Must support header aliases:

- `HOSTS` or `SPEAKERS` -> `speakers`
- `SOURCE` or `SOURCE FILE` -> `audio_url`
- `ARCHIVE` or `FILE ARCHIVE` -> `series_archive_url`
- trailing copyright and license section -> `license`

Must treat these as optional:

- `SHOW TEASE`
- `DESCRIPTION`

Must split transcript body from the header reliably.

### HTML fallback parser

Must:

- remove navigation and footer noise
- locate episode title and description
- extract transcript paragraphs only
- convert speaker labels into the same normalized format as the text parser

Implementation note:

- use `lxml` directly rather than Beautiful Soup wrappers

The final normalized model should be the same no matter which source was used.

### License handling

When source transcripts include copyright or Creative Commons text, preserve that text in normalized front matter.

### Front matter writing

- generate YAML front matter with `PyYAML`
- keep field order stable for readable diffs

---

## Tests

Tests are offline. The suite now includes committed real GRC fixtures under `tests/fixtures/` plus focused inline samples for edge cases.

### Required fixture set

- one recent `.txt` transcript
- one recent `.htm` transcript
- one old `.txt` transcript
- one old `.htm` transcript
- one archive index page
- one yearly archive page
- one sample with non-UTF-8 bytes

### Implemented real fixture set in v1

- `tests/fixtures/archive/securitynow-main.htm`
- `tests/fixtures/transcripts/sn-1000.txt`
- `tests/fixtures/transcripts/sn-1000.htm`
- `tests/fixtures/transcripts/sn-1074.txt`
- `tests/fixtures/transcripts/sn-1074.htm`

These files were fetched politely from `grc.com` and are used only for offline tests.

### Required coverage

- CLI parsing
- archive discovery
- header alias handling
- encoding detection and UTF-8 rewrite
- Markdown output shape
- manifest update logic
- incremental sync planning
- polite request spacing logic
- missing transcript retry behavior
- status command output
- exit code behavior
- distinction between `remote_missing`, `fetch_error`, and `parse_error`

### Implemented coverage in v1

- CLI parsing and status rendering
- archive discovery across main and yearly pages
- text transcript parsing, header aliases, and license capture
- HTML fallback parsing
- real archive and transcript parsing against downloaded GRC fixtures
- encoding fallback to `cp1252`
- Markdown output and target path generation
- manifest persistence
- incremental sync planning
- sync fallback from text to HTML when text parsing fails
- partial exit behavior for missing transcripts

---

## Out of scope for this phase

- search
- full text indexing
- remote change detection for every already-downloaded episode on every run
- parallel downloads
- database storage
- web UI
- atomic writes

---

## First implementation milestone

Build working `grc sync` and `grc status` commands that can:

- install with `uv`
- sync a selected archive year or all discovered years
- store UTF-8 Markdown transcripts in a chosen directory
- run offline tests from fixtures only
- avoid unnecessary load on `grc.com`
- preserve license text in front matter when present
- report missing transcripts, transcript counts, and local archive status
