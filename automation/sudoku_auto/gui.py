"""Small Tk control window: Scan, Fill, Stop."""

import queue
import signal
import threading
import time
import tkinter as tk

from . import capture, detect, filler, pipeline, uinput

CELL = 28
COUNTDOWN = 3
HIDE_WAIT = 0.4     # seconds for the compositor to hide our window before a capture


class App:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.stopEvent = threading.Event()
        self.worker = None
        self.scan = None
        self.solution = None
        self.screenSize = None

        root.title("Sudoku Auto")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=CELL * 9 + 2, height=CELL * 9 + 2,
                                bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=3, padx=8, pady=8)

        self.scanBtn = tk.Button(root, text="Scan", width=8, command=self.onScan)
        self.fillBtn = tk.Button(root, text="Fill", width=8, command=self.onFill,
                                 state=tk.DISABLED)
        self.stopBtn = tk.Button(root, text="Stop", width=8, command=self.onStop,
                                 state=tk.DISABLED)
        self.scanBtn.grid(row=1, column=0, padx=4)
        self.fillBtn.grid(row=1, column=1, padx=4)
        self.stopBtn.grid(row=1, column=2, padx=4)

        opts = tk.Frame(root)
        opts.grid(row=2, column=0, columnspan=3, pady=6)
        tk.Label(opts, text="Delay (ms):").pack(side=tk.LEFT)
        self.delay = tk.Spinbox(opts, from_=0, to=1000, increment=20, width=5)
        self.delay.delete(0, tk.END)
        self.delay.insert(0, "80")
        self.delay.pack(side=tk.LEFT)
        self.verify = tk.BooleanVar(value=True)
        tk.Checkbutton(opts, text="Verify after fill", variable=self.verify).pack(side=tk.LEFT)

        self.status = tk.Label(root, text="Open the puzzle in Chrome, then press Scan.",
                               wraplength=CELL * 9, justify=tk.LEFT, anchor="w")
        self.status.grid(row=3, column=0, columnspan=3, sticky="we", padx=8, pady=(0, 8))

        root.bind("<Escape>", lambda _e: self.onStop())
        signal.signal(signal.SIGUSR1, lambda *_: self.stopEvent.set())
        self.drawBoard()
        self.poll()

    # ---- drawing -------------------------------------------------------

    def drawBoard(self):
        cv = self.canvas
        cv.delete("all")
        for i in range(10):
            w = 2 if i % 3 == 0 else 1
            p = 1 + i * CELL
            cv.create_line(1, p, 1 + 9 * CELL, p, width=w)
            cv.create_line(p, 1, p, 1 + 9 * CELL, width=w)
        if self.scan is None:
            return
        for i in range(81):
            r, c = divmod(i, 9)
            x = 1 + c * CELL + CELL // 2
            y = 1 + r * CELL + CELL // 2
            if self.scan.cells[i]:
                cv.create_text(x, y, text=str(self.scan.cells[i]),
                               font=("TkDefaultFont", 13, "bold"))
            elif self.solution:
                cv.create_text(x, y, text=str(self.solution[i]), fill="#2a6fdb",
                               font=("TkDefaultFont", 12))

    def setStatus(self, text):
        self.status.config(text=text)

    def setBusy(self, busy):
        self.scanBtn.config(state=tk.DISABLED if busy else tk.NORMAL)
        self.fillBtn.config(state=tk.DISABLED if busy or not self.solution else tk.NORMAL)
        self.stopBtn.config(state=tk.NORMAL if busy else tk.DISABLED)

    # ---- worker plumbing ----------------------------------------------

    def post(self, kind, *args):
        self.events.put((kind, args))

    def poll(self):
        try:
            while True:
                kind, args = self.events.get_nowait()
                getattr(self, "on_" + kind)(*args)
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def run(self, target):
        self.stopEvent.clear()
        self.setBusy(True)
        self.worker = threading.Thread(target=self.guard, args=(target,), daemon=True)
        self.worker.start()

    def guard(self, target):
        try:
            target()
        except filler.Stopped as e:
            self.post("status", "Stopped: %s." % e)
        except (pipeline.PipelineError, capture.CaptureError, uinput.InputError) as e:
            self.post("status", str(e))
        except Exception as e:     # keep the window alive on unexpected errors
            self.post("status", "Error: %r" % e)
        finally:
            self.post("show")
            self.post("done")

    def countdown(self, verb):
        for s in range(COUNTDOWN, 0, -1):
            if self.stopEvent.is_set():
                raise filler.Stopped("before %s" % verb)
            self.post("status", "%s in %d… (Stop / Esc to cancel)" % (verb, s))
            time.sleep(1)

    def grab(self):
        """Hide the window, capture the screen, show the window again."""
        self.post("hide")
        time.sleep(HIDE_WAIT)
        try:
            return capture.capture()
        finally:
            self.post("show")

    # ---- event handlers (main thread) ---------------------------------

    def on_status(self, text):
        self.setStatus(text)

    def on_hide(self):
        self.root.withdraw()

    def on_show(self):
        self.root.deiconify()

    def on_done(self):
        self.setBusy(False)

    def on_scanned(self, scan, solution, size):
        self.scan, self.solution, self.screenSize = scan, solution, size
        self.drawBoard()
        empty = scan.cells.count(0)
        self.setStatus("Found the board: %d givens, %d empty. Press Fill to type the solution."
                       % (81 - empty, empty))

    # ---- buttons -------------------------------------------------------

    def onScan(self):
        self.scan = self.solution = None
        self.drawBoard()
        self.run(self.doScan)

    def doScan(self):
        self.post("status", "Capturing screen…")
        image = self.grab()
        scan, solution = pipeline.analyse(image)
        self.post("scanned", scan, solution, image.size)

    def onFill(self):
        if not self.solution:
            return
        try:
            delay = max(0, int(self.delay.get())) / 1000.0
        except ValueError:
            delay = 0.08
        verify = self.verify.get()
        self.moveAwayFromBoard()
        self.run(lambda: self.doFill(delay, verify))

    def doFill(self, delay, verify):
        self.countdown("Filling")
        w, h = self.screenSize
        self.post("status", "Creating virtual mouse/keyboard…")
        with uinput.VirtualInput(w, h) as dev:
            total = filler.fill(self.scan, self.solution, dev, self.stopEvent, delay,
                                lambda d, t: self.post("status", "Filling %d/%d…" % (d, t)))
        if not verify:
            self.post("status", "Typed %d digits." % total)
            return
        self.post("status", "Verifying…")
        time.sleep(0.3)
        after = detect.scanImage(self.grab())
        if after is None:
            self.post("status", "Typed %d digits. Could not re-read the board to verify." % total)
            return
        bad = filler.mismatches(after, self.solution)
        if bad:
            where = ", ".join("r%dc%d" % (r + 1, c + 1) for r, c, _, _ in bad[:6])
            self.post("status", "Typed %d digits, but %d cells differ: %s" % (total, len(bad), where))
        else:
            self.post("status", "Done. Board verified: all 81 cells correct.")

    def onStop(self):
        self.stopEvent.set()

    def moveAwayFromBoard(self):
        """If this window covers the board, move it to the far side of the screen."""
        if self.scan is None or self.screenSize is None:
            return
        self.root.update_idletasks()
        scale = self.screenSize[0] / float(self.root.winfo_screenwidth())
        wx, wy = self.root.winfo_rootx() * scale, self.root.winfo_rooty() * scale
        ww, wh = self.root.winfo_width() * scale, self.root.winfo_height() * scale
        x0, y0, x1, y1 = self.scan.grid.bbox
        if wx > x1 or wx + ww < x0 or wy > y1 or wy + wh < y0:
            return
        sw = self.root.winfo_screenwidth()
        boardMid = (x0 + x1) / 2.0 / scale
        nx = 10 if boardMid > sw / 2 else sw - self.root.winfo_width() - 10
        self.root.geometry("+%d+%d" % (nx, 40))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
