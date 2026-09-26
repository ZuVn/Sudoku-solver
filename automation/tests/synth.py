"""Render fake screenshots of a Sudoku page for detection tests."""

import random

from PIL import Image, ImageDraw, ImageFont

from sudoku_auto import digits

LIGHT = {"bg": (255, 255, 255), "thin": (190, 198, 212), "thick": (52, 72, 97),
         "digit": (52, 72, 97), "note": (110, 125, 140), "hl": (226, 235, 243)}
DARK = {"bg": (30, 32, 36), "thin": (70, 74, 82), "thick": (170, 176, 188),
        "digit": (225, 228, 235), "note": (140, 145, 150), "hl": (45, 55, 70)}


def font(name, size):
    for path in digits.findFonts():
        if path.endswith(name):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def render(puzzle, side=450, origin=(300, 200), screen=(1280, 800), theme=LIGHT,
           fontName="LiberationSans-Regular.ttf", notes=False, highlightRow=None,
           decoys=True, seed=1):
    rng = random.Random(seed)
    img = Image.new("RGB", screen, theme["bg"])
    dr = ImageDraw.Draw(img)
    ox, oy = origin
    cell = side / 9.0

    if decoys:
        # Page furniture: text, a toolbar strip, a 1x9 number pad like many sites have.
        dr.rectangle([0, 0, screen[0], 40], fill=theme["thin"])
        dr.text((20, 60), "Sudoku - Easy  0:42", font=font("DejaVuSans.ttf", 22), fill=theme["digit"])
        px, py = ox, oy + side + 30
        for i in range(10):
            dr.line([px + i * cell, py, px + i * cell, py + cell], fill=theme["thick"], width=2)
        dr.line([px, py, px + side, py], fill=theme["thick"], width=2)
        dr.line([px, py + cell, px + side, py + cell], fill=theme["thick"], width=2)

    if highlightRow is not None:
        y = oy + highlightRow * cell
        dr.rectangle([ox, y, ox + side, y + cell], fill=theme["hl"])

    f = font(fontName, int(cell * 0.6))
    small = font("DejaVuSans.ttf", max(6, int(cell * 0.2)))
    for i, ch in enumerate(puzzle):
        r, c = divmod(i, 9)
        cx, cy = ox + (c + 0.5) * cell, oy + (r + 0.5) * cell
        if ch in "123456789":
            dr.text((cx, cy), ch, font=f, fill=theme["digit"], anchor="mm")
        elif notes and rng.random() < 0.4:
            for d in rng.sample(range(1, 10), 3):
                nx = ox + c * cell + ((d - 1) % 3 + 0.5) * cell / 3
                ny = oy + r * cell + ((d - 1) // 3 + 0.5) * cell / 3
                dr.text((nx, ny), str(d), font=small, fill=theme["note"], anchor="mm")

    for k in range(10):
        thick = k % 3 == 0
        w = 3 if thick else 1
        col = theme["thick"] if thick else theme["thin"]
        p = k * cell
        dr.line([ox, oy + p, ox + side, oy + p], fill=col, width=w)
        dr.line([ox + p, oy, ox + p, oy + side], fill=col, width=w)
    return img
