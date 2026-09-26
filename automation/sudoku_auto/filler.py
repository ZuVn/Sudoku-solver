"""Turn a scan + solution into clicks and key presses."""

import time


class Stopped(Exception):
    pass


def plan(scan, solution):
    """[(r, c, digit)] for every cell that was empty in the scan, row-major."""
    moves = []
    for i, value in enumerate(scan.cells):
        if value == 0:
            moves.append((i // 9, i % 9, solution[i]))
    return moves


def fill(scan, solution, device, stopEvent, delay=0.08, progress=None):
    """Click each empty cell and type its digit. Never touches given cells.

    stopEvent is a threading.Event checked before every move; setting it
    raises Stopped. progress(done, total) is called after each cell.
    """
    moves = plan(scan, solution)
    for done, (r, c, digit) in enumerate(moves, 1):
        if stopEvent.is_set():
            raise Stopped("stopped after %d of %d cells" % (done - 1, len(moves)))
        x, y = scan.grid.cellCenter(r, c)
        device.pointer.moveTo(x, y)
        time.sleep(0.03)
        device.pointer.click()
        time.sleep(0.03)
        device.keyboard.typeDigit(digit)
        time.sleep(delay)
        if progress:
            progress(done, len(moves))
    return len(moves)


def mismatches(scan, solution):
    """Cells whose value on screen differs from the solution: [(r, c, seen, expected)]."""
    out = []
    for i, value in enumerate(scan.cells):
        if value != solution[i]:
            out.append((i // 9, i % 9, value, solution[i]))
    return out
