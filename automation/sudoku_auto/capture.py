"""Full-screen capture through the xdg-desktop-portal Screenshot interface.

This is the supported way to capture the screen on GNOME Wayland. GNOME may
ask for permission the first time. The portal writes a PNG (usually into
~/Pictures/Screenshots); it is loaded and then deleted.
"""

import os
import uuid
from urllib.parse import unquote, urlparse

from PIL import Image


class CaptureError(Exception):
    pass


def capture(timeout=30):
    """Return the whole screen as an RGB PIL image."""
    if os.name == "nt":
        from PIL import ImageGrab
        return ImageGrab.grab().convert("RGB")

    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    context = GLib.MainContext.new()
    context.push_thread_default()
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        token = "sudoku_auto_" + uuid.uuid4().hex
        sender = bus.get_unique_name()[1:].replace(".", "_")
        handle = "/org/freedesktop/portal/desktop/request/%s/%s" % (sender, token)
        loop = GLib.MainLoop.new(context, False)
        result = {}

        def onResponse(_conn, _sender, _path, _iface, _signal, params):
            code, results = params.unpack()
            result["code"] = code
            result["uri"] = results.get("uri")
            loop.quit()

        sub = bus.signal_subscribe("org.freedesktop.portal.Desktop",
                                   "org.freedesktop.portal.Request", "Response",
                                   handle, None, Gio.DBusSignalFlags.NONE,
                                   onResponse)
        try:
            options = {"handle_token": GLib.Variant("s", token),
                       "interactive": GLib.Variant("b", False)}
            bus.call_sync("org.freedesktop.portal.Desktop",
                          "/org/freedesktop/portal/desktop",
                          "org.freedesktop.portal.Screenshot", "Screenshot",
                          GLib.Variant("(sa{sv})", ("", options)),
                          None, Gio.DBusCallFlags.NONE, -1, None)

            timer = GLib.timeout_source_new_seconds(timeout)
            timer.set_callback(lambda *_: loop.quit())
            timer.attach(context)
            loop.run()
            timer.destroy()
        finally:
            bus.signal_unsubscribe(sub)
    finally:
        context.pop_thread_default()

    if "code" not in result:
        raise CaptureError("screenshot portal did not answer within %ds" % timeout)
    if result["code"] != 0 or not result.get("uri"):
        raise CaptureError("screenshot was denied or cancelled (code %s)" % result["code"])

    path = unquote(urlparse(result["uri"]).path)
    try:
        with Image.open(path) as img:
            image = img.convert("RGB")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return image
