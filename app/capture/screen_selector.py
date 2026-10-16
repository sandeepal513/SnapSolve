from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ScreenSelector(QWidget):
    selected = Signal(object)   # QPixmap of the chosen area
    cancelled = Signal()

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.start = self.end = None

    def begin(self):
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())  # all monitors
        self.start = self.end = None
        self.show(); self.raise_(); self.activateWindow()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if self.start and self.end:
            r = QRect(self.start, self.end).normalized()
            p.fillRect(r, QColor(255, 255, 255, 40))
            p.setPen(QPen(QColor(0, 120, 215), 2)); p.drawRect(r)

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
        g = r.translated(self.geometry().topLeft())          # global logical coords
        QTimer.singleShot(60, lambda: self._grab(g))        # let overlay disappear

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide(); self.cancelled.emit()

    def _grab(self, g):
        scr = QGuiApplication.screenAt(g.center()) or QGuiApplication.primaryScreen()
        sg = scr.geometry()
        loc = g.intersected(sg).translated(-sg.topLeft())
        if loc.isEmpty():
            self.cancelled.emit(); return
        self.selected.emit(scr.grabWindow(0, loc.x(), loc.y(), loc.width(), loc.height()))
