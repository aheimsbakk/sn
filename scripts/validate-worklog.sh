#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'Usage: scripts/validate-worklog.sh docs/worklogs/<file>.md\n' >&2
	exit 1
fi

uv run python - "$1" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(f"Worklog not found: {path}")

text = path.read_text(encoding="utf-8")
lines = text.splitlines()
if len(lines) < 8 or lines[0] != "---":
    raise SystemExit("Worklog must start with YAML front matter")

try:
    closing_index = lines.index("---", 1)
except ValueError as error:
    raise SystemExit("Worklog front matter must end with ---") from error

front_matter = lines[1:closing_index]
expected_keys = ["when", "why", "what", "model", "tags"]
keys = []
for line in front_matter:
    if ":" not in line:
        raise SystemExit("Invalid front matter line")
    keys.append(line.split(":", 1)[0].strip())

if keys != expected_keys:
    raise SystemExit("Worklog front matter keys must be when, why, what, model, tags")

body = [line for line in lines[closing_index + 1 :] if line.strip()]
if not 1 <= len(body) <= 4:
    raise SystemExit("Worklog body must be 1-4 non-empty lines")
PY
