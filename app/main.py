import os, sys, threading
from PySide6.QtCore import Qt, QTimer, QDir, QLockFile, QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox

from app.ai.ai_service import AIService
from app.ai.providers.provider import AIError
from app.capture.screen_capture import pixmap_to_pil
from app.capture.screen_selector import ScreenSelector
from app.config.settings import Settings
from app.hotkey.hotkey_manager import HotkeyManager
from app.hotkey.keys import parse as parse_hotkey
from app.ocr.ocr_engine import OCREngine, OCRError
from app.parser.question_parser import parse
from app.ui.answer_popup import AnswerPopup
from app.ui.tray import Tray
from app.utils.clipboard import copy_text
from app.utils.logger import get_logger
from app.utils import ipc
from app.utils.platform import is_wayland, mac_activate, mac_setup

log = get_logger()


class Signals(QObject):
    ocr_done, answer, error = Signal(str), Signal(object), Signal(str)


class Worker(QRunnable):
    def __init__(self, img, settings, ocr, sig, full=False):
        super().__init__(); self.img, self.cfg, self.ocr, self.sig, self.full = img, settings, ocr, sig, full

    def run(self):
        try:
            log.info("OCR started")
            text = self.ocr.read(self.img, self.cfg["preprocess"])
            if not text.strip():
                self.sig.error.emit("No readable text detected."); return
            log.info("OCR completed")
            log.info("AI request started")
            if self.full:
                ans, clip = AIService(self.cfg).answer_screen(text)
                self.sig.ocr_done.emit(clip)          # copy only the question + options, not the whole screen
            else:
                self.sig.ocr_done.emit(text)
                ans = AIService(self.cfg).answer(parse(text))
            log.info("AI request completed"); self.sig.answer.emit(ans)
        except (OCRError, AIError) as e:
            log.info("Error: %s", e); self.sig.error.emit(str(e))
        except Exception:
            log.exception("Unexpected error"); self.sig.error.emit("Something went wrong. Please try again.")


class IPCBridge(QObject):
    command = Signal(str)


