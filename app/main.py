import sys, threading
from PySide6.QtCore import Qt, QTimer, QDir, QLockFile, QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit

from app.ai.ai_service import AIService
from app.ai.providers.provider import AIError
from app.capture.screen_capture import pixmap_to_pil
from app.capture.screen_selector import ScreenSelector
from app.config.settings import Settings
from app.hotkey.hotkey_manager import HotkeyManager
from app.ocr.ocr_engine import OCREngine, OCRError
from app.parser.question_parser import parse
from app.ui.answer_popup import AnswerPopup
from app.ui.tray import Tray
from app.utils.clipboard import copy_text
from app.utils.logger import get_logger
from app.utils.platform import mac_activate, mac_setup

log = get_logger()


class Signals(QObject):
    ocr_done, answer, error = Signal(str), Signal(object), Signal(str)


class Worker(QRunnable):
    def __init__(self, img, settings, ocr, sig):
        super().__init__(); self.img, self.cfg, self.ocr, self.sig = img, settings, ocr, sig

    def run(self):
        try:
            log.info("OCR started")
            text = self.ocr.read(self.img, self.cfg["preprocess"])
            if not text.strip():
                self.sig.error.emit("No readable text detected."); return
            log.info("OCR completed"); self.sig.ocr_done.emit(text)
            log.info("AI request started")
            ans = AIService(self.cfg).answer(parse(text))
            log.info("AI request completed"); self.sig.answer.emit(ans)
        except (OCRError, AIError) as e:
            log.info("Error: %s", e); self.sig.error.emit(str(e))
        except Exception:
            log.exception("Unexpected error"); self.sig.error.emit("Something went wrong. Please try again.")


class Controller:
    def __init__(self, app):
        self.cfg, self.ocr, self.paused = Settings(), OCREngine(), False
        self.sig = Signals(); self.popup = AnswerPopup(); self.sel = ScreenSelector(self.cfg["overlay_dim"], self.cfg["overlay_border"])
        self.tray = Tray(self.cfg["hotkey"]); self.hk = HotkeyManager(self.cfg["hotkey"])
        self.hk.triggered.connect(self.start); self.hk.failed.connect(
            lambda: self.tray.notify("Hotkey unavailable (already in use?)"))
        self.sel.selected.connect(self.on_selected)
        self.sig.ocr_done.connect(copy_text)  # GUI thread -> clipboard
        self.sig.answer.connect(lambda a: self.popup.show_answer(a, self.cfg["popup_seconds"]))
        self.sig.error.connect(lambda m: self.popup.show_message(f"<b>{m}</b>"))
        self.tray.select.connect(self.start); self.tray.quit.connect(self.exit)
        self.tray.toggle_pause.connect(lambda on: setattr(self, "paused", on))
        self.tray.set_key.connect(self.ask_key); self.app = app; self.hk.start()
        threading.Thread(target=self._warm, daemon=True).start()
        if not self.cfg.api_key:                       # first run: ask for the key right away
            QTimer.singleShot(400, self.first_run)

    def _warm(self):
        """Load OCR models and open the HTTPS connection before the first use."""
        try:
            from PIL import Image
            from app.ai.providers.provider import SESSION
            self.ocr.read(Image.new("RGB", (240, 80), "white"))
            SESSION.get("https://api.groq.com/", timeout=5)
        except Exception:
            pass

    def start(self):
        if not self.paused:
            self.popup.hide()
            self.sel.begin()

    def on_selected(self, pm):
        QThreadPool.globalInstance().start(Worker(pixmap_to_pil(pm), self.cfg, self.ocr, self.sig))

    def first_run(self):
        if not self.ask_key():
            self.tray.notify("No API key set. Right-click the tray icon > Set API Key.")

    def ask_key(self) -> bool:
        text = "Paste your Groq API key (starts with gsk_):"
        while True:
            mac_activate()
            dlg = QInputDialog()
            dlg.setWindowTitle("SnapSolve - API Key"); dlg.setLabelText(text)
            dlg.setTextEchoMode(QLineEdit.Password); dlg.resize(440, 120)
            dlg.setWindowFlag(Qt.WindowStaysOnTopHint)
            if not dlg.exec():
                return False
            k = dlg.textValue().strip()
            if k.startswith("gsk_"):
                break
            text = "That doesn't look like a Groq key (it should start with gsk_).\nPlease paste it again:"
        saved = self.cfg.set_api_key(k)
        self.tray.notify("API key saved. Press Ctrl+Shift+A to select a question." if saved else
                         "API key set for this session only (could not save it to disk).")
        return True

    def exit(self):
        self.hk.stop(); self.tray.icon.hide(); self.app.quit()


def main():
    app = QApplication(sys.argv); app.setQuitOnLastWindowClosed(False); mac_setup()
    lock = QLockFile(QDir.tempPath() + "/snapsolve.lock")
    if not lock.tryLock(100):
        return 0  # already running
    ctrl = Controller(app)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
