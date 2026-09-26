"""Tests for sudoku_auto. Run from automation/: python -m unittest -v"""

import os
import threading
import unittest

from PIL import Image

from sudoku_auto import detect, filler, pipeline, solver
from tests import synth

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")

EASY = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"

# Real Chrome screenshots (headless, 1600x1000) with the puzzle read by hand.
REAL = {
    "websudoku.png":
        ".25......4..8..13....6..87..62.38.17.817.452.75.29.36..17..6....49..2..6......24.",
    "sudokuonline.png":
        ".2..8.9....67...84......7.69....35..385.76.....489.......4..8..4.1.6.2.3....5764.",
}


def load(name):
    with Image.open(os.path.join(FIXTURES, name)) as img:
        return img.convert("RGB")


class RealScreenshots(unittest.TestCase):
    def test_reads_every_cell(self):
        for name, expected in REAL.items():
            with self.subTest(name):
                scan = detect.scanImage(load(name))
                self.assertIsNotNone(scan)
                self.assertEqual(scan.puzzleString(), expected)

    def test_grid_is_square_and_on_board(self):
        scan = detect.scanImage(load("sudokuonline.png"))
        x0, y0, x1, y1 = scan.grid.bbox
        self.assertAlmostEqual(x1 - x0, y1 - y0, delta=6)
        self.assertAlmostEqual(x0, 424, delta=4)
        self.assertAlmostEqual(y0, 307, delta=4)


class SyntheticScreenshots(unittest.TestCase):
    def check(self, **kw):
        scan = detect.scanImage(synth.render(EASY, **kw))
        self.assertIsNotNone(scan, kw)
        self.assertEqual(scan.puzzleString(), EASY, kw)
        return scan

    def test_light_theme(self):
        self.check()

    def test_dark_theme(self):
        self.check(theme=synth.DARK)

    def test_pencil_marks_are_empty(self):
        self.check(notes=True)

    def test_highlighted_row(self):
        self.check(highlightRow=4)

    def test_small_grid(self):
        self.check(side=270, origin=(900, 450))

    def test_bold_and_serif_fonts(self):
        for name in ("DejaVuSans-Bold.ttf", "DejaVuSerif.ttf"):
            with self.subTest(name):
                self.check(fontName=name)

    def test_cell_centres_match_render(self):
        scan = self.check(side=450, origin=(300, 200))
        x, y = scan.grid.cellCenter(4, 7)
        self.assertAlmostEqual(x, 300 + 7.5 * 50, delta=3)
        self.assertAlmostEqual(y, 200 + 4.5 * 50, delta=3)

    def test_no_grid(self):
        img = Image.new("RGB", (800, 600), "white")
        self.assertIsNone(detect.scanImage(img))


class Pipeline(unittest.TestCase):
    def test_solves_detected_board(self):
        scan, solution = pipeline.analyse(synth.render(EASY))
        self.assertEqual(len(solution), 81)
        for i, v in enumerate(scan.cells):
            if v:
                self.assertEqual(solution[i], v)

    def test_refuses_invalid_board(self):
        bad = "55" + EASY[2:]   # duplicate 5 in row 1
        with self.assertRaises(pipeline.PipelineError):
            pipeline.analyse(synth.render(bad))

    def test_solver_bridge_error(self):
        with self.assertRaises(solver.SolveError):
            solver.solve("1" * 81)


class FakeDevice:
    def __init__(self):
        self.log = []
        self.pointer = self
        self.keyboard = self

    def moveTo(self, x, y):
        self.log.append(("move", round(x), round(y)))

    def click(self):
        self.log.append(("click",))

    def typeDigit(self, d):
        self.log.append(("key", d))


class Filler(unittest.TestCase):
    def setUp(self):
        self.scan, self.solution = pipeline.analyse(synth.render(EASY))

    def test_only_empty_cells_are_typed(self):
        dev = FakeDevice()
        n = filler.fill(self.scan, self.solution, dev, threading.Event(), delay=0)
        self.assertEqual(n, EASY.count("."))
        keys = [e[1] for e in dev.log if e[0] == "key"]
        expected = [self.solution[i] for i, ch in enumerate(EASY) if ch == "."]
        self.assertEqual(keys, expected)

    def test_first_click_hits_first_empty_cell(self):
        dev = FakeDevice()
        filler.fill(self.scan, self.solution, dev, threading.Event(), delay=0)
        # r1c3 is the first empty cell: centre (300 + 2.5*50, 200 + 0.5*50)
        self.assertEqual(dev.log[0][0], "move")
        self.assertAlmostEqual(dev.log[0][1], 425, delta=3)
        self.assertAlmostEqual(dev.log[0][2], 225, delta=3)

    def test_stop_before_any_input(self):
        stop = threading.Event()
        stop.set()
        dev = FakeDevice()
        with self.assertRaises(filler.Stopped):
            filler.fill(self.scan, self.solution, dev, stop, delay=0)
        self.assertEqual(dev.log, [])

    def test_mismatches(self):
        self.assertEqual(filler.mismatches(self.scan, self.solution),
                         [(i // 9, i % 9, 0, self.solution[i])
                          for i, ch in enumerate(EASY) if ch == "."])


if __name__ == "__main__":
    unittest.main()
