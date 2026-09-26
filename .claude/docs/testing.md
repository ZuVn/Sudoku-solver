# Testing

## Running

```bash
make test        # builds first, then runs tests/run_tests.sh from the repo root
```
Expected tail: `8 passed, 0 failed`. The script exits non-zero if any check fails.

Automation layer: `make auto-test` (unittest, 17 tests, about 7 s). See
[screen_automation.md](screen_automation.md#tests-automationtests-run-with-make-auto-test).

## What is checked (`tests/run_tests.sh`)

| Check | Fixture | Pass condition |
|---|---|---|
| easy | `tests/easy.txt` | Valid solved grid that keeps all clues |
| hard17 | `tests/hard17.txt` | Same (17-clue puzzle) |
| invalid_duplicate | `tests/invalid_duplicate.txt` | Exit code 1 |
| unsolvable | `tests/unsolvable.txt` | Exit code 1 |
| stdin | `easy.txt` via `-f -` | Valid solved grid |
| generate round-trip ×3 | `./sudoku -g 28 \| tail -n +2` | Generated puzzle solves and keeps its clues |

Helpers:
- `solution_digits` takes the stdout after the `Solution:` line and keeps only `1-9.`.
- `grid_is_solved` checks 81 chars and that every row, column and box sorts to `123456789`.
- `keeps_clues` checks that the solution matches every given digit.
- `puzzle_digits` normalizes a fixture (`0` → `.`).

## Adding a test

1. Put the fixture in `tests/<name>.txt` (any layout the parser accepts, see [io_formats.md](io_formats.md)).
2. Add `expect_solved "<name>" tests/<name>.txt` or `expect_exit1 …` to `run_tests.sh`.
3. Update the expected count mentioned in CLAUDE.md and the README §7 table.

## Not covered

- The ncurses UI (manual only, see [ui.md](ui.md)).
- Live portal capture and uinput clicking (manual only: `make auto-scan`, then `make auto` on a real site).
- Uniqueness of generated puzzles (only solvability is checked).
- Inputs larger than 4095 bytes, and the `-f`-with-no-path edge case.

## Debugging

- Build flags include `-g`: `gdb -batch -ex run -ex bt --args ./sudoku -f tests/easy.txt`.
- A segfault on startup, even with `-h`, usually means the binary is on an NTFS mount. Move the repo to
  ext4 and rebuild before looking at the code.
