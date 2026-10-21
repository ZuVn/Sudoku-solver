"""Mouse and keyboard on Windows through user32 (same interface as uinput.py).

The process is made DPI-aware on import, so screenshot pixels and cursor
coordinates are the same physical pixels (single monitor assumed).
"""

import ctypes
import time

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
KEYEVENTF_KEYUP = 0x0002
VK_1 = 0x31         # VK '1'..'9' are 0x31..0x39 (top row)
VK_F2 = 0x71

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)     # per-monitor aware, Windows 8.1+
except (AttributeError, OSError):
    user32.SetProcessDPIAware()


class InputError(Exception):
    pass


def f2Down():
    """True while F2 is held, whichever window has focus (global kill switch)."""
    return bool(user32.GetAsyncKeyState(VK_F2) & 0x8000)


class Pointer:
    def moveTo(self, x, y):
        user32.SetCursorPos(int(round(x)), int(round(y)))

    def click(self):
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class Keyboard:
    def typeDigit(self, digit):
        vk = VK_1 + digit - 1
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


class VirtualInput:
    """Pointer + keyboard pair. Use as a context manager."""

    def __init__(self, width, height):
        self.pointer = Pointer()
        self.keyboard = Keyboard()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
