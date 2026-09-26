# I/O Formats and CLI Contract

## Puzzle input (`src/input.c`)

- `parseBoardString(b, text)`: scans characters in order.
  - `1`–`9` → digit. `0 . _ *` → empty. **Every other character is skipped** (spaces, newlines, `|`, `-`, letters).
  - Fails (returns 0, message on stderr) if:
    - there are more than 81 cells: `Error: input has more than 81 cells`
    - there are fewer than 81: `Error: expected 81 cells, got K`
    - a filled digit is duplicated in a unit: `Error: puzzle is invalid (duplicate digit in a row, column or box)`
  - On success it calls `computeCandidates`.
- `loadBoardFromStream` reads up to **4095 bytes** into a stack buffer. Anything beyond is silently dropped.
- `loadBoardFromFile` prints `Error: cannot open '<path>'` if `fopen` fails.
- The parser checks duplicates only. Solvability is decided later by `solveBoard`.

## Output (stdout), which tests and README pipelines parse

Solve mode:
```
Puzzle:
<grid>
Solution:
<grid>
```
Generate mode (first line is dropped by `tail -n +2` in the documented pipelines):
```
Generated puzzle (<actual clue count> clues):
<grid>
```
Grid (`printPuzzle`): 13 lines. Separator lines are exactly 31 `-`. Each row reads `|` then for every
cell ` d ` (or ` . ` if empty) with `|` after every 3rd cell, e.g.
```
-------------------------------
| 5  3  . | .  7  . | .  .  . |
```
Printed grids use `.` for empty cells, which the parser accepts, so output can be fed back as input.

## stderr and exit codes

| Condition | Stream / message | Exit |
|---|---|---|
| Success (solve, generate, `-h`, interactive) | stdout | 0 |
| Parse / validation error | stderr `Error: …` | 1 |
| Valid but unsolvable | stdout puzzle, stderr `No solution.` | 1 |
| Unknown option or `-f` without a path | stderr `Unknown option: X` + usage on stdout | 2 |

Note: `-f` as the last argument (no path) falls through to "Unknown option: -f" (exit 2).

## Changing any of this

Update, in the same change: `tests/run_tests.sh` (`solution_digits` parses from `Solution:`),
README.md §3–5 (Vietnamese), and `usage()` in `src/sudoku.c`.
