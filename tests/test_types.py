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
import sys
import unittest

from mypy.main import main  # type: ignore


class Types(unittest.TestCase):
    def test_types(self) -> None:
        directory = os.path.join(os.path.dirname(__file__), "..")
        try:
            main(
                None,
                args=["--exclude", "build", directory],
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            exit_code = 0
        except SystemExit as system_exit:
            exit_code = system_exit.code
        self.assertEqual(exit_code, 0)
