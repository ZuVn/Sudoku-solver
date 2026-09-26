# CLAUDE.md

## 1. Project Overview

Sudoku_solver finds a 9×9 Sudoku board shown on screen (e.g. in Google Chrome), reads the givens and empty
cells, solves it, then moves the mouse and types the answers into the empty cells.
Two layers: a **C/ncurses core** (`src/`, binary `./sudoku`: parse, solve, generate, terminal UI) and a
**Python automation layer** (`automation/sudoku_auto/`: screen capture, grid/digit detection, virtual
mouse/keyboard, Tk window). The Python layer calls the C binary to solve and never re-implements the solver.

## 2. Tech Stack

- C, compiled with `gcc` (developed on 15.2, no `-std` flag, so gcc's default `gnu17`)
- `ncurses` 6.x (`libncurses-dev`), used only by `src/ui.c`
- GNU Make 4.x (`makefile`, lowercase)
- Bash 5 for `tests/run_tests.sh`
- Python 3.14 in `.venv/` (created with `--system-site-packages`): `numpy`, `pillow`,
  system `python3-gi` (xdg-desktop-portal screenshot), system `python3-tk` (GUI)
- `/dev/uinput` for synthetic input (the user needs rw access). No xdotool, OpenCV or OCR engine.
- Linux only. Target desktop: GNOME on Wayland (X11 also works). Single monitor assumed.

## 3. Dev Commands

```bash
sudo apt install build-essential libncurses-dev python3-gi python3-tk python3-venv
make            # build ./sudoku (objects go to obj/)
make run        # build, then open the interactive ncurses UI
make test       # build, then run tests/run_tests.sh (expects "8 passed, 0 failed")
make clean      # remove obj/ and ./sudoku
make auto-setup # create .venv (system site packages) + pip install automation/requirements.txt
make auto       # open the Tk window: Scan → Fill (types into the screen!)
make auto-scan  # capture + detect + solve, print only (no typing)
make auto-test  # Python unit tests (expects "Ran 17 tests ... OK")
```

There is no dev server and no release build. The build is always `-Wall -Wextra -g`.

Run it:

```bash
./sudoku -f tests/easy.txt           # solve a puzzle file
echo "<81 chars>" | ./sudoku -f -    # solve from stdin
./sudoku -g 28                       # generate a puzzle with a unique solution (~28 clues)
./sudoku -f tests/easy.txt -i        # load the puzzle into the ncurses UI
cd automation && ../.venv/bin/python -m sudoku_auto --image tests/fixtures/websudoku.png   # offline detect
```

Exit codes: `0` ok, `1` bad input / duplicate digit / no solution, `2` unknown option.

## 4. Core Logic Summary

- **Board** = `cells[9][9]` (0 = empty) + `candidates[9][9]` (9-bit mask, bit `d-1` set = digit `d` still allowed).
- **Propagation** (`propagate`): repeat *naked single* + *hidden single* until nothing changes.
  Return 0 on contradiction.
- **Weight / cell choice** (`pickCell`): the weight of an empty cell is `popcount9(candidates)`, the number of
  digits still allowed there. Search branches on the lowest-weight cell (MRV heuristic). Ties go to the
  first cell in row-major order.
- **Search** (`search`): recursive backtracking. Each branch works on a full stack copy of `Board`.
  It returns the solution count, capped at `limit`.
- **Uniqueness** (`countSolutions(b, 2) == 1`): the generator uses this to decide whether a clue can be removed.
- **Automation pipeline**: portal screenshot → locate the grid from its 4 thick box lines → classify each cell
  by template correlation (fonts rendered at runtime) → `./sudoku -f -` → click and type **only empty cells**
  through uinput → optional re-scan to verify.

Full details: [.claude/docs/solver_algorithm.md](.claude/docs/solver_algorithm.md),
[.claude/docs/screen_automation.md](.claude/docs/screen_automation.md).

## 5. Key Constraints

Never change these without being asked:

1. **Output format is a contract.** `tests/run_tests.sh` parses the line `Solution:` and the grid printed by
   `printPuzzle`. The README pipelines drop the first line of `-g` output with `tail -n +2`. Changing the
   header text, the grid characters or the line order breaks the tests and the documented usage.
2. **Exit codes 0/1/2** are part of the CLI interface. The tests check exit code 1.
3. **Candidate bit layout** `bitOf(d) = 1 << (d-1)` and `POSSIBLE = 0x1FF` are used by every module.
4. **`solveBoard` leaves the input unchanged when it fails.** It works on a copy. The UI depends on this.
5. **Grid size is fixed at 9×9** (`N`, `BOX` in `board.h`). Do not generalize.
6. **Input parser ignores** any character other than `1-9 0 . _ *`, and stops reading at 4095 bytes.
   Puzzle files in `tests/` rely on this.
7. **Code style:** Allman braces, 4-space indent, `camelCase` functions, variables declared at the top of the
   block, `static` for file-local helpers, include guards `NAME_H`. Match it.
8. **Keep ncurses in `ui.c` only.** `board`/`input`/`solver`/`generator` must stay headless so a future
   automation layer can reuse them. Capture, GUI and OS-input code live only in `automation/`.
10. **Automation never types into given cells** and refuses to type when a read is unsure
    (score < `MIN_SCORE`) or unsolvable. Keep the Stop / Esc / `SIGUSR1` kill switches working.
11. **Never trigger a real Fill (uinput) or `make auto` yourself** without asking. It moves the user's real
    mouse. Use `--image`, fixtures and `FakeDevice` tests.
9. **Branch manager**: Before adding any futures or fix bugs, always work on a new git branch. Never commit direcly on main. Bug branches must follow naming convention bug/[des], future branches follow naming convention futures/[desc]

Never assume:

- That Chrome-specific APIs are used. Detection is purely from pixels. Any site with a lined grid should work.
- That xdotool/X11 capture works. The session is Wayland, so use the portal and uinput.
- That the ncurses UI or live capture/uinput are covered by tests. They are not. Test them by hand.
- That a crash is a code bug before checking the filesystem. Binaries built on an NTFS mount
  (`/run/media/...`) segfault even on `-h`. Build on ext4.
- That build output is in git. `.gitignore` excludes `obj/`, `/sudoku`, `__pycache__/`, `.venv/` and
  `.claude/settings.local.json`. A fresh clone must run `make` (and `make auto-setup`). Never force-add these.
- That `-g N` gives exactly N clues. `N` is clamped to 17..81. Removal stops once uniqueness would break,
  so the real count is often higher.
- That the project is in English only. README and user communication are in Vietnamese. Code and comments
  are in English.

## 6. Additional Documentation

Read the file that matches your task before editing that area:

| Doc | Read when |
|---|---|
| [.claude/docs/architecture.md](.claude/docs/architecture.md) | Adding a module, changing `main`/CLI flags, tracing data flow |
| [.claude/docs/data_model.md](.claude/docs/data_model.md) | Touching `Board`, candidate masks, helper functions in `board.h` |
| [.claude/docs/solver_algorithm.md](.claude/docs/solver_algorithm.md) | Changing propagation, MRV weighting, search, counting, generation |
| [.claude/docs/io_formats.md](.claude/docs/io_formats.md) | Changing the parser, printed output, error messages, exit codes |
| [.claude/docs/ui.md](.claude/docs/ui.md) | Editing the ncurses editor (`src/ui.c`) |
| [.claude/docs/testing.md](.claude/docs/testing.md) | Adding tests or puzzle fixtures, debugging failures |
| [.claude/docs/screen_automation.md](.claude/docs/screen_automation.md) | Anything in `automation/`: capture, detection, digits, uinput, GUI, kill switches |

User-facing usage (Vietnamese): [README.md](README.md).
