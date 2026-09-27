# Screen Automation (`automation/sudoku_auto/`)

Python layer that finds a Sudoku board on screen (e.g. in Chrome), solves it with the C binary, and types
the answers with a virtual mouse and keyboard. Built for **GNOME on Wayland**. It also works on X11,
because both the portal and uinput work there.

## Decisions (made by the user, do not change without asking)

| Topic | Choice | Why |
|---|---|---|
| Capture | xdg-desktop-portal `Screenshot` (non-interactive) via PyGObject | The only supported full-screen capture on GNOME Wayland. X11 grabs and `gnome-screenshot` do not work there. |
| Input | `/dev/uinput` virtual devices (absolute pointer + keyboard) | xdotool does not work on Wayland. uinput is compositor-agnostic. The user has rw ACL on `/dev/uinput`. |
| Site support | Generic: line detection + font-rendered templates | No site-specific tuning. |
| Interface | Tk window (`gui.py`) + CLI flags (`__main__.py`) | Tk is part of the stdlib and the OS packages. |
| Dependencies | `numpy`, `pillow`, system `python3-gi`, `python3-tk` | No OpenCV, no OCR engine. The venv is created with `--system-site-packages` to reach `gi`. |

## Modules

| File | Role |
|---|---|
| `capture.py` | `capture()` → full-screen RGB PIL image. It calls the portal, waits for the `Request.Response` signal on a private `GLib.MainContext`, loads the PNG, then **deletes it**. |
| `detect.py` | `findGrid(gray)` → `Grid(xs[10], ys[10])`. `readCells` classifies 81 cells. `scanImage(img)` → `Scan` or `None`. |
| `digits.py` | Template matching: `defaultTemplates()` (cached) and `classifyCell(crop)` → `(digit or 0, score)`. |
| `solver.py` | `solve(puzzle81)` pipes into `../sudoku -f -` and parses after `Solution:`. Raises `SolveError`. |
| `pipeline.py` | `analyse(img)` → `(scan, solution)`. It rejects a missing grid, low scores, a full board, and unsolvable reads. `reanalyse(img, solution)` re-reads a partly filled board for Resume and rejects any digit that disagrees with the solution. |
| `uinput.py` | Raw ioctl uinput: `Pointer` (ABS_X/ABS_Y range = screenshot size, BTN_LEFT), `Keyboard` (KEY_1..KEY_9), `VirtualInput` context manager with a 1 s settle time. |
| `filler.py` | `plan` (empty cells only, row-major), `fill(..., stopEvent)`. |
| `gui.py` | Tk window with Scan / Fill / Stop-Resume (one toggle button), preview and delay. Workers post to a queue that the main thread polls every 50 ms. |
| `__main__.py` | `--image PNG`, `--scan`, `--fill`, `--save`, `--delay`, `--countdown`. No flag starts the GUI. |

## Grid detection (`detect.py`)

1. Convert to gray. Try the mask `gray < t` for `t` in `THRESHOLDS = (100, 150, 190, 215)`, then the same on
   the inverted image (dark themes). The first grid found wins.
2. Collect horizontal dark runs ≥ `max(150, min(h, w) / 12)` px (vectorised `np.diff`). Cluster the runs
   sharing the same `(x0, x1)` within ±4 px.
3. In each cluster, merge adjacent rows into lines and drop lines thicker than `side / 30`, which removes
   highlighted rows. Look for a top line with box lines at `top + k·side/3`, for k = 1, 2, 3.
4. Confirm vertical box lines using a column profile (≥ 85 % dark over the grid height).
5. `fitLines` keeps detected thin lines when present, otherwise it interpolates. The largest grid wins.

**Assumption:** box lines (every 3rd line) are at least as dark as thin lines and pass at least one
threshold. Grids drawn without lines, or drawn only with cell backgrounds, are not detected.

## Digit reading (`digits.py`)

- Crop each cell with a 12 % margin. Background = median. Ink = `|gray − bg| > max(30, 0.45·peak)`.
  A peak contrast < 50 means empty.
- Keep only the largest **8-connected** component. At small sizes an 8's loops touch only diagonally,
  so 4-connectivity would break it. If its height is < 40 % of the crop, the cell is empty,
  which filters out pencil marks.
- Normalise (pad to square → 24×24 → blur 0.8 → zero mean, unit norm). Take the best dot product against
  templates rendered from system fonts (DejaVu, Liberation, Free, Noto, Ubuntu, and Roboto/OpenSans/Arial if
  present; sans + serif, regular + bold).
- `pipeline.MIN_SCORE = 0.6`. Real fixtures score ≥ 0.91.

## Filling

- Pointer coordinates are **screenshot pixels**. The absolute device range equals the screenshot size, so
  HiDPI and fractional scaling cancel out. **Assumes a single monitor.** With several monitors, the mapping
  of an absolute device to the stitched screenshot is untested.
- Per cell: move → 30 ms → click → 30 ms → key → `delay` (default 80 ms). Givens are never clicked.
- Keys are the top-row KEY_1..KEY_9. This assumes a layout where those keys produce digits without Shift
  (US or Vietnamese: yes. AZERTY: no).
- **Resume:** a stop during typing keeps the fill resumable. Resume re-captures the screen, calls
  `pipeline.reanalyse` (every digit on screen must match the stored solution, so a scrolled page is fine but
  a different puzzle is refused), then types only the cells still empty, at the new grid position.

## Safety / kill switches

- Tk: the **Stop/Resume** toggle and **F2** stop while busy and resume a stopped fill when idle. **Esc** only stops.
  Tk keys work only when the window has focus, so in practice only during the countdown: the first click gives
  focus to the browser. Mid-fill, F2 works through the global GNOME shortcut below. There is a 3 s countdown before filling.
- Global: `SIGUSR1` sets the stop event directly in the signal handler (GUI and `--fill`). In the GUI, a
  `SIGUSR1` while idle and paused sets `resumePending`, which `poll()` turns into a resume (CLI `--fill` has no resume). Bind a GNOME custom shortcut to
  `pkill -USR1 -f '^[^ ]*python[^ ]* -m sudoku_auto'` (installed on the user's machine as F2, gsettings path
  `.../custom-keybindings/sudoku-auto-stop/`). The anchored pattern matters: a bare `-f sudoku_auto` also hits
  the `sh -c` of `make auto` or an editor with that path open, and SIGUSR1 kills those. On Wayland this is the
  only global hotkey path. Reading `/dev/input` needs the
  `input` group, which the user does not have.
- CLI `--fill`: Ctrl+C in the terminal.
- The Tk window hides during each capture. Before filling, it moves away if it overlaps the board.
- Refusal rules (nothing is typed): no grid, any cell score < 0.6, full board, duplicate or unsolvable read.

## Tests (`automation/tests/`, run with `make auto-test`)

- `fixtures/websudoku.png`, `fixtures/sudokuonline.png`: real headless-Chrome screenshots (1600×1000),
  with the expected strings read by hand in `test_auto.py`.
- `synth.py` renders fake pages (light/dark theme, pencil marks, highlighted row, small grid, bold/serif fonts,
  decoy 1×9 number pad).
- `FakeDevice` checks that fill types only empty cells, clicks at the right centres, and honours stop.
- Not automated: the portal and uinput on a live desktop. Test by hand with `make auto` on a real site.

## Known limitations

- sudoku.com could not be captured headlessly (it times out), so it has no fixture. NYT shows a popup over the grid.
- Cells with pre-filled wrong user digits are read as givens. The solver then refuses.
- Wayland portal capture takes about 1.5 s per scan.
