"""PyInstaller entry point (a package run with -m cannot be frozen directly)."""

import sys

from sudoku_auto.__main__ import main

sys.exit(main())
