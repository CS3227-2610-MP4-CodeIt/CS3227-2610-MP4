"""Regression test for Git's UTF-8 output on Windows legacy code pages."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib.git_workspace import git


class GitUtf8Tests(unittest.TestCase):
    def test_git_output_decodes_utf8_independent_of_system_locale(self):
        original_run = subprocess.run

        def emit_git_output(_command, **kwargs):
            return original_run(
                [sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([0xe2,0x80,0x9d]))"],
                **kwargs,
            )

        with patch("_lib.git_workspace.subprocess.run", side_effect=emit_git_output):
            result = git(Path.cwd(), "diff")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "\u201d")


if __name__ == "__main__":
    unittest.main()
