"""
aquaorder
Copyright (C) 2022  schnusch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os.path
import subprocess
import sys
import unittest


class TSC(unittest.TestCase):
    def test_tsc(self) -> None:
        args = [
            "tsc",
            "--noEmit",
            "--noErrorTruncation",
            "--noUnusedParameters",
            "--strict",
            "--moduleResolution",
            "node",
            "--target",
            "es6",
            "src/script.ts",
        ]
        print(*args, file=sys.stderr)
        directory = os.path.join(os.path.dirname(__file__), "..")
        p = subprocess.run(args, cwd=directory)
        self.assertEqual(p.returncode, 0)
