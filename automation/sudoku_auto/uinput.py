"""Virtual mouse and keyboard through /dev/uinput (works on Wayland and X11).

The mouse is an absolute pointer whose range equals the screenshot size, so a
pixel in the screenshot maps straight to a pointer position regardless of
display scaling (single monitor assumed).

Requires write access to /dev/uinput.
"""

import fcntl
import os
import struct
import time

UINPUT_PATH = "/dev/uinput"

EV_SYN, EV_KEY, EV_ABS = 0x00, 0x01, 0x03
SYN_REPORT = 0
ABS_X, ABS_Y = 0x00, 0x01
BTN_LEFT = 0x110
KEY_1 = 2           # KEY_1..KEY_9 are 2..10 (top row, US-style layouts)
BUS_VIRTUAL = 0x06

UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_DEV_SETUP = 0x405C5503       # _IOW('U', 3, struct uinput_setup)  size 92
UI_ABS_SETUP = 0x401C5504       # _IOW('U', 4, struct uinput_abs_setup) size 28
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567

EVENT = struct.Struct("llHHi")  # struct input_event on 64-bit Linux

# Seconds to wait after creating a device so the compositor picks it up.
SETTLE = 1.0


class InputError(Exception):
    pass


class _Device:
    def __init__(self, name, product):
        try:
            self.fd = os.open(UINPUT_PATH, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as e:
            raise InputError("cannot open %s: %s" % (UINPUT_PATH, e.strerror))
        self.name = name
        self.product = product

    def _create(self):
        setup = struct.pack("HHHH80sI", BUS_VIRTUAL, 0x1234, self.product, 1,
                            self.name.encode(), 0)
        fcntl.ioctl(self.fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(self.fd, UI_DEV_CREATE)

    def emit(self, etype, code, value):
        os.write(self.fd, EVENT.pack(0, 0, etype, code, value))

    def sync(self):
        self.emit(EV_SYN, SYN_REPORT, 0)

    def close(self):
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
            finally:
                os.close(self.fd)
                self.fd = None


class Pointer(_Device):
    def __init__(self, width, height):
        super().__init__("sudoku-auto pointer", 0x5301)
        self.width = width
        self.height = height
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_LEFT)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
        for code, maximum in ((ABS_X, width - 1), (ABS_Y, height - 1)):
            fcntl.ioctl(self.fd, UI_SET_ABSBIT, code)
            # struct uinput_abs_setup: code, pad, value, min, max, fuzz, flat, resolution
            fcntl.ioctl(self.fd, UI_ABS_SETUP,
                        struct.pack("HHiiiiii", code, 0, 0, 0, maximum, 0, 0, 0))
        self._create()

    def moveTo(self, x, y):
        self.emit(EV_ABS, ABS_X, int(round(min(max(x, 0), self.width - 1))))
        self.emit(EV_ABS, ABS_Y, int(round(min(max(y, 0), self.height - 1))))
        self.sync()

    def click(self):
        self.emit(EV_KEY, BTN_LEFT, 1)
        self.sync()
        time.sleep(0.02)
        self.emit(EV_KEY, BTN_LEFT, 0)
        self.sync()


class Keyboard(_Device):
    def __init__(self):
        super().__init__("sudoku-auto keyboard", 0x5302)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        # Enable the ordinary key range so udev/libinput classify it as a keyboard.
        for code in range(1, 128):
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, code)
        self._create()

    def typeDigit(self, digit):
        code = KEY_1 + digit - 1
        self.emit(EV_KEY, code, 1)
        self.sync()
        time.sleep(0.02)
        self.emit(EV_KEY, code, 0)
        self.sync()


class VirtualInput:
    """Pointer + keyboard pair. Use as a context manager."""

    def __init__(self, width, height):
        self.pointer = Pointer(width, height)
        try:
            self.keyboard = Keyboard()
        except Exception:
            self.pointer.close()
            raise
        time.sleep(SETTLE)

    def close(self):
        self.pointer.close()
        self.keyboard.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
