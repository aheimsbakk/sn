from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .archive_state import load_archive_state
from .http import HttpClient
from .status import (
    list_non_present,
    render_status_json,
    render_status_text,
    summarize_archive_state,
)
from .sync import sync_archive
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sn")
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-d", "--archive-dest", default=".")

    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--year", type=int)
    sync_parser.add_argument("--latest", type=int)
    sync_parser.add_argument("--force", action="store_true")
    sync_parser.add_argument("--dry-run", action="store_true")
    sync_parser.add_argument("--pause-seconds", type=float, default=2.0)
    sync_parser.add_argument("--timeout-seconds", type=float, default=20.0)
    sync_parser.add_argument("--max-retries", type=int, default=2)
    sync_parser.add_argument("--backoff-seconds", type=float, default=5.0)
    sync_parser.add_argument(
        "--source-preference", choices=("auto", "txt", "html"), default="auto"
    )

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--missing", action="store_true")
    status_parser.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    archive_root = Path(args.archive_dest).resolve()

    if args.command == "sync":
        client = HttpClient(
            pause_seconds=args.pause_seconds,
            timeout_seconds=args.timeout_seconds,
            max_retries=args.max_retries,
            backoff_seconds=args.backoff_seconds,
        )
        exit_code, archive_state = sync_archive(
            archive_root,
            client=client,
            year=args.year,
            latest=args.latest,
            force=args.force,
            dry_run=args.dry_run,
            source_preference=args.source_preference,
            verbose=args.verbose,
            output=sys.stderr,
        )
        summary = summarize_archive_state(archive_state)
        print(render_status_text(summary))
        return exit_code

    archive_state = load_archive_state(archive_root)
    summary = summarize_archive_state(archive_state)
    missing = list_non_present(archive_state) if args.missing else None
    if args.json:
        print(render_status_json(summary, missing))
    else:
        print(render_status_text(summary, missing))
    if missing or any(
        summary[key] for key in ("remote_missing", "fetch_error", "parse_error")
    ):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
