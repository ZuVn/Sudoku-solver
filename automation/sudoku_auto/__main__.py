"""Entry point.

  python -m sudoku_auto                 Tk window (Scan / Fill / Stop)
  python -m sudoku_auto --image F.png   read a saved screenshot, print puzzle + solution
  python -m sudoku_auto --scan          capture the screen, print puzzle + solution (no typing)
  python -m sudoku_auto --fill          capture, solve and type the answers (Ctrl+C to stop)
"""

import argparse
import signal
import sys
import threading
import time

from . import capture, filler, pipeline, uinput


def printBoard(cells, title):
    print(title)
    for r in range(9):
        row = cells[r * 9:(r + 1) * 9]
        print(" ".join(str(v) if v else "." for v in row))


def report(image):
    scan, solution = pipeline.analyse(image)
    x0, y0, x1, y1 = scan.grid.bbox
    print("Grid at x=%d..%d y=%d..%d (screenshot %dx%d)" % (x0, x1, y0, y1, *image.size))
    print("Puzzle: %s" % scan.puzzleString())
    printBoard(scan.cells, "Detected:")
    printBoard(solution, "Solution:")
    return scan, solution


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sudoku_auto", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--image", metavar="PNG", help="analyse a saved screenshot")
    mode.add_argument("--scan", action="store_true", help="capture and analyse, no typing")
    mode.add_argument("--fill", action="store_true", help="capture, solve and type")
    ap.add_argument("--save", metavar="PNG", help="with --scan/--fill: also save the capture")
    ap.add_argument("--delay", type=int, default=80, help="ms to wait after each cell (default 80)")
    ap.add_argument("--countdown", type=int, default=3, help="seconds before capturing (default 3)")
    args = ap.parse_args(argv)

    if not (args.image or args.scan or args.fill):
        from . import gui
        gui.main()
        return 0

    try:
        if args.image:
            from PIL import Image
            with Image.open(args.image) as img:
                report(img.convert("RGB"))
            return 0

        for s in range(args.countdown, 0, -1):
            print("Capturing in %d…" % s, flush=True)
            time.sleep(1)
        image = capture.capture()
        if args.save:
            image.save(args.save)
        scan, solution = report(image)
        if not args.fill:
            return 0

        stop = threading.Event()
        signal.signal(signal.SIGUSR1, lambda *_: stop.set())
        with uinput.VirtualInput(*image.size) as dev:
            total = filler.fill(scan, solution, dev, stop, args.delay / 1000.0)
        print("Typed %d digits." % total)
        return 0
    except (pipeline.PipelineError, capture.CaptureError, uinput.InputError, filler.Stopped) as e:
        print("Error: %s" % e, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
