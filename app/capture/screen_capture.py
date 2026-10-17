import os, shutil, subprocess, tempfile
from PIL import Image

from app.utils.platform import is_wayland

def pixmap_to_pil(pm) -> Image.Image:
    """QPixmap -> PIL. Qt grabs at native resolution, so it is DPI/multi-monitor safe."""
    from PySide6.QtGui import QImage
    img = pm.toImage().convertToFormat(QImage.Format_RGBA8888)
    return Image.frombytes("RGBA", (img.width(), img.height()), img.bits().tobytes()).convert("RGB")


# ---- Linux/Wayland: Qt cannot grab the screen there, so use a system screenshot tool if one is installed
SHOT_TOOLS = [["grim", "{f}"], ["gnome-screenshot", "-f", "{f}"],
              ["spectacle", "-b", "-n", "-f", "-o", "{f}"], ["scrot", "-o", "{f}"],
              ["import", "-window", "root", "{f}"]]


def external_screenshot():
    """Screenshot of the whole desktop as a PIL image, or None."""
    fd, path = tempfile.mkstemp(suffix=".png"); os.close(fd)
    try:
        for cmd in SHOT_TOOLS:
            if not shutil.which(cmd[0]):
                continue
            try:
                subprocess.run([c.replace("{f}", path) for c in cmd], timeout=8, check=True,
                               capture_output=True)
                if os.path.getsize(path) > 0:
                    return Image.open(path).convert("RGB")
            except Exception:
                continue
        return None
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def crop_desktop(img, rect, desktop):
    """rect/desktop = (x, y, w, h) in logical pixels; scales to the screenshot's real resolution."""
    sx, sy = img.width / desktop[2], img.height / desktop[3]
    x, y = (rect[0] - desktop[0]) * sx, (rect[1] - desktop[1]) * sy
    return img.crop((int(x), int(y), int(x + rect[2] * sx), int(y + rect[3] * sy)))


def looks_blank(pm) -> bool:
    small = pm.toImage().scaled(24, 24)
    return all(small.pixelColor(x, y).value() < 8 for x in range(24) for y in range(24))


def pil_to_pixmap(img):
    from PySide6.QtGui import QImage, QPixmap
    img = img.convert("RGBA")
    qi = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, img.width * 4,
                QImage.Format_RGBA8888).copy()
    return QPixmap.fromImage(qi)


def grab_rect(rect, whole=False):
    """QPixmap of a global (logical-pixel) rectangle, or of the whole screen it is on. None if empty."""
    from PySide6.QtGui import QGuiApplication
    scr = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
    sg = scr.geometry()
    loc = sg if whole else rect.intersected(sg)
    if loc.isEmpty():
        return None
    if whole:
        pm = scr.grabWindow(0)
    else:
        pm = scr.grabWindow(0, loc.x() - sg.x(), loc.y() - sg.y(), loc.width(), loc.height())
    if is_wayland() and looks_blank(pm):
        shot = external_screenshot()
        if shot is not None:
            vg = QGuiApplication.primaryScreen().virtualGeometry()
            crop = crop_desktop(shot, (loc.x(), loc.y(), loc.width(), loc.height()),
                                (vg.x(), vg.y(), vg.width(), vg.height()))
            return pil_to_pixmap(crop)
    return pm
