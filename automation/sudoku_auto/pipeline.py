"""Screenshot -> detected puzzle -> solution. No input devices involved."""

from . import detect, solver

# Lowest template score accepted for a digit. Below this the read is unreliable.
MIN_SCORE = 0.6


class PipelineError(Exception):
    pass


def analyse(image):
    """Return (scan, solution). Raises PipelineError with a user-facing message."""
    scan = detect.scanImage(image)
    if scan is None:
        raise PipelineError("No 9x9 grid found on screen. Make sure the whole board is visible.")

    weak = [i for i, s in enumerate(scan.scores) if s < MIN_SCORE]
    if weak:
        cells = ", ".join("r%dc%d" % (i // 9 + 1, i % 9 + 1) for i in weak[:5])
        raise PipelineError("Unsure about digits in %s. Not filling." % cells)

    if scan.cells.count(0) == 0:
        raise PipelineError("The board is already full.")

    try:
        solution = solver.solve(scan.puzzleString())
    except solver.SolveError as e:
        raise PipelineError("Detected board cannot be solved (%s). "
                            "A digit was probably misread; nothing was typed." % e)
    return scan, solution


def reanalyse(image, solution):
    """Re-read a partly filled board before resuming. Returns the new scan.

    Every digit on screen must agree with the solution, so a moved page or a
    different puzzle is refused instead of typed over.
    """
    scan = detect.scanImage(image)
    if scan is None:
        raise PipelineError("No 9x9 grid found on screen. Make sure the whole board is visible.")

    weak = [i for i, s in enumerate(scan.scores) if s < MIN_SCORE]
    if weak:
        cells = ", ".join("r%dc%d" % (i // 9 + 1, i % 9 + 1) for i in weak[:5])
        raise PipelineError("Unsure about digits in %s. Not resuming." % cells)

    wrong = [i for i, v in enumerate(scan.cells) if v and v != solution[i]]
    if wrong:
        cells = ", ".join("r%dc%d" % (i // 9 + 1, i % 9 + 1) for i in wrong[:5])
        raise PipelineError("Board on screen differs from the solution at %s. Not resuming." % cells)

    if scan.cells.count(0) == 0:
        raise PipelineError("The board is already full.")
    return scan
