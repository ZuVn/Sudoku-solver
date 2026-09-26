# Architecture

## Module map

| File | Header | Responsibility | Depends on |
|---|---|---|---|
| `src/sudoku.c` | none | `main`: parse CLI flags, pick a mode, set the exit code | all headers |
| `src/board.c` | `board.h` | `Board` type, validity checks, clue count, `printPuzzle` | libc |
| `src/input.c` | `input.h` | Parse 81-cell text from a string, file or stdin | board, solver (`computeCandidates`) |
| `src/solver.c` | `solver.h` | Candidates, propagation, backtracking, solution counting | board |
| `src/generator.c` | `generator.h` | Seed RNG, build a full random grid, remove cells while the solution stays unique | board, solver |
| `src/ui.c` | `ui.h` | ncurses editor | board, solver, generator, ncurses |

Dependency direction: `sudoku.c → ui → generator → solver → board`. `input → solver → board`.
There are no cycles. Only `ui.c` includes `<ncurses.h>`. Keep it that way.

## Automation layer (`automation/sudoku_auto/`, Python)

`gui`/`__main__` → `pipeline` → (`capture`, `detect` → `digits`, `solver`) and `filler` → `uinput`.
It talks to the C core **only** through the `./sudoku -f -` subprocess (`solver.py`), so C changes to the
output format break it too (it parses from `Solution:`). Details: [screen_automation.md](screen_automation.md).

## Build

- `makefile` compiles every `src/*.c` into `obj/*.o` (a wildcard, so a new `.c` file is picked up without
  editing the makefile) and links `./sudoku` with `-lncurses`.
- Headers are not listed as prerequisites. After editing a `.h` file, run `make clean && make`.
  Otherwise stale objects can link.

## Control flow in `main` (`src/sudoku.c`)

1. Parse argv left to right:
   - `-f <path>` sets the input path (`-` means stdin)
   - `-i` sets interactive mode
   - `-g [n]` sets generate mode. `n` is consumed only if the next arg does not start with `-`, and is read with `atoi`.
   - `-h` prints usage and exits 0
   - Anything else exits 2.
2. `generatorSeed()` is always called (`srand(time(NULL))`).
3. Mode choice (in this priority order):
   - `-f` given: load and validate the board. Exit 1 on failure.
   - else `-g`: `generatePuzzle(&board, clues)`.
   - else: interactive with an empty board.
4. If interactive: `runInteractiveUI(&board)`, then exit 0.
5. If generate: print `Generated puzzle (%d clues):` and the grid, then exit 0.
6. Otherwise print `Puzzle:` + grid, run `solveBoard`, and either print `Solution:` + grid (exit 0) or
   write `No solution.` to stderr (exit 1).

If both `-f` and `-g` are given, `-f` wins and `-g` is ignored, apart from its clue argument being consumed.

## Extension points

- New solving strategy: add it to `propagate` in `solver.c`. See [solver_algorithm.md](solver_algorithm.md).
- New input source: produce an 81-char string and pipe it to `./sudoku -f -` (as `automation/` does), or
  call `parseBoardString` from C.
- New CLI flag: add it to the argv loop and to `usage()` in `sudoku.c`, update README §3, and add a test.
