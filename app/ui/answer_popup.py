from html import escape
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

COLOR = "#475452"


from app.utils.platform import mouse_down as _mouse_down


class AnswerPopup(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                         | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.label = QLabel(wordWrap=True, textFormat=Qt.RichText)
        self.label.setStyleSheet(f"background:transparent;border:none;color:{COLOR};"
                                 "font-size:16px;font-weight:600;padding:6px;")
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.addWidget(self.label)
        self.timer = QTimer(self, singleShot=True); self.timer.timeout.connect(self.hide)
        self.poll = QTimer(self); self.poll.setInterval(25); self.poll.timeout.connect(self._check)
        self._was_down = False

    def show_answer(self, a, seconds):
        self.show_message(escape(a.display or a.answer).replace("\n", "<br>"), seconds)

    def show_message(self, html, seconds=6):
        self.label.setText(html); self.setFixedWidth(360); self.adjustSize()
        g = QGuiApplication.primaryScreen().availableGeometry()
        self.move(g.right() - self.width() - 16, g.bottom() - self.height() - 16)
        self._was_down = _mouse_down()
        self.show(); self.timer.start(int(seconds * 1000)); self.poll.start()

    def _check(self):
        down = _mouse_down()
        if down and not self._was_down:   # any click anywhere dismisses it
            self.hide()
        self._was_down = down

    def hideEvent(self, e):
        self.poll.stop(); self.timer.stop(); super().hideEvent(e)
