import io
import importlib.util
import json
import sys
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from grc import cli


class CliTests(unittest.TestCase):
    def test_project_name_matches_cli_command(self) -> None:
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with pyproject_path.open("rb") as handle:
            pyproject = tomllib.load(handle)

        self.assertEqual(pyproject["project"]["name"], "grc")

    def test_console_script_points_to_grc_package(self) -> None:
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with pyproject_path.open("rb") as handle:
            pyproject = tomllib.load(handle)

        self.assertEqual(pyproject["project"]["scripts"]["grc"], "grc.cli:main")

    def test_legacy_grc_sync_package_is_removed(self) -> None:
        self.assertIsNone(importlib.util.find_spec("grc_sync"))

    def test_version_option(self) -> None:
        with self.assertRaises(SystemExit) as context:
            cli.build_parser().parse_args(["--version"])
        self.assertEqual(context.exception.code, 0)

    def test_status_json_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "sn-0001-as-the-show-begins.md").write_text(
                "---\nseries: Security Now!\nepisode: 1\ntitle: As The Show Begins\n---\n\n# Security Now! Episode 1: As The Show Begins\n",
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = cli.main(["-d", temp_dir, "status", "--json"])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(buffer.getvalue())["present"], 1)

    def test_sync_command_uses_sync_archive(self) -> None:
        buffer = io.StringIO()
        with (
            TemporaryDirectory() as temp_dir,
            redirect_stdout(buffer),
            patch("grc.cli.sync_archive", return_value=(0, {"episodes": {}})) as mocked,
        ):
            exit_code = cli.main(["-d", temp_dir, "sync", "--dry-run"])
        self.assertEqual(exit_code, 0)
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.kwargs["verbose"], 0)
        self.assertIs(mocked.call_args.kwargs["output"], sys.stderr)
