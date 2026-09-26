"""Find a 9x9 Sudoku grid in a screenshot and read its digits.

The grid is located from its four thick box lines (rows/columns 0, 3, 6, 9),
which every common Sudoku site draws darker than the thin cell lines. Thin
lines are used when found, otherwise interpolated.
"""

from dataclasses import dataclass, field

import numpy as np

from . import digits

N = 9

# Gray levels tried, darkest first. The first one that yields a grid wins.
THRESHOLDS = (100, 150, 190, 215)

# Smallest grid side (px) worth considering.
MIN_GRID = 150


@dataclass
class Grid:
    """Location of a grid in screenshot pixels."""

    xs: list    # 10 vertical line centres, left to right
    ys: list    # 10 horizontal line centres, top to bottom

    @property
    def bbox(self):
        return (self.xs[0], self.ys[0], self.xs[-1], self.ys[-1])

    def cellCenter(self, r, c):
        return ((self.xs[c] + self.xs[c + 1]) / 2.0,
                (self.ys[r] + self.ys[r + 1]) / 2.0)


@dataclass
class Scan:
    """Result of reading a screenshot."""

    grid: Grid
    cells: list                                  # 81 ints, 0 = empty
    scores: list = field(default_factory=list)   # 81 match scores, 1.0 for empty

    def puzzleString(self):
        return "".join(str(v) if v else "." for v in self.cells)


def toGray(image):
    """PIL image or array -> float32 gray array."""
    arr = np.asarray(image)
    if arr.ndim == 3:
        arr = arr[..., :3].astype(np.float32)
        return arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    return arr.astype(np.float32)


def horizontalRuns(mask, minLen):
    """Return (y, x0, x1) for every horizontal run of True with length >= minLen.

    x1 is exclusive.
    """
    h, w = mask.shape
    padded = np.zeros((h, w + 2), dtype=np.int8)
    padded[:, 1:-1] = mask
    diff = np.diff(padded, axis=1)
    sy, sx = np.nonzero(diff == 1)
    ey, ex = np.nonzero(diff == -1)
    keep = (ex - sx) >= minLen
    return sy[keep], sx[keep], ex[keep]


def groupLines(ys):
    """Merge consecutive row indices into lines -> list of (centre, thickness)."""
    lines = []
    start = prev = None

    for y in sorted(set(int(v) for v in ys)):
        if start is None:
            start = prev = y
        elif y <= prev + 1:
            prev = y
        else:
            lines.append(((start + prev) / 2.0, prev - start + 1))
            start = prev = y

    if start is not None:
        lines.append(((start + prev) / 2.0, prev - start + 1))

    return lines


def clusterSpans(ys, x0s, x1s, tol):
    """Group runs that share the same horizontal extent."""
    clusters = []

    order = np.argsort(x0s - x1s)    # longest first
    for i in order:
        x0, x1, y = int(x0s[i]), int(x1s[i]), int(ys[i])
        for cl in clusters:
            if abs(cl["x0"] - x0) <= tol and abs(cl["x1"] - x1) <= tol:
                cl["ys"].append(y)
                break
        else:
            clusters.append({"x0": x0, "x1": x1, "ys": [y]})

    return clusters


def nearest(lines, target, tol):
    """Line centre closest to target within tol, or None."""
    best = None
    for centre, _ in lines:
        d = abs(centre - target)
        if d <= tol and (best is None or d < abs(best - target)):
            best = centre
    return best


def columnProfile(mask, y0, y1):
    """Fraction of dark pixels per column between rows y0 and y1."""
    return mask[int(y0):int(y1) + 1, :].mean(axis=0)


def fitLines(first, side, found, tol):
    """10 line positions: use detected lines when close, else interpolate."""
    step = side / 9.0
    out = []
    for k in range(10):
        hit = nearest(found, first + k * step, tol)
        out.append(hit if hit is not None else first + k * step)
    return out


def findGridInMask(mask):
    h, w = mask.shape
    minLen = max(MIN_GRID, min(h, w) // 12)
    ys, x0s, x1s = horizontalRuns(mask, minLen)
    if len(ys) == 0:
        return None

    tol = 4
    best = None

    for cl in clusterSpans(ys, x0s, x1s, tol):
        side = cl["x1"] - cl["x0"]
        if side < MIN_GRID:
            continue

        maxThick = max(3, side // 30)
        lines = [ln for ln in groupLines(cl["ys"]) if ln[1] <= maxThick]
        if len(lines) < 4:
            continue

        lineTol = max(3.0, side / 60.0)

        for top, _ in lines:
            # Box lines must sit at top + k * side / 3.
            if top + side > h + lineTol:
                continue
            if not all(nearest(lines, top + k * side / 3.0, lineTol) is not None
                       for k in (1, 2, 3)):
                continue

            bottom = nearest(lines, top + side, lineTol)
            prof = columnProfile(mask, top, bottom)
            vlines = verticalLines(prof, cl["x0"], cl["x1"], maxThick)
            left = nearest(vlines, cl["x0"] + 0.5, lineTol + maxThick)
            if left is None:
                continue
            if not all(nearest(vlines, left + k * side / 3.0, lineTol + maxThick) is not None
                       for k in (1, 2, 3)):
                continue

            right = nearest(vlines, left + side, lineTol + maxThick)
            ysFit = fitLines(top, bottom - top, lines, lineTol)
            xsFit = fitLines(left, right - left, vlines, lineTol + maxThick)
            grid = Grid(xs=xsFit, ys=ysFit)

            if best is None or side > best[0]:
                best = (side, grid)
            break

    return best[1] if best else None


def verticalLines(profile, x0, x1, maxThick):
    """Columns in [x0 - pad, x1 + pad] that are dark along >= 85% of the grid height."""
    pad = maxThick + 4
    lo = max(0, x0 - pad)
    hi = min(len(profile), x1 + pad)
    cols = [lo + i for i, v in enumerate(profile[lo:hi]) if v >= 0.85]
    return [ln for ln in groupLines(cols) if ln[1] <= maxThick]


def findGrid(gray):
    """Locate the largest 9x9 grid. Tries dark-on-light, then light-on-dark."""
    for img in (gray, 255.0 - gray):
        for t in THRESHOLDS:
            grid = findGridInMask(img < t)
            if grid is not None:
                return grid
    return None


def readCells(gray, grid, templates=None):
    """Classify all 81 cells. Returns (cells, scores)."""
    if templates is None:
        templates = digits.defaultTemplates()

    cells, scores = [], []
    for r in range(N):
        for c in range(N):
            x0, x1 = grid.xs[c], grid.xs[c + 1]
            y0, y1 = grid.ys[r], grid.ys[r + 1]
            mx = (x1 - x0) * 0.12
            my = (y1 - y0) * 0.12
            crop = gray[int(y0 + my):int(y1 - my), int(x0 + mx):int(x1 - mx)]
            value, score = digits.classifyCell(crop, templates)
            cells.append(value)
            scores.append(score)
    return cells, scores


def scanImage(image, templates=None):
    """Full pipeline on a PIL image. Returns a Scan or None if no grid is found."""
    gray = toGray(image)
    grid = findGrid(gray)
    if grid is None:
        return None
    cells, scores = readCells(gray, grid, templates)
    return Scan(grid=grid, cells=cells, scores=scores)
