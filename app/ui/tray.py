from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.utils.paths import resource_path


def make_icon():
    custom = resource_path("assets/icon.png")
    if custom.exists():
        return QIcon(str(custom))
    pm = QPixmap(64, 64); pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm); p.setBrush(QColor(0, 120, 215)); p.setPen(QColor(0, 0, 0, 0))
    p.drawRoundedRect(4, 4, 56, 56, 14, 14); p.setPen(QColor("white")); p.drawText(pm.rect(), 0x84, "S")
    p.end(); return QIcon(pm)


class Tray(QObject):
    select, set_key, toggle_pause, quit = Signal(), Signal(), Signal(bool), Signal()

    def __init__(self, hotkey):
        super().__init__()
        self.icon = QSystemTrayIcon(make_icon()); self.icon.setToolTip("SnapSolve - Running")
        m = QMenu()
        m.addAction(f"Select Screen Area ({hotkey})", self.select.emit)
        self.pause = QAction("Pause", checkable=True); self.pause.toggled.connect(self._p); m.addAction(self.pause)
        m.addAction("Set API Key...", self.set_key.emit)
        m.addSeparator(); m.addAction("Exit", self.quit.emit)
        self.menu = m; self.icon.setContextMenu(m); self.icon.show()

    def _p(self, on):
        self.icon.setToolTip("SnapSolve - " + ("Paused" if on else "Running"))
        self.toggle_pause.emit(on)

    def notify(self, msg):
        self.icon.showMessage("SnapSolve", msg, QSystemTrayIcon.Warning, 4000)
