"""Bridge to the C solver: pipe an 81-char puzzle into `./sudoku -f -`."""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if getattr(sys, "frozen", False):     # PyInstaller bundle: sudoku.exe is unpacked next to the code
    REPO_ROOT = sys._MEIPASS
BINARY = os.path.join(REPO_ROOT, "sudoku.exe" if os.name == "nt" else "sudoku")


class SolveError(Exception):
    pass


def solve(puzzle, binary=BINARY):
    """81-char puzzle ('.' = empty) -> list of 81 ints. Raises SolveError."""
    if not os.path.exists(binary):
        raise SolveError("solver binary not found: %s (run `make` in the repo root)" % binary)

    proc = subprocess.run([binary, "-f", "-"], input=puzzle + "\n",
                          capture_output=True, text=True, timeout=30,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if proc.returncode != 0:
        msg = proc.stderr.strip() or "exit code %d" % proc.returncode
        raise SolveError(msg)

    marker = proc.stdout.find("Solution:")
    if marker < 0:
        raise SolveError("unexpected solver output")
    body = proc.stdout[marker + len("Solution:"):]
    values = [int(ch) for ch in body if ch in "123456789"]
    if len(values) != 81:
        raise SolveError("solver returned %d digits" % len(values))
    return values
