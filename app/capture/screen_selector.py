from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.capture.screen_capture import grab_rect
from app.utils.platform import IS_LINUX, IS_MAC, mac_activate


class ScreenSelector(QWidget):
    selected = Signal(object)   # QPixmap of the chosen area
    cancelled = Signal()

    def __init__(self, dim=35, border=1):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.dim = max(20, min(150, int(dim)))        # overlay darkness (always at least slightly visible)
        self.border = max(1, min(4, int(border)))     # selection outline thickness
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)   # keep visible while app is in background (macOS)
        self.setCursor(Qt.CrossCursor)
        self.start = self.end = None

    def begin(self):
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())  # all monitors
        self.start = self.end = None
        self.show(); self.raise_(); self.activateWindow(); mac_activate()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, self.dim))
        if self.start and self.end:
            r = QRect(self.start, self.end).normalized()
            p.fillRect(r, QColor(255, 255, 255, 15))
            p.setPen(QPen(QColor(120, 160, 200, 150), self.border)); p.drawRect(r)

    def mousePressEvent(self, e):
        self.start = self.end = e.position().toPoint(); self.update()

    def mouseMoveEvent(self, e):
        self.end = e.position().toPoint(); self.update()

    def mouseReleaseEvent(self, e):
        self.end = e.position().toPoint()
        r = QRect(self.start, self.end).normalized()
        self.hide()
        if r.width() < 10 or r.height() < 10:
            self.cancelled.emit(); return
        g = QRect(self.mapToGlobal(r.topLeft()), r.size())   # global logical coords
        QTimer.singleShot(160 if IS_MAC else (120 if IS_LINUX else 60), lambda: self._grab(g))        # let overlay disappear

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide(); self.cancelled.emit()

    def _grab(self, g):
        pm = grab_rect(g)
        if pm is None or pm.isNull():
            self.cancelled.emit(); return
        self.selected.emit(pm)
