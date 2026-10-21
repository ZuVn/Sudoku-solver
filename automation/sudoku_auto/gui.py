"""Small Tk control window: Scan, Fill, Stop."""

import os
import queue
import signal
import threading
import time
import tkinter as tk

from . import capture, filler, pipeline

if os.name == "nt":
    from . import winput as uinput
else:
    from . import uinput

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
        self.paused = False     # a fill was stopped and can be resumed
        self.busy = False
        self.resumePending = False  # set by SIGUSR1 (F2) while idle, handled in poll()

        root.title("Sudoku Auto")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=CELL * 9 + 2, height=CELL * 9 + 2,
                                bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=3, padx=8, pady=8)

        self.scanBtn = tk.Button(root, text="Scan", width=8, command=self.onScan)
        self.fillBtn = tk.Button(root, text="Fill", width=8, command=self.onFill,
                                 state=tk.DISABLED)
        self.toggleBtn = tk.Button(root, text="Stop", width=8, command=self.onToggle,
                                   state=tk.DISABLED)
        self.scanBtn.grid(row=1, column=0, padx=4)
        self.fillBtn.grid(row=1, column=1, padx=4)
        self.toggleBtn.grid(row=1, column=2, padx=4)

        opts = tk.Frame(root)
        opts.grid(row=2, column=0, columnspan=3, pady=6)
        tk.Label(opts, text="Delay (ms):").pack(side=tk.LEFT)
        self.delay = tk.Spinbox(opts, from_=0, to=1000, increment=20, width=5)
        self.delay.delete(0, tk.END)
        self.delay.insert(0, "80")
        self.delay.pack(side=tk.LEFT)

        self.status = tk.Label(root, text="",
                               wraplength=CELL * 9, justify=tk.LEFT, anchor="w")
        self.status.grid(row=3, column=0, columnspan=3, sticky="we", padx=8, pady=(0, 8))

        root.bind("<Escape>", lambda _e: self.onStop())
        if os.name == "nt":
            self.f2Held = False     # global F2 is polled in poll()
        else:
            root.bind("<F2>", lambda _e: self.onToggle())
            signal.signal(signal.SIGUSR1, self.onSignal)
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
        self.busy = busy
        resumable = self.paused and not busy
        self.toggleBtn.config(text="Resume" if resumable else "Stop",
                              state=tk.NORMAL if busy or resumable else tk.DISABLED)

    # ---- worker plumbing ----------------------------------------------

    def post(self, kind, *args):
        self.events.put((kind, args))

    def poll(self):
        if os.name == "nt":
            held = uinput.f2Down()
            if held and not self.f2Held:
                self.onSignal()
            self.f2Held = held
        if self.resumePending:
            self.resumePending = False
            self.onToggle()
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
            self.post("status", "%s in %d… (Stop / Esc / F2 to cancel)" % (verb, s))
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

    def on_paused(self, paused):
        self.paused = paused

    def on_scanned(self, scan, solution, size):
        self.scan, self.solution, self.screenSize = scan, solution, size
        self.drawBoard()
        empty = scan.cells.count(0)
        self.setStatus("Found the board: %d givens, %d empty. Press Fill to type the solution."
                       % (81 - empty, empty))

    # ---- buttons -------------------------------------------------------

    def onScan(self):
        self.scan = self.solution = None
        self.paused = False
        self.drawBoard()
        self.run(self.doScan)

    def doScan(self):
        self.post("status", "Capturing screen…")
        image = self.grab()
        scan, solution = pipeline.analyse(image)
        self.post("scanned", scan, solution, image.size)

    def fillDelay(self):
        try:
            return max(0, int(self.delay.get())) / 1000.0
        except ValueError:
            return 0.08

    def onFill(self):
        if not self.solution:
            return
        delay = self.fillDelay()
        self.moveAwayFromBoard()
        self.run(lambda: self.doFill(delay))

    def doFill(self, delay):
        self.countdown("Filling")
        self.typeSolution(self.scan, self.screenSize, delay)

    def onResume(self):
        if not self.paused or not self.solution:
            return
        delay = self.fillDelay()
        self.moveAwayFromBoard()
        self.run(lambda: self.doResume(delay))

    def doResume(self, delay):
        self.countdown("Resuming")
        self.post("status", "Re-reading the board…")
        image = self.grab()
        scan = pipeline.reanalyse(image, self.solution)
        self.typeSolution(scan, image.size, delay)

    def typeSolution(self, scan, size, delay):
        """Type the solution into the empty cells of scan. A stop leaves the fill resumable."""
        self.post("paused", True)
        w, h = size
        self.post("status", "Creating virtual mouse/keyboard…")
        try:
            with uinput.VirtualInput(w, h) as dev:
                total = filler.fill(scan, self.solution, dev, self.stopEvent, delay,
                                    lambda d, t: self.post("status", "Filling %d/%d…" % (d, t)))
        except filler.Stopped as e:
            raise filler.Stopped("%s. Press Resume or F2 to continue" % e)
        self.post("paused", False)
        self.post("status", "Typed %d digits." % total)

    def onStop(self):
        self.stopEvent.set()

    def onToggle(self):
        """Stop/Resume button and F2: stop while working, resume a stopped fill when idle."""
        if self.busy:
            self.onStop()
        elif self.paused:
            self.onResume()

    def onSignal(self, *_):
        """SIGUSR1 (global F2). Stopping is done here directly so it never waits on Tk."""
        if self.busy:
            self.stopEvent.set()
        else:
            self.resumePending = True

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