class Controller:
    def __init__(self, app):
        self.cfg, self.ocr, self.paused = Settings(), OCREngine(), False
        self.sig = Signals(); self.popup = AnswerPopup(); self.sel = ScreenSelector(self.cfg["overlay_dim"], self.cfg["overlay_border"])
        self.tray = Tray(self.cfg["hotkey"], self.cfg["hotkey_full"])
        self.hk = self._new_hotkey("hotkey", 1, self.start)
        self.hk_full = self._new_hotkey("hotkey_full", 2, self.start_full)
        self.sel.selected.connect(self.on_selected)
        self.sig.ocr_done.connect(copy_text)  # GUI thread -> clipboard
        self.sig.answer.connect(lambda a: self.popup.show_answer(a, self.cfg["popup_seconds"]))
        self.sig.error.connect(lambda m: self.popup.show_message(f"<b>{m}</b>"))
        self.tray.select.connect(self.start); self.tray.select_full.connect(self.start_full)
        self.tray.quit.connect(self.exit)
        self.tray.toggle_pause.connect(lambda on: setattr(self, "paused", on))
        self.tray.change_keys.connect(self.change_hotkeys); self.tray.set_key.connect(self.ask_key); self.tray.clear_key.connect(self.clear_key); self.app = app; self.hk.start(); self.hk_full.start()
        threading.Thread(target=self._warm, daemon=True).start()
        self.bridge = IPCBridge(); self.bridge.command.connect(self._on_ipc)
        self.ipc_srv = ipc.serve(self.bridge.command.emit)
        if is_wayland():
            QTimer.singleShot(2000, lambda: self.tray.notify(
                "Wayland: apps can't grab global keys. Add shortcuts in your system keyboard settings that run "
                "tools/snapsolve_cmd.py --area and --full (see README)."))
        if not self.cfg.api_key:                       # first run: ask for the key right away
            QTimer.singleShot(400, self.first_run)

    def _new_hotkey(self, name, hid, handler):
        hk = HotkeyManager(self.cfg[name], hid)
        hk.triggered.connect(handler)
        hk.failed.connect(lambda: self.tray.notify(
            f"Shortcut {self.cfg[name]} is unavailable (already used by another program, or invalid)."))
        return hk

    def change_hotkeys(self):
        mac_activate()
        new = {}
        for name, label in (("hotkey", "selecting an area"), ("hotkey_full", "reading the full screen")):
            text = f"Shortcut for {label}\n(examples: ctrl+shift+a   alt+q   ctrl+alt+f9):"
            while True:
                dlg = QInputDialog()
                dlg.setWindowTitle("SnapSolve - Shortcuts"); dlg.setLabelText(text)
                dlg.setTextValue(self.cfg[name]); dlg.resize(480, 130)
                dlg.setWindowFlag(Qt.WindowStaysOnTopHint)
                if not dlg.exec():
                    return
                v = dlg.textValue().strip().lower().replace(" ", "")
                try:
                    parse_hotkey(v); new[name] = v
                    break
                except ValueError as e:
                    text = f"{e}\nTry again (examples: ctrl+shift+a   alt+q   ctrl+alt+f9):"
        if new["hotkey"] == new["hotkey_full"]:
            self.tray.notify("The two shortcuts must be different."); return
        for name, attr, hid, handler in (("hotkey", "hk", 1, self.start), ("hotkey_full", "hk_full", 2, self.start_full)):
            if new[name] != self.cfg[name]:
                getattr(self, attr).stop()
                self.cfg.data[name] = new[name]
                setattr(self, attr, self._new_hotkey(name, hid, handler))
                QTimer.singleShot(250, getattr(self, attr).start)   # give the old one time to release the keys
        self.cfg.save()
        self.tray.set_labels(self.cfg["hotkey"], self.cfg["hotkey_full"])
        self.tray.notify("Shortcuts updated.")

    def _on_ipc(self, cmd):
        {"--area": self.start, "--full": self.start_full, "--quit": self.exit}.get(cmd, lambda: None)()

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

    def start_full(self):
        if not self.paused:
            self.popup.hide()
            QTimer.singleShot(150, self._capture_full)      # let the old popup disappear first

    def _capture_full(self):
        scr = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.on_selected(scr.grabWindow(0), full=True)       # the screen the cursor is on

    def on_selected(self, pm, full=False):
        QThreadPool.globalInstance().start(Worker(pixmap_to_pil(pm), self.cfg, self.ocr, self.sig, full))

    def clear_key(self):
        mac_activate()
        box = QMessageBox()
        box.setIcon(QMessageBox.Question); box.setWindowTitle("SnapSolve - Clear API Key")
        box.setText("Remove your saved API key from this computer?\n\nSnapSolve won't be able to answer until you enter a key again (tray menu > Set API Key).")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No); box.setDefaultButton(QMessageBox.No)
        box.setWindowFlag(Qt.WindowStaysOnTopHint)
        if box.exec() != QMessageBox.Yes:
            return
        ok = self.cfg.clear_api_key()
        self.tray.notify("Saved API key removed. Use Set API Key to add a new one." if ok else
                         "The key was cleared for this session, but a key file could not be deleted.")

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
        self.tray.notify(f"API key saved. {self.cfg['hotkey']} selects an area, {self.cfg['hotkey_full']} reads the whole screen." if saved else
                         "API key set for this session only (could not save it to disk).")
        return True

    def exit(self):
        self.hk.stop(); self.hk_full.stop(); self.tray.icon.hide()
        if self.ipc_srv:
            self.ipc_srv.close()
        self.app.quit()


def main():
    cmd = next((a for a in sys.argv[1:] if a in ipc.COMMANDS), None)
    if cmd and ipc.send(cmd):               # a running SnapSolve handles it (Linux/macOS)
        return 0
    if cmd == "--quit":
        return 0
    if sys.platform.startswith("linux") and os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")     # X11 / XWayland: overlay + positioning work
    app = QApplication(sys.argv); app.setQuitOnLastWindowClosed(False); mac_setup()
    lock = QLockFile(QDir.tempPath() + "/snapsolve.lock")
    if not lock.tryLock(100):
        return 0  # already running
    ctrl = Controller(app)
    if cmd in ("--area", "--full"):         # started by a shortcut while not running: do it once ready
        QTimer.singleShot(2500, ctrl.start if cmd == "--area" else ctrl.start_full)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
