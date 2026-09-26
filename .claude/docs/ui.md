# ncurses UI (`src/ui.c`)

Entry: `runInteractiveUI(Board *b)`. It is called from `main` when there is no `-f`/`-g`, or when `-i` is passed.
It edits `b` in place and always returns (exit 0).

## Screen layout

| Row | Content |
|---|---|
| 0–12 | Grid, same shape as `printPuzzle` |
| 14–15 | Key help (`STATUS_ROW`) |
| 16 | Message line (`MESSAGE_ROW + 1`) |

Cell mapping: `screenRow(r) = 1 + r + r/3` and `screenCol(c) = 2 + 3c + c/3`. The terminal cursor sits on
the selected cell. It is the only selection indicator (no highlight).

## State

- `curR`, `curC`: cursor position.
- `fixed[9][9]`: cells drawn **bold**. It is set from non-zero cells on entry, after `g` and after `c`,
  and also for each digit the user types. Solver-filled digits are **not** marked, so they render normal weight.
  `fixed` is display-only and does not lock cells.

## Keys

| Key | Action |
|---|---|
| arrows / `hjkl` | Move, clamped to the grid (no wrap) |
| `1`–`9` | `boardSetCell`. On a conflict it shows the conflict message and waits for a key. |
| `0`, space, Backspace (`KEY_BACKSPACE` or 127) | Clear the cell |
| `s` | `solveBoard` on a copy. Shows `Solved.` or `No solution for this board.` and waits for a key. |
| `g` | `generatePuzzle(b, 32)`, replacing the board |
| `c` | `boardInit`, empty board |
| `q` | `endwin()` and return |

## Gotchas

- The loop redraws everything each iteration (`erase` + `drawGrid`). There are no windows or colors.
- `boardSetCell` does not refresh `candidates`. That is fine here because `solveBoard` recomputes them.
  Anything new that reads masks must call `computeCandidates` first.
- There are no automated tests. After any change: `make run`, then check move, enter, conflict, solve,
  unsolvable, `g`, `c`, `q`, and that the terminal is restored after `q`.
- Terminal resize is not handled.
