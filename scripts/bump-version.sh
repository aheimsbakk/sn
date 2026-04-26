#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'Usage: scripts/bump-version.sh [patch|minor|major]\n' >&2
	exit 1
fi

bump_type="$1"
case "$bump_type" in
patch | minor | major) ;;
*)
	printf 'Usage: scripts/bump-version.sh [patch|minor|major]\n' >&2
	exit 1
	;;
esac

uv run python - "$bump_type" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path.cwd()
bump_type = sys.argv[1]
pyproject_path = root / "pyproject.toml"
version_path = root / "src" / "grc" / "version.py"
http_path = root / "src" / "grc" / "http.py"
blueprint_path = root / "BLUEPRINT.md"

pyproject_text = pyproject_path.read_text(encoding="utf-8")
match = re.search(r'^version = "(\d+)\.(\d+)\.(\d+)"$', pyproject_text, re.MULTILINE)
if not match:
    raise SystemExit("Could not find project version in pyproject.toml")

major, minor, patch = (int(part) for part in match.groups())
if bump_type == "patch":
    patch += 1
elif bump_type == "minor":
    minor += 1
    patch = 0
else:
    major += 1
    minor = 0
    patch = 0

new_version = f"{major}.{minor}.{patch}"

def replace_version(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"Could not update version in {path}")
    path.write_text(updated, encoding="utf-8")

replace_version(pyproject_path, r'^version = ".*"$', f'version = "{new_version}"')
replace_version(version_path, r'^__version__ = ".*"$', f'__version__ = "{new_version}"')
replace_version(http_path, r'^USER_AGENT = ".*"$', f'USER_AGENT = "grc/{new_version} (+https://www.grc.com/)"')
replace_version(blueprint_path, r'^- current version: `.*`$', f'- current version: `{new_version}`')

print(new_version)
PY
