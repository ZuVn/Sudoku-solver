"""Digit recognition by template matching.

Templates are rendered from fonts installed on the system (sans and serif,
regular and bold), so no training data is needed. A cell crop and a template
go through the same normalisation, and the best normalised correlation wins.
"""

import functools
import glob
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 24

# Font file names searched under the font directories.
FONT_FILES = (
    "DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
    "DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf",
    "LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf",
    "LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf",
    "FreeSans.ttf", "FreeSansBold.ttf",
    "FreeSerif.ttf", "FreeSerifBold.ttf",
    "NotoSans-Regular.ttf", "NotoSans-Bold.ttf",
    "NotoSerif-Regular.ttf", "NotoSerif-Bold.ttf",
    "Ubuntu[wdth,wght].ttf", "UbuntuSans[wdth,wght].ttf",
    "Roboto-Regular.ttf", "Roboto-Bold.ttf",
    "OpenSans-Regular.ttf", "OpenSans-Bold.ttf",
    "Arial.ttf", "Arial_Bold.ttf", "Verdana.ttf",
)

FONT_DIRS = ("/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.local/share/fonts"))

if os.name == "nt":
    FONT_FILES = (
        "arial.ttf", "arialbd.ttf", "verdana.ttf", "verdanab.ttf",
        "tahoma.ttf", "tahomabd.ttf", "times.ttf", "timesbd.ttf",
        "georgia.ttf", "georgiab.ttf", "calibri.ttf", "calibrib.ttf",
        "segoeui.ttf", "segoeuib.ttf", "trebuc.ttf", "trebucbd.ttf",
    )
    FONT_DIRS = (os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),)

# Minimum contrast (gray levels) between ink and cell background.
MIN_CONTRAST = 50

# A glyph shorter than this fraction of the crop is treated as a pencil mark / noise.
MIN_HEIGHT = 0.4


def findFonts():
    wanted = set(FONT_FILES)
    found = {}
    for root in FONT_DIRS:
        for path in glob.glob(os.path.join(glob.escape(root), "**", "*.ttf"), recursive=True):
            name = os.path.basename(path)
            if name in wanted and name not in found:
                found[name] = path
    return sorted(found.values())


def normalise(ink):
    """Float ink map (0 = background, 1 = ink) cropped to the glyph -> unit vector."""
    h, w = ink.shape
    side = max(h, w)
    square = np.zeros((side, side), dtype=np.float32)
    square[(side - h) // 2:(side - h) // 2 + h, (side - w) // 2:(side - w) // 2 + w] = ink

    img = Image.fromarray((square * 255).astype(np.uint8))
    img = img.resize((SIZE, SIZE), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8))
    vec = np.asarray(img, dtype=np.float32).ravel()
    vec -= vec.mean()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def renderTemplate(font, digit):
    img = Image.new("L", (120, 120), 255)
    ImageDraw.Draw(img).text((20, 5), str(digit), font=font, fill=0)
    ink = (255.0 - np.asarray(img, dtype=np.float32)) / 255.0
    box = inkBox(ink > 0.5)
    if box is None:
        return None
    y0, y1, x0, x1 = box
    return normalise(ink[y0:y1, x0:x1])


def inkBox(mask):
    rows = np.nonzero(mask.any(axis=1))[0]
    cols = np.nonzero(mask.any(axis=0))[0]
    if len(rows) == 0:
        return None
    return rows[0], rows[-1] + 1, cols[0], cols[-1] + 1


@functools.lru_cache(maxsize=1)
def defaultTemplates():
    """(labels, matrix): one row per (font, digit) template."""
    labels, rows = [], []
    fonts = [ImageFont.truetype(p, 80) for p in findFonts()]
    if not fonts:
        fonts = [ImageFont.load_default(80)]
    for font in fonts:
        for d in range(1, 10):
            vec = renderTemplate(font, d)
            if vec is not None:
                labels.append(d)
                rows.append(vec)
    return np.array(labels), np.vstack(rows)


def neighbours8(y, x):
    return ((y - 1, x - 1), (y - 1, x), (y - 1, x + 1), (y, x - 1),
            (y, x + 1), (y + 1, x - 1), (y + 1, x), (y + 1, x + 1))


def largestComponent(mask):
    """Boolean mask of the largest 8-connected component of mask (pure Python BFS).

    8-connectivity keeps small glyphs whole: at ~20px an 8's loops touch only diagonally.
    """
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = []
    for sy, sx in zip(*np.nonzero(mask)):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]
        seen[sy, sx] = True
        comp = []
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            for ny, nx in neighbours8(y, x):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(mask, dtype=bool)
    if best:
        ys, xs = zip(*best)
        out[list(ys), list(xs)] = True
    return out


def classifyCell(crop, templates):
    """Gray cell crop -> (digit or 0, score). Score is 1.0 for empty cells."""
    if crop.size == 0 or min(crop.shape) < 8:
        return 0, 1.0

    bg = float(np.median(crop))
    diff = np.abs(crop - bg)
    peak = float(diff.max())
    if peak < MIN_CONTRAST:
        return 0, 1.0

    mask = diff > max(MIN_CONTRAST * 0.6, peak * 0.45)
    comp = largestComponent(mask)
    box = inkBox(comp)
    y0, y1, x0, x1 = box
    h, w = crop.shape
    if (y1 - y0) < MIN_HEIGHT * h:
        return 0, 1.0

    ink = np.clip(diff[y0:y1, x0:x1] / peak, 0.0, 1.0)
    vec = normalise(ink)
    labels, matrix = templates
    scores = matrix @ vec
    i = int(np.argmax(scores))
    return int(labels[i]), float(scores[i])
